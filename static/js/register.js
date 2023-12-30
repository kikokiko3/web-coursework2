document.getElementById('add_user').addEventListener('submit', function(event) {
    var username = document.getElementById('yourUsername').value;
    var email = document.getElementById('yourEmail').value;

    if (!username || !email) {
        alert('Username and email cannot be empty.');
        event.preventDefault();
    }
});

document.getElementById('add_user').addEventListener('submit', function(event) {
    event.preventDefault();
    fetch('/add_user', {
      method: 'POST',
      body: new FormData(this)
    })
    .then(response => response.json())
    .then(data => {
    if (data.success) {
        alert('Account created successfully!');
        window.location.href = data.redirect;
        } else {
        alert(data.message);
        }
    })
    .catch((error) => {
      console.error('Error:', error);
    });
  });