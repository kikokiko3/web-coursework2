# Importing necessary modules and components from Flask and SQLAlchemy
from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from sqlalchemy.exc import OperationalError
from config import SQLALCHEMY_DATABASE_URI
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.datastructures import FileStorage
import pandas as pd
from sqlalchemy import func
from sqlalchemy.sql.expression import func
from datetime import datetime

# Initializing Flask app
app = Flask(__name__)
app.secret_key = 'kiko'

# Configuring database URI for the app
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
# Initializing SQLAlchemy instance
db = SQLAlchemy(app)
# Initializing migration instance
migrate = Migrate(app, db)

likes = db.Table('likes',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('movie_id', db.Integer, db.ForeignKey('movie.id'), primary_key=True)
)

movie_tags = db.Table('movie_tags',
    db.Column('movie_id', db.Integer, db.ForeignKey('movie.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    liked_movies = db.relationship('Movie', secondary=likes, backref=db.backref('liked_by', lazy='dynamic'))

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post = db.Column(db.Text, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    certificate = db.Column(db.String(50))
    runtime = db.Column(db.String(50))
    tag = db.Column(db.String(200))
    score = db.Column(db.Float)
    score_100 = db.Column(db.Integer)
    overview = db.Column(db.Text)
    director = db.Column(db.String(100))
    star = db.Column(db.String(200))
    tags = db.relationship('Tag', secondary=movie_tags, backref=db.backref('movies', lazy='dynamic'))

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)

    user = db.relationship('User', backref='comments')
    movie = db.relationship('Movie', backref='comments')

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False, unique=True)

class SystemLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action = db.Column(db.String(200), nullable=False)
    details = db.Column(db.Text)

    user = db.relationship('User', backref='system_logs')



# Ensure all tables are created before any request
@app.before_request
def create_tables_if_not_exists():
    try:
        db.create_all()
    except OperationalError:
        pass

@app.route('/')
def index():
    movies = Movie.query.all()
    recommended_movies = []

    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            liked_movies = user.liked_movies
            if liked_movies:
                recommended_movies = recommend_movies(user.id)
            else:
                recommended_movies = Movie.query.order_by(func.random()).limit(4).all()
        else:
            session.pop('user_id', None)
            session.pop('username', None)
            recommended_movies = Movie.query.order_by(func.random()).limit(4).all()

        return render_template('index.html', user=user, movies=movies, recommended_movies=recommended_movies)
    else:
        return render_template('index.html', user=None, movies=movies)



@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/movies')
def movies_page():
    tag_name = request.args.get('tag')
    page = request.args.get('page', 1, type=int)

    available_tags = [tag.name for tag in Tag.query.all()]

    if tag_name:
        tag = Tag.query.filter_by(name=tag_name).first()
        if tag:
            movies = Movie.query.filter(Movie.tags.contains(tag)).paginate(page=page, per_page=24, error_out=False)
        else:
            movies = Movie.query.paginate(page=page, per_page=24, error_out=False)
    else:
        movies = Movie.query.paginate(page=page, per_page=24, error_out=False)

    return render_template('movies.html', movies=movies, available_tags=available_tags)


@app.route('/movie_single')
def movie_single_page():
    movie_id = request.args.get('movie_id')
    movie = Movie.query.get(movie_id)
    user_liked = False

    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user and movie:
            user_liked = movie in user.liked_movies

    related_movies = Movie.query.filter(Movie.tag == movie.tag, Movie.id != movie.id).limit(6).all()
    comments = Comment.query.filter_by(movie_id=movie_id).all()
    return render_template('movie_single.html', movie=movie, user_liked=user_liked, related_movies=related_movies, comments=comments)



@app.route('/movie_like')
def movie_like_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))

    user_id = session.get('user_id')
    user = User.query.get(user_id)

    if user is None:
        session.pop('user_id', None)
        session.pop('username', None)
        return redirect(url_for('login_page'))

    liked_movies = user.liked_movies
    return render_template('movie_like.html', movies=liked_movies)


