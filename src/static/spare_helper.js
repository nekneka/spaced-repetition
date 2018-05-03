function changeDoneStatus(checkboxElem) {
  let item = checkboxElem.parentNode;

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

let agenda_submit = document.getElementById("agenda_form");
let agenda_response_container = document.getElementById("agenda_response_container");

agenda_submit.addEventListener('submit', function(ev) {
  let data = new FormData(agenda_submit);
  let request = new XMLHttpRequest();

  request.open("POST", "/agenda", true);

  request.onload = function(oEvent) {
    if (request.status == 200) {
      agenda_response_container.innerHTML = request.response;
    } else {
      console.log("Error!");
    }
  };

  request.send(data);
  ev.preventDefault();
}, false);
