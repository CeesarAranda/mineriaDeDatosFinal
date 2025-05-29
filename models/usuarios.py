from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash



class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuario'
    id_usuario = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(100), unique=True, nullable=False)
    contraseña = db.Column('contraseña', db.String(200), nullable=False)
    es_admin = db.Column(db.Boolean, default=False)
    prestamos = db.relationship('Prestamo', backref='usuario', lazy=True)

   
 # Sobrescribir el método get_id para que use id_usuario
    def get_id(self):
        return str(self.id_usuario)
    




    