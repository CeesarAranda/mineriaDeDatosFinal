from . import db



class Categoria(db.Model):
    __tablename__ = 'categoria'
    id_categoria = db.Column(db.Integer, primary_key=True)
    categoria = db.Column(db.String(100), nullable=False)

    libros = db.relationship('Libro', backref='categoria_libros', lazy=True)
