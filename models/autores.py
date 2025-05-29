from . import db




class Autor(db.Model):
    __tablename__ = 'autor'
    id_autor = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)

    libros = db.relationship('Libro', backref='autor_libros', lazy=True)
