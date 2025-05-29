from datetime import datetime, timedelta
from flask import Blueprint, jsonify, render_template, request, redirect, url_for,flash
from werkzeug.security import generate_password_hash
from models import db, Usuario
from models.libros import Libro
from models.prestamo import Prestamo

usuarios_bp = Blueprint("usuarios", __name__, template_folder="../templates/usuarios")

@usuarios_bp.route("/")
def lista_usuarios():
    usuarios = Usuario.query.order_by(usuarios.id_usuario.desc()).limit(10).all()    # Limita a los primeros 10 usuarios

    return render_template("lista.html", usuarios=usuarios)

@usuarios_bp.route("/crear", methods=["GET", "POST"])
def crear_usuario():
    if request.method == "POST":
        nuevo = Usuario(nombre=request.form["nombre"])
        db.session.add(nuevo)
        db.session.commit()
        return redirect(url_for("usuarios.lista_usuarios"))
    return render_template("crear.html")



usuarios_bp = Blueprint('usuarios', __name__, url_prefix='/usuarios')

@usuarios_bp.route('/crear', methods=['POST'])
def crear_usuario():
    nombre = request.form['nombre']
    correo = request.form['correo']
    contraseña = request.form['contraseña']
    es_admin = True if request.form.get('es_admin') == 'true' else False

    # Verificar si el correo ya existe
    if Usuario.query.filter_by(correo=correo).first():
        flash('El correo ya está registrado.', 'danger')
        return redirect(url_for('libros.lista_libros'))

    nuevo_usuario = Usuario(
        nombre=nombre,
        correo=correo,
        contraseña=generate_password_hash(contraseña),
        es_admin=es_admin
    )
    db.session.add(nuevo_usuario)
    db.session.commit()
    flash('Usuario creado correctamente.', 'success')
    return redirect(url_for('libros.lista_libros'))



# Ruta para editar un usuario desde el modal
@usuarios_bp.route('/editar_usuario/<int:id>', methods=['POST'])
def editar_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    usuario.nombre = request.form['nombre']
    usuario.correo = request.form['correo']

    contraseña = request.form.get('contraseña')
    if contraseña:
        usuario.contraseña = generate_password_hash(contraseña)

    usuario.es_admin = True if request.form.get('es_admin') else False

    # Actualizar préstamos activos
    prestamos_ids = request.form.getlist('prestamo_id[]')
    for pid in prestamos_ids:
        prestamo = Prestamo.query.get(int(pid))
        if not prestamo:
            continue

        fecha_salida = request.form.get(f'fecha_salida_{pid}')
        fecha_devolucion = request.form.get(f'fecha_devolucion_{pid}')
        devuelto = request.form.get(f'devuelto_{pid}') == 'on'

        if fecha_salida:
            prestamo.fecha_salida = datetime.strptime(fecha_salida, '%Y-%m-%d')
        if fecha_devolucion:
            prestamo.fecha_devolucion = datetime.strptime(fecha_devolucion, '%Y-%m-%d')
        prestamo.devuelto = devuelto

    try:
        db.session.commit()
        flash("Usuario y préstamos editados correctamente.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al editar: {e}", "danger")

    return redirect(url_for('usuarios.lista_usuarios'))




# Ruta para eliminar un usuario
@usuarios_bp.route('/eliminar_usuario/<int:id>', methods=['POST'])
def eliminar_usuario(id):
    usuario = Usuario.query.get_or_404(id)

    # Verificar si el usuario tiene préstamos activos
    prestamos_activos = Prestamo.query.filter(Prestamo.usuario_id == id, Prestamo.devuelto == False).first()

    if prestamos_activos:
        flash("No puedes eliminar este usuario porque tiene préstamos activos.", "danger")
        return redirect(url_for('libros.lista_libros'))

    try:
        # Eliminar todos los préstamos relacionados con el usuario
        Prestamo.query.filter(Prestamo.usuario_id == id).delete()

        # Eliminar el usuario
        db.session.delete(usuario)
        db.session.commit()
        flash("Usuario eliminado correctamente.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar el usuario: {e}", "danger")

    return redirect(url_for('libros.lista_libros'))



@usuarios_bp.route('/usuarios/<int:usuario_id>/libros_prestados')
def libros_prestados(usuario_id):
    usuario = Usuario.query.get(usuario_id)
    if usuario:
        libros_prestados = []
        
        # Obtener los préstamos relacionados con el usuario
        prestamos = Prestamo.query.filter_by(usuario_id=usuario.id_usuario).all()

        # Obtener la fecha actual
        hoy = datetime.now()

        for prestamo in prestamos:
            libro = prestamo.libro
            alerta = None

            # Verificar si la fecha de devolución está pasada o próxima
            if prestamo.fecha_devolucion <= hoy:
                alerta = '¡Fecha de devolución vencida!'
            elif prestamo.fecha_devolucion <= hoy + timedelta(days=2):  # Vencimiento dentro de 2 días
                alerta = '¡Devolución próxima!'

            libros_prestados.append({
                'titulo': libro.titulo,
                'autor': libro.autor_libros.nombre,
                'fecha_salida': prestamo.fecha_salida.strftime('%Y-%m-%d'),
                'fecha_devolucion': prestamo.fecha_devolucion.strftime('%Y-%m-%d'),
                'devuelto': 'Sí' if prestamo.devuelto else 'No',
                'alerta': alerta
            })
        
        return jsonify({'libros': libros_prestados})
    
    return jsonify({'libros': []}), 404



#bp usuarios normales



from flask import jsonify

@usuarios_bp.route('/buscar', methods=['GET'])
def buscar_usuario():
    q = request.args.get('q', '')
    if not q:
        return jsonify([])

    usuarios = Usuario.query.filter(
        (Usuario.nombre.ilike(f'%{q}%')) | (Usuario.correo.ilike(f'%{q}%'))
    ).limit(5).all()

    resultado = []
    for u in usuarios:
        prestamos = Prestamo.query.filter_by(usuario_id=u.id_usuario, devuelto=False).all()
        prestamos_data = []
        for p in prestamos:
            prestamos_data.append({
                'id': p.id_prestamo,
                'titulo': p.libro.titulo,
                'fecha_salida': p.fecha_salida.strftime('%Y-%m-%d'),
                'fecha_devolucion': p.fecha_devolucion.strftime('%Y-%m-%d'),
                'vencido': p.fecha_devolucion < datetime.now()
            })

        resultado.append({
            'id_usuario': u.id_usuario,
            'nombre': u.nombre,
            'correo': u.correo,
            'es_admin': u.es_admin,
            'prestamos': prestamos_data
        })

    return jsonify(resultado)

#registro de usuarios
@usuarios_bp.route('/registro', methods=['GET', 'POST'])
def registrar():
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        contraseña = request.form['contraseña']

        # Validar si el correo ya está en uso
        if Usuario.query.filter_by(correo=correo).first():
            flash('Este correo ya está registrado.', 'danger')
            return redirect(url_for('usuarios.registrar'))

        nuevo_usuario = Usuario(
            nombre=nombre,
            correo=correo,
            contraseña=generate_password_hash(contraseña),
        )
        db.session.add(nuevo_usuario)
        db.session.commit()
        flash('Usuario registrado exitosamente.', 'success')
        return redirect(url_for('auth.login'))  # Redirigir a la página de inicio de sesión

    return render_template('auth/registro.html')



