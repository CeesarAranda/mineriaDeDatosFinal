from datetime import datetime
from . import db



class Prestamo(db.Model):
    __tablename__ = 'prestamo'
    id_prestamo = db.Column(db.Integer, primary_key=True)

    libro_id = db.Column(db.Integer, db.ForeignKey('libro.id_libro'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)

    fecha_salida = db.Column(db.DateTime, nullable=False)
    fecha_devolucion = db.Column(db.DateTime, nullable=False)
    devuelto = db.Column(db.Boolean, default=False)

    @property
    def dias_restantes(self):
        hoy = datetime.now().date()
        dias_restantes = (self.fecha_devolucion - hoy).days
        return dias_restantes