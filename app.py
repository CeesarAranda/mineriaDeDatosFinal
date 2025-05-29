

from flask import Flask, render_template
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_required, current_user
from flask_talisman import Talisman
from models import db
from models.usuarios import Usuario
from routes.libros_bp import libros_bp
from routes.autores_bp import autores_bp
from routes.usuarios_bp import usuarios_bp
from routes.prestamos_bp import prestamos_bp
from routes.auth_bp import auth_bp
from config import Config
import os

# Inicializar extensiones
login_manager = LoginManager()
migrate = Migrate()






def create_app():
    # Crear la aplicación Flask
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializar extensiones con la aplicación
    db.init_app(app)  
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Configurar Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, inicia sesión para acceder a esta página.'
    login_manager.login_message_category = 'info'

    # Registrar blueprints
    app.register_blueprint(libros_bp, url_prefix="/libros")
    app.register_blueprint(autores_bp, url_prefix="/autores")
    app.register_blueprint(usuarios_bp, url_prefix="/usuarios")
    app.register_blueprint(prestamos_bp, url_prefix="/prestamos")
    app.register_blueprint(auth_bp, url_prefix="/auth")

    
    return app





# Cargar el usuario para Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# Crear la aplicación
app = create_app()
# app.config['UPLOAD_FOLDER'] = 'static/img'
app.config['WTF_CSRF_ENABLED'] = False

app.config['SESSION_COOKIE_SAMESITE'] = "None"
app.config['SESSION_COOKIE_SECURE'] = True

CORS(app)



if __name__ == "__main__":
    app.run(debug=True)

@app.context_processor
def inject_user():
    return dict(current_user=current_user)




