from core import app
from flask.ext.login import LoginManager, current_user
from core.models import DBUser

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

app.jinja_env.globals.update(current_user=current_user)

@login_manager.user_loader
def loadUser(id):
	return DBUser.query.get(int(id))
