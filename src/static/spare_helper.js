function changeDoneStatus(checkboxElem) {
  let item = checkboxElem.parentNode;

  if (checkboxElem.checked) {
    item.classList.add('striked');
  } else {
    item.classList.remove('striked');
  }

  let ul_parent = item.parentNode;

  let data = JSON.stringify({added_timestamp: checkboxElem.id, done: checkboxElem.checked, parent_id: ul_parent.id});

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

