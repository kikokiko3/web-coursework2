import os

# Getting the absolute path of the directory where the script is located
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Configuring the SQLite database URI
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(
    BASE_DIR, 'CineExplorer.db')

# Disabling the Flask-SQLAlchemy event system
SQLALCHEMY_TRACK_MODIFICATIONS = False
