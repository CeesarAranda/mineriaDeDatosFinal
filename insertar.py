from app import app, db
from models.usuarios import Usuario
from werkzeug.security import generate_password_hash

with app.app_context():  # Necesario para usar la base de datos
    usuario = Usuario(
        nombre='prueba',
        correo='prueba@gmail',
        contraseña=generate_password_hash('1234'),
        es_admin=False
    )
    db.session.add(usuario)
    db.session.commit()
    print(" Usuario creado con contraseña hasheada")
