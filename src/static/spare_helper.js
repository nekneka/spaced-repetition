// add new item
let new_item_form = document.getElementById("new_item_form");
let to_repeat_container = document.getElementById("to_repeat_container");
let learn_new = document.getElementById("learn-something-new");
let added_tags = document.getElementById("added_tags");
let tagcloud = document.getElementById('tagcloud');

new_item_form.addEventListener('submit', function(ev) {
  let data = new FormData(new_item_form);

  let tags = [];
  for (let item of added_tags.children) {
    tags.push(item.text.trim());
  }
  data.append('tags', tags);

  let request = new XMLHttpRequest();
  request.open("POST", "/", true);

  request.onload = function(oEvent) {
    if (request.status == 200) {
      let li_node = document.createElement("li");
      li_node.innerHTML = request.response;
      to_repeat_container.appendChild(li_node);
      learn_new.hidden = true;
      to_repeat_container.hidden = false;
      $('.tagline a').tagcloud();
    } else {
      console.log("Error!");
    }
  };

  request.send(data);
  ev.preventDefault();
}, false);


// done checkboxes
function changeDoneStatus(checkboxElem) {
  let item = checkboxElem.parentNode.parentNode;

  if (checkboxElem.checked) {
    item.classList.add('striked');
  } else {
    item.classList.remove('striked');
  }

  let data = JSON.stringify({added_timestamp: checkboxElem.id.split('_').pop(),
        done: checkboxElem.checked,
        parent_id: item.id.split('_').pop()});

  fetch("/api/item_done_change", {
    method: "POST",
    body: data,
    headers: {
        'Content-Type': 'application/json'
    }
  }).then(res => {
    console.log("Request complete! response:", res);

  }).catch(error => {
    // TODO error handling
    console.error(error);
  });
}


// checkbox see agenda for range of dates
function changeIsAgendaDatesRange(checkboxIsRange) {
  let end_date_elem = document.getElementById("agenda_end_date_block");
  let start_date_label_elem = document.getElementById("agenda_start_date_input_label");

  if (checkboxIsRange.checked) {
    end_date_elem.hidden = false;
    start_date_label_elem.textContent = 'Show things to repeat from ';
  } else {
    end_date_elem.hidden = true;
    start_date_label_elem.textContent = 'Show things to repeat on ';
  }

}


// agenda request
// TODO: this smells
let agenda_submit = document.getElementById("agenda_form");
let agenda_response_container = document.getElementById("agenda_response_container");

agenda_submit.addEventListener('submit', function(ev) {
  let data = new FormData(agenda_submit);
  let request = new XMLHttpRequest();

  request.open("POST", "/agenda", true);

  request.onload = function(oEvent) {
    if (request.status == 200) {
      agenda_response_container.innerHTML = request.response;
      $('.tagline a').tagcloud();
    } else {
      console.log("Error!");
    }
  };

  request.send(data);
  ev.preventDefault();
}, false);

function removeTag(event) {
  event.preventDefault();
  let tag = event.currentTarget;
  tag.onclick = addTag;
  added_tags.removeChild(tag)
  tagcloud.appendChild(tag);
}

function addTag(event) {
  event.preventDefault();
  let tag = event.currentTarget;
  tag.onclick = removeTag;
  tagcloud.removeChild(tag)
  added_tags.appendChild(tag);
  $('.tagline').tagcloud();
}

document.addEventListener('DOMContentLoaded', function(){
    $.fn.tagcloud.defaults = {
      size: {start: 10, end: 14, unit: 'px'},
      color: {start: '#1c5866', end: '#661c49'}
    };
    $('.tagline a').tagcloud();
    // specifically sized font for the cloud of tags
    $('.tagcloud a').tagcloud({size: {start: 14, end: 20, unit: 'px'}});

    let cloudTags = tagcloud.children;
    for (var i = 0; i < cloudTags.length; i++) {
        cloudTags[i].onclick = addTag;
    }
}, false);
