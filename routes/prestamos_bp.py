# Blueprint para la funcionalidad de préstamos
from datetime import date, datetime, timedelta
from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import login_required, current_user
from models import db
from models.libros import Libro
from models.prestamo import Prestamo
from models.usuarios import Usuario

prestamos_bp = Blueprint('prestamos', __name__, url_prefix='/prestamos')

@prestamos_bp.route("/")
def lista_prestamos():
    prestamos = Prestamo.query.all()
    return render_template("lista.html", prestamos=prestamos)

@prestamos_bp.route("/libros_prestados/<int:usuario_id>")
def libros_prestados(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    prestamos = Prestamo.query.filter_by(usuario_id=usuario_id, devuelto=False).all()
    libros_prestados = []

    for prestamo in prestamos:
        libro = Libro.query.get(prestamo.libro_id)
        libros_prestados.append({
            'id_prestamo': prestamo.id_prestamo,
            'titulo': libro.titulo,
            'autor': libro.autor_libros.nombre,
            'fecha_salida': prestamo.fecha_salida.strftime('%Y-%m-%d'),
            'fecha_devolucion': prestamo.fecha_devolucion.strftime('%Y-%m-%d'),
            'devuelto': prestamo.devuelto
        })
    
    return jsonify({
        'nombre_usuario': usuario.nombre,
        'libros': libros_prestados
    })

@prestamos_bp.route("/devolver/<int:id_prestamo>", methods=["POST"])
def devolver_libro(id_prestamo):
    prestamo = Prestamo.query.get_or_404(id_prestamo)
    prestamo.devuelto = True

    # Devolver stock al libro
    libro = Libro.query.get(prestamo.libro_id)
    if libro:
        libro.stock += 1

    db.session.commit()
    return jsonify({'success': True})

@prestamos_bp.route('/crear', methods=['POST'])
def crear_prestamo():
    usuario_id = request.form.get('usuario_id')
    libro_id = request.form.get('libro_id')
    fecha_salida = request.form.get('fecha_salida')
    fecha_devolucion = request.form.get('fecha_devolucion')

    libro = Libro.query.get(libro_id)
    if not libro or libro.stock < 1:
        flash("El libro no está disponible o no existe.", "danger")
        return redirect(url_for('libros.lista_libros'))

    nuevo_prestamo = Prestamo(
        usuario_id=usuario_id,
        libro_id=libro_id,
        fecha_salida=datetime.strptime(fecha_salida, '%Y-%m-%d'),
        fecha_devolucion=datetime.strptime(fecha_devolucion, '%Y-%m-%d'),
        devuelto=False
    )

    libro.stock -= 1
    db.session.add(nuevo_prestamo)
    db.session.commit()

    flash("Préstamo agregado correctamente.", "success")
    return redirect(url_for('libros.lista_libros'))

# ------------------------------
@prestamos_bp.route('/agregar/<int:libro_id>', methods=['POST'])
@login_required
def agregar_prestamo(libro_id):
    libro = Libro.query.get_or_404(libro_id)

    # Validar si el usuario ya tiene un préstamo activo del mismo libro
    prestamo_existente = Prestamo.query.filter_by(
        usuario_id=current_user.id_usuario,
        libro_id=libro_id,
        devuelto=False
    ).first()

    if prestamo_existente:
        flash('Ya tienes un préstamo activo de este libro.', 'warning')
        return redirect(url_for('libros.principal'))

    if libro.stock <= 0:
        flash('No hay stock disponible para este libro.', 'danger')
        return redirect(url_for('libros.principal'))

     #Definimos fecha_salida y fecha_devolucion correctamente
    fecha_salida = datetime.now()
    fecha_devolucion = fecha_salida + timedelta(days=7)

    nuevo_prestamo = Prestamo(
        usuario_id=current_user.id_usuario,
        libro_id=libro_id,
        fecha_salida=fecha_salida,
        fecha_devolucion=fecha_devolucion,
        devuelto=False
    )


    libro.stock -= 1
    db.session.add(nuevo_prestamo)
    db.session.commit()

    flash('Préstamo solicitado exitosamente.', 'success')
    return redirect(url_for('libros.principal'))
# ------------------------------
