$(document).ready(function() {
    $('#add-movie-form').submit(function(e) {
        e.preventDefault();
        $.ajax({
            url: addMovieUrl,  // 直接使用后端路由
            type: 'POST',
            data: $(this).serialize(),
            success: function(response) {
                alert(response.message);
                if(response.success) {
                    $('#add-movie-form').trigger('reset');  // 清空表单
                }
            }
        });
    });
  });
  
  document.addEventListener("DOMContentLoaded", function() {
    var form = document.getElementById('excel-upload-form');
    form.addEventListener('submit', function(e) {
        e.preventDefault();

        var formData = new FormData(form);

        fetch(addMovieExcel, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            if (data.success) {
                form.reset();
            }
        })
        .catch(error => {
            alert('Error: ' + error);
        });
    });
});

function deleteMovie(buttonElement) {
    var movieId = $(buttonElement).data('id');
    var baseUrl = $('meta[name="urls"]').data('delete-url');
    var deleteUrl = baseUrl.replace('/0', '/' + movieId);

    $.ajax({
        url: deleteUrl,
        type: 'POST',
        success: function(response) {
            if (response.success) {
                // 删除成功后从表格中移除该行
                $(`#movie-${movieId}`).remove();
                alert("Movie deleted successfully.");
            } else {
                alert(response.message);
            }
        },
        error: function() {
            alert("An error occurred while deleting the movie.");
        }
    });
}

function deleteUser(buttonElement) {
    var userId = $(buttonElement).data('id');
    var deleteUrl = $('meta[name="urls1"]').data('delete-user-url').replace('/0', '/' + userId);

    $.ajax({
        url: deleteUrl,
        type: 'POST',
        success: function(response) {
            if(response.success) {
                alert('User deleted successfully');
                $(`#user-${userId}`).remove();
            } else {
                alert(response.message);
            }
        },
        error: function() {
            alert('An error occurred');
        }
    });
}

function deleteComment(buttonElement) {
    var commentId = $(buttonElement).data('id');
    var deleteUrl = $('meta[name="urls2"]').data('delete-comment-url').replace('/0', '/' + commentId);

    $.ajax({
        url: deleteUrl,
        type: 'POST',
        success: function(response) {
            if(response.success) {
                alert('Comment deleted successfully');
                $(`#comment-${commentId}`).remove();
            } else {
                alert(response.message);
            }
        },
        error: function() {
            alert('An error occurred');
        }
    });
}
