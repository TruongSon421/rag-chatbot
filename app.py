from flask import Flask
from routes import crud_blueprint
from models import Admin, db
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://tiendoan:tiendoan@localhost:3300/document_store'
db.init_app(app)
migrate = Migrate(app, db)

app.register_blueprint(crud_blueprint)
def create_default_admin():
    if not Admin.query.first():
        admin = Admin(username="admin", email="admin@example.com", password="admin123")
        db.session.add(admin)
        db.session.commit()
        print("Default admin created: username='admin', password='admin123'")
    else:
        print("Admin account already exists.")
        
if __name__ == '__main__':
    # with app.app_context():
    #     create_default_admin()  
    app.run(port=5000,debug=True)

