function validateLoginForm() {
    let namecheck = document.forms["loginForm"]["username"].value;
    let pwcheck = document.forms["loginForm"]["password"].value;
    if (namecheck == "") {
        document.getElementById('username-message').innerHTML = '<div class="alert alert-danger my-2" role="alert">Username must be filled out</div>';
        return false;
    }
    if (pwcheck == "") {
        document.getElementById('password-message').innerHTML = '<div class="alert alert-danger my-2" role="alert">Password must be filled out</div>';
        return false;
    }
}
