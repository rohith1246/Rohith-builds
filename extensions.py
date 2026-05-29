from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from flask_migrate import Migrate

db = SQLAlchemy()

migrate = Migrate()

csrf = CSRFProtect()

login_manager = LoginManager()