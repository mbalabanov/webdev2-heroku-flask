function validatePostForm() {
    let wholeForm = document.getElementById("postForm");
    for (let index = 0; index < wholeForm.length; index++) {
        let currentMessage = 'message' + index;
        if (wholeForm.elements[index].value == "") {
            document.getElementById(currentMessage).innerHTML = '<div class="alert alert-danger my-2" role="alert">Please fill out this field</div>';
            return false;
        } else {
            document.getElementById(currentMessage).innerHTML = ' ';
        };
    }
}