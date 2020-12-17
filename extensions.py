from flask_bcrypt import Bcrypt
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate

bcrypt = Bcrypt()
mail = Mail()
db = SQLAlchemy()
csrf_protect = CSRFProtect()
migrate = Migrate()

