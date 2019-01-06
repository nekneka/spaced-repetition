import json
from sqlalchemy import ForeignKey, Column, Boolean, Integer, DateTime, String, Table
from sqlalchemy.orm import relationship
from sqlalchemy.types import BigInteger
from ..db.database import Base


class LogItem(Base):
    __tablename__ = 'log_item'
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, unique=False, nullable=False)
    ip = Column(String, unique=False, nullable=True)
    description = Column(String, unique=False, nullable=True)

    # def __init__(self, timestamp, ip):
    #     self.timestamp = timestamp
    #     self.ip = ip

    def __repr__(self):
        return json.dumps({'timestamp': self.timestamp,
                           'ip': self.ip})


repeat_item_to_tag = Table('repeat_item_to_tag', Base.metadata,
    Column('item_id', Integer, ForeignKey('repeat_item.id')),
    Column('tag_id', Integer, ForeignKey('tag.id'))
)


class Tag(Base):
    __tablename__ = 'tag'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tag = Column(String, unique=True, nullable=False)
    count = Column(Integer, unique=False, nullable=False)
    items = relationship(
        "RepeatItem",
        secondary=repeat_item_to_tag,
        back_populates="tags")

    def __init__(self, tag, count):
        self.tag = tag
        self.count = count

    def __repr__(self):
        return json.dumps({'tag': self.tag,
                           'count': self.count})


class RepeatItem(Base):
    __tablename__ = 'repeat_item'
    id = Column(BigInteger, primary_key=True)
    date_created = Column(DateTime, unique=False, nullable=False)
    description = Column(String, unique=False, nullable=False)
    tags = relationship(
        "Tag",
        secondary=repeat_item_to_tag,
        back_populates="items")

    def __init__(self, date_created, description, tags):
        self.date_created = date_created
        self.description = description
        self.tags = tags

    def __repr__(self):
        return json.dumps({'description': self.description,
                           'tags': json.loads(repr(self.tags))})


class DateRepeatItemLink(Base):
    __tablename__ = 'date_repeat_item_link'
    id = Column(BigInteger, primary_key=True)
    date_to_repeat = Column(DateTime, unique=False, nullable=False)
    repeat_item_id = Column(BigInteger, ForeignKey('repeat_item.id'))
    repeat_item = relationship("RepeatItem")

    # TODO probably don't need to store it here - can just calculate each time from Item Created date
    added_days_ago = Column(Integer, unique=False, nullable=False)
    done = Column(Boolean, unique=False, nullable=False)

    def __init__(self, date_to_repeat, repeat_item_id, added_days_ago):
        self.date_to_repeat = date_to_repeat
        self.repeat_item_id = repeat_item_id
        self.added_days_ago = added_days_ago
        self.done = False if added_days_ago != 0 else True

    def __repr__(self):
        return json.dumps({'date_to_repeat': self.date_to_repeat.isoformat(),
                           'repeat_item': json.loads(repr(self.repeat_item))})

