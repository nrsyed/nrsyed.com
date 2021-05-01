function post_data(form_submission) {
  let name = encodeURIComponent(document.getElementById("edit-name").value);
  let email = encodeURIComponent(document.getElementById("edit-mail").value);
  let url = encodeURIComponent(document.getElementById("edit-url").value);
  let subject = encodeURIComponent(document.getElementById("edit-subject").value);
  let message = encodeURIComponent(document.getElementById("edit-message").value);

  // Parameters to send to PHP script.
  let params = "name=" + name + "&email=" + email + "&url=" + url
    + "&subject=" + subject + "&message=" + message;

  let http = new XMLHttpRequest();
  http.open("POST", "/php/contact.php", true);
  http.setRequestHeader("Content-type", "application/x-www-form-urlencoded");

  http.onreadystatechange = function(){
    let form = document.getElementById("contact-form");
    form.classList.add("hidden");

    let contact_status = document.getElementById("contact-status");
    if (http.readyState == 4 && http.status == 200){
      contact_status.textContent = "Message submitted";
    } else {
      contact_status.textContent = "Error submitting message";
    }
	}

  http.send(params);

  // Disable button after it's been clicked.
  let submit_button = document.getElementById("contact-submit");
  submit_button.setAttribute("disabled", true);
}

function unlock_form() {
  let body = document.body;
  let form = document.getElementById("contact-form");
  let submit_button = document.getElementById("contact-submit");

  submit_button.removeAttribute("disabled");
  body.removeEventListener("mousemove", on_move);
  body.removeEventListener("touchmove", on_move);
  body.removeEventListener("keydown", on_keydown);
}

function on_move(e) {
  unlock_form();
}

function on_keydown(e) {
  if ((e.keyCode === 9) || (e.keyCode === 13)) {
    unlock_form();
  }
}

function main() {
  let body = document.body;
  let contact_status = document.getElementById("contact-status");
  let form = document.getElementById("contact-form");
  let submit_button = document.getElementById("contact-submit");

  // Remove the no JavaScript message and display the form.
  contact_status.textContent = "";
  form.classList.remove("hidden");

  // Wait for a mouse move, touch move, or tab/enter keypress to unlock form.
  body.addEventListener("mousemove", on_move);
  body.addEventListener("touchmove", on_move);
  body.addEventListener("keydown", on_keydown);

  // Mark form as submitted on submit button click.
  submit_button.onclick = function(e) {
    e.preventDefault();
    if (form.checkValidity()) {
      post_data(e);
    }
  };
}

main();
