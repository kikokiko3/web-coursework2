document.getElementById('my_login').addEventListener('submit', function(event) {
    event.preventDefault();
    fetch('/login', {
        method: 'POST',
        body: new FormData(this)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.href = data.redirect;
        } else {
            alert(data.message);
        }
    })
    .catch((error) => {
        console.error('Error:', error);
    });
});