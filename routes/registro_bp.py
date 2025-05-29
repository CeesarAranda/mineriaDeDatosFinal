from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash
from models.usuarios import Usuario
from models import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        contraseña = request.form['contraseña']

        # Verificar si el correo ya está registrado
        usuario_existente = Usuario.query.filter_by(correo=correo).first()
        if usuario_existente:
            flash('El correo ya está registrado.', 'danger')
            return redirect(url_for('auth.registro'))

        # Crear un nuevo usuario
        nueva_contraseña = generate_password_hash(contraseña)
        nuevo_usuario = Usuario(nombre=nombre, correo=correo, contraseña=nueva_contraseña)
        db.session.add(nuevo_usuario)
        db.session.commit()

        flash('Registro exitoso. Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/registro.html')