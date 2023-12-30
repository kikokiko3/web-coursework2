function toggleLike(movieId) {
    $.ajax({
        url: toggleLikeUrl,
        type: 'GET',
        data: { movie_id: movieId },
        success: function(response) {
            var btn = $('#like-btn-' + movieId);
            if (!response.logged_in) {
                window.location.href = '/login';
            } 
            else if (response.success) {
                if (btn.hasClass('added')) {
                    btn.removeClass('added');
                    btn.html('+ ADD YOUR LIST');
                } else {
                    btn.addClass('added');
                    btn.html('&#10004; ADDED TO LIST');
                }
            } else {
                alert(response.message);
            }
        }
    });
}