@app.route('/movie_manage', methods=['GET'])
def movie_manage():
    movie_page = request.args.get('movie_page', 1, type=int)
    user_page = request.args.get('user_page', 1, type=int)
    comment_page = request.args.get('comment_page', 1, type=int)
    log_page = request.args.get('log_page', 1, type=int)
    active_tab = request.args.get('active_tab', 'system-log')

    movies = Movie.query.paginate(page=movie_page, per_page=25, error_out=False)
    users = User.query.paginate(page=user_page, per_page=25, error_out=False)
    comments = Comment.query.paginate(page=comment_page, per_page=25, error_out=False)
    logs = SystemLog.query.order_by(SystemLog.timestamp.desc()).paginate(page=log_page, per_page=25, error_out=False)

    return render_template('movie_manage.html', logs=logs, movies=movies, users=users, comments=comments, active_tab=active_tab)





@app.route('/add_user', methods=['POST'])
def add_user():
    try:
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        existing_username = User.query.filter_by(username=username).first()
        if existing_username:
            return jsonify({'success': False, 'message': 'Username already exists!'}), 400

        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            return jsonify({'success': False, 'message': 'Email already exists!'}), 400

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        # Now log the action after committing the new user to the database
        log_action(user_id=new_user.id, action="User Registration", details=f"New user registered: {username}")

        return jsonify({'success': True, 'redirect': url_for('login_page')})
    except Exception as e:
        print(e)
        return jsonify(success=False, message="Failed to add user.")


@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    user = User.query.filter_by(username=username).first()

    if not user:
        return jsonify({'success': False, 'message': 'Username does not exist.'})
    elif not check_password_hash(user.password, password):
        return jsonify({'success': False, 'message': 'Incorrect password.'})
    else:
        # Storing essential user information in session
        session['user_id'] = user.id
        session['username'] = user.username

        # Log the action after user is successfully logged in and session is updated
        log_action(user_id=user.id, action="User Login", details=f"User {username} logged in")

        return jsonify({'success': True, 'redirect': url_for('index')})


@app.route('/logout')
def logout():
    user_id = session.get('user_id', None)
    if user_id:
        log_action(user_id=user_id, action="User Logout", details=f"User with ID {user_id} logged out")
    session.pop('user_id', None)
    session.pop('username', None)

    return redirect(url_for('index'))


@app.route('/change_user')
def change_user():
    session.pop('user_id', None)
    session.pop('username', None)

    return redirect(url_for('login'))


@app.route('/upload_movie_from_excel', methods=['POST'])
def upload_movie_from_excel():
    try:
        file: FileStorage = request.files['excelUpload']
        if not file:
            return jsonify(success=False, message="No file provided.")
        
        df = pd.read_excel(file, engine='openpyxl')

        for _, row in df.iterrows():
            title = row['title']

            # 检查电影标题是否已存在
            existing_movie = Movie.query.filter_by(title=title).first()
            if existing_movie:
                continue  # 如果存在相同标题的电影，则跳过此条目

            # 以下为创建和添加电影的代码
            post = row['post']
            year = row['year']
            certificate = row['certificate']
            runtime = row['runtime']
            tag = row['tag']
            score = row['score']
            score_100 = row['score_100']-10
            overview = row['overview']
            director = row['director']
            star = row['star']

            new_movie = Movie(post=post, title=title, year=year, certificate=certificate,
                              runtime=runtime, tag=tag, score=score, score_100=score_100,
                              overview=overview, director=director, star=star)

            movie_tags = tag.split(',')
            for tag_name in movie_tags:
                tag_name = tag_name.strip()
                tag_instance = Tag.query.filter_by(name=tag_name).first()
                if not tag_instance:
                    tag_instance = Tag(name=tag_name)
                    db.session.add(tag_instance)
                new_movie.tags.append(tag_instance)

            db.session.add(new_movie)
        
        db.session.commit()
        user_id = session.get('user_id')
        log_action(user_id=user_id, action="Upload Movie", details="Movies uploaded from Excel file")
        return jsonify(success=True, message="Successfully add movie.")
    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        print(error_message)
        return jsonify(success=False, message=error_message), 500



@app.route('/toggle_like')
def toggle_like():
    movie_id = request.args.get('movie_id')
    if 'user_id' not in session:
        return jsonify(success=False, logged_in=False, message="User not logged in")
    
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    movie = Movie.query.get(movie_id)
    
    if movie and user:
        if movie in user.liked_movies:
            user.liked_movies.remove(movie)
            action = 'removed'
        else:
            user.liked_movies.append(movie)
            action = 'added'
        db.session.commit()

        details = f"User {user.username} {'liked' if action == 'added' else 'disliked'} movie with ID {movie_id}"
        log_action(user_id=user_id, action=f"Toggle Like Movie", details=details)
        
        return jsonify(success=True, logged_in=True, message=f"Movie {action} from likes")
    
    return jsonify(success=False, message="Movie not found")



