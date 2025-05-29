from .import db

class Libro(db.Model):
    __tablename__ = 'libro'
    id_libro = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)

    autor_id = db.Column(db.Integer, db.ForeignKey('autor.id_autor'), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categoria.id_categoria'), nullable=False)

    prestamos = db.relationship('Prestamo', backref='libro', lazy=True)
    stock = db.Column(db.Integer, nullable=False, default=0)

    #LINEA DE PRUEBA
    autor = db.relationship('Autor', lazy=True)
    categoria = db.relationship('Categoria', lazy=True)
    imagen_url = db.Column(db.String(255)) 