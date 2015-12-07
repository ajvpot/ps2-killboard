from sqlalchemy.exc import OperationalError, IntegrityError
from core.models import db, DBUser
try:
	print "Creating schema..."
	db.create_all()
	print "Committing schema..."
	db.session.commit()

	print "Creating admin user"
	user = DBUser('admin', 'admin@admin.com', 'admin', access=10)
	db.session.add(user)
	db.session.commit()

	print "Successfully set up DB. Log in with admin:admin"
	print "Be sure to change your password."

except OperationalError as e:
	print "Error: Failed to provision database.\n" \
		  "Did you edit core/__init__.py with your config values?\n" \
		  "Exception: %s" % e
except IntegrityError as e:
	print "Error: There's already an admin user.\n" \
		  "We can't add another one."