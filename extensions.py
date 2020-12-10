from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

mail = Mail()
db = SQLAlchemy()
csrf_protect = CSRFProtect()

