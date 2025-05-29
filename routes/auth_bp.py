from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user
from werkzeug.security import check_password_hash
from models.usuarios import Usuario

auth_bp = Blueprint('auth', __name__, url_prefix='/')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form.get('correo')
        contraseña = request.form.get('contraseña')

        # Busca el usuario por correo
        usuario = Usuario.query.filter_by(correo=correo).first()

        if usuario and check_password_hash(usuario.contraseña, contraseña):
            login_user(usuario)
            flash(f'Bienvenido de nuevo, {usuario.nombre}', 'success')
            
            if usuario.es_admin:  # Si es admin
                return redirect(url_for('libros.lista_libros'))  # O la ruta que uses para admin
            else:  # Si es usuario normal
                return redirect(url_for('libros.principal'))  # Ruta de usuario normal

        else:
            flash('Correo o contraseña incorrectos', 'danger')
            return redirect(url_for('auth.login'))

    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    logout_user()
    flash('Sesión cerrada correctamente', 'success')
    return redirect(url_for('auth.login'))