@app.route('/add_comment', methods=['POST'])
def add_comment():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))

    movie_id = request.form.get('movie_id')
    content = request.form.get('content')
    user_id = session.get('user_id')

    if movie_id and content and user_id:
        comment = Comment(content=content, user_id=user_id, movie_id=movie_id)
        db.session.add(comment)
        db.session.commit()
        log_action(user_id=user_id, action="Add Comment", details=f"User {user_id} commented on movie {movie_id}")
        return redirect(url_for('movie_single_page', movie_id=movie_id))

    return redirect(url_for('index'))


def recommend_movies(user_id):
    user = User.query.get(user_id)
    liked_movies = user.liked_movies
    movie_scores = {}
    liked_movies_ids = {movie.id for movie in liked_movies}

    liked_tags = {tag.name for movie in liked_movies for tag in movie.tags}

    for movie in Movie.query.all():
        if movie.id in liked_movies_ids:
            continue

        movie_tags = {tag.name for tag in movie.tags}
        matching_tags = liked_tags.intersection(movie_tags)
        score = len(matching_tags)*10 + movie.score

        if matching_tags:
            movie_scores[movie.id] = (score, movie)

    top_20_movies = [movie for _, movie in sorted(movie_scores.values(), key=lambda x: x[0], reverse=True)[:20]]

    # 从这20个电影中选择名字不同的四个
    recommended_movies = []
    movie_titles = set()
    for movie in top_20_movies:
        if movie.title not in movie_titles and len(recommended_movies) < 4:
            recommended_movies.append(movie)
            movie_titles.add(movie.title)
    return recommended_movies


def log_action(user_id, action, details=None):
    log_entry = SystemLog(user_id=user_id, action=action, details=details)
    db.session.add(log_entry)
    db.session.commit()

@app.route('/add_movie', methods=['GET', 'POST'])
def add_movie():
    if request.method == 'POST':
        try:
            # 获取表单数据
            post = request.form.get('post')
            title = request.form.get('title')
            year = int(request.form.get('year'))
            certificate = request.form.get('certificate')
            runtime = request.form.get('runtime')
            tag = request.form.get('tag')
            score = float(request.form.get('score'))
            overview = request.form.get('overview')
            director = request.form.get('director')
            star = request.form.get('star')

            # 创建新电影实例
            new_movie = Movie(post=post, title=title, year=year, certificate=certificate, 
                              runtime=runtime, tag=tag, score=score, 
                              overview=overview, director=director, star=star)

            # 保存到数据库
            db.session.add(new_movie)
            db.session.commit()

            # 记录系统日志
            user_id = session.get('user_id')
            log_action(user_id, 'Add Movie', f'Added movie: {title}')
            return jsonify(success=True, message="Movie added successfully.")
        except Exception as e:
            return jsonify(success=False, message=str(e))

@app.route('/delete_movie/<int:movie_id>', methods=['POST'])
def delete_movie(movie_id):
    try:
        movie = Movie.query.get(movie_id)
        if movie:
            db.session.delete(movie)
            db.session.commit()

            # 记录系统日志
            user_id = session.get('user_id')
            log_action(user_id, 'Delete Movie', f'Deleted movie: {movie.title}')
            return jsonify(success=True, message="Movie deleted successfully.")
        else:
            return jsonify(success=False, message="Movie not found.")
    except Exception as e:
        return jsonify(success=False, message=str(e))



@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    try:
        user = User.query.get(user_id)
        if user:
            db.session.delete(user)
            db.session.commit()
            log_action(session.get('user_id'), 'Delete User', f'Deleted user: {user.username}')
            return jsonify(success=True, message="User successfully deleted.")
        else:
            return jsonify(success=False, message="User not found."), 404
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500


@app.route('/delete_comment/<int:comment_id>', methods=['POST'])
def delete_comment(comment_id):
    comment = Comment.query.get(comment_id)
    if comment:
        db.session.delete(comment)
        db.session.commit()
        # 记录系统日志
        user_id = session.get('user_id')
        log_action(user_id, 'Delete comment', f'Deleted comment: {comment.id}')
        return jsonify(success=True, message="Comment deleted successfully.")
    return jsonify(success=False, message="Comment not found.")


# Run the app in debug mode
if __name__ == "__main__":
    app.run(debug=True)
