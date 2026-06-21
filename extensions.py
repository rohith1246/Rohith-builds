"""Shared Flask extensions for the Rohith Builds application."""

from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

db: SQLAlchemy = SQLAlchemy()
migrate: Migrate = Migrate()
csrf: CSRFProtect = CSRFProtect()
login_manager: LoginManager = LoginManager()