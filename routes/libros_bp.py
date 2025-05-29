from datetime import datetime
import os
from flask import Blueprint, abort, flash, render_template, request, redirect, send_file, url_for
from flask_login import current_user
from sqlalchemy import Table
from models import db, Libro, Autor, Categoria
from models.prestamo import Prestamo
from models.usuarios import Usuario
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet

libros_bp = Blueprint("libros", __name__, template_folder="../templates/libros")


@libros_bp.route("/")
def lista_libros():
    if not current_user.is_authenticated or not current_user.es_admin:
        abort(403)
    libros = Libro.query.order_by(Libro.id_libro.desc()).limit(10).all()
    usuarios = Usuario.query.limit(10).all()
    return render_template('libros/lista.html', libros=libros, usuarios=usuarios)


@libros_bp.route("/busqueda", methods=["GET"])
def libros_busqueda():
    titulo = request.args.get('titulo', '')
    autor = request.args.get('autor', '')
    categoria = request.args.get('categoria', '')

    query = Libro.query
    if titulo:
        query = query.filter(Libro.titulo.ilike(f'%{titulo}%'))
    if autor:
        query = query.join(Autor).filter(Autor.nombre.ilike(f'%{autor}%'))
    if categoria:
        query = query.join(Categoria).filter(Categoria.categoria.ilike(f'%{categoria}%'))

    libros = query.order_by(Libro.id_libro.desc()).all()
    return render_template("resultados_busqueda_libros.html", libros=libros)


def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@libros_bp.route("/crear", methods=["GET", "POST"])
def crear_libro():
    if not current_user.is_authenticated or not current_user.es_admin:
        abort(403)

    if request.method == "POST":
        file = request.files.get('imagen')
        imagen_url = None

        if file and allowed_file(file.filename):
            filename = file.filename
            file.save(os.path.join('static/img', filename))
            imagen_url = f'img/{filename}'  

        autor_nombre = request.form.get("autor_nombre").strip()
        autor = Autor.query.filter_by(nombre=autor_nombre).first()
        if not autor:
            autor = Autor(nombre=autor_nombre)
            db.session.add(autor)
            db.session.flush()

        categoria_nombre = request.form.get("categoria_nombre").strip()
        categoria = Categoria.query.filter_by(categoria=categoria_nombre).first()
        if not categoria:
            categoria = Categoria(categoria=categoria_nombre)
            db.session.add(categoria)
            db.session.flush()

        nuevo = Libro(
            titulo=request.form["titulo"],
            autor_id=autor.id_autor,
            categoria_id=categoria.id_categoria,
            stock=request.form["stock"],
            imagen_url=imagen_url
        )
        db.session.add(nuevo)
        db.session.commit()
        return redirect(url_for("libros.lista_libros"))

    autores = Autor.query.all()
    categorias = Categoria.query.all()
    return render_template("libros/crear.html", autores=autores, categorias=categorias)


@libros_bp.route('/eliminar/<int:id>', methods=['POST'])
def eliminar_libro(id):
    libro = Libro.query.get_or_404(id)
    prestamos_asociados = Prestamo.query.filter_by(libro_id=libro.id_libro).first()
    if prestamos_asociados:
        flash("No se puede eliminar el libro porque tiene préstamos asociados.", "danger")
        return redirect(url_for('libros.lista_libros'))

    try:
        db.session.delete(libro)
        db.session.commit()
        flash("Libro eliminado correctamente.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar el libro: {e}", "danger")

    return redirect(url_for('libros.lista_libros'))


@libros_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_libro(id):
    libro = Libro.query.get_or_404(id)
    autores = Autor.query.all()
    categorias = Categoria.query.all()

    if request.method == 'POST':
        libro.titulo = request.form['titulo']
        libro.autor_id = request.form['autor_id']
        libro.categoria_id = request.form['categoria_id']
        libro.stock = request.form['stock']

        file = request.files.get('imagen')
        if file and allowed_file(file.filename):
            filename = file.filename
            file.save(os.path.join('static/img', filename))
            libro.imagen_url = f'img/{filename}'  # ✅ CORREGIDO

        try:
            db.session.commit()
            flash('Libro actualizado correctamente.', 'success')
            return redirect(url_for('libros.lista_libros'))
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar el libro.', 'danger')
            print(e)

    return render_template('libros/editar.html', libro=libro, autores=autores, categorias=categorias)


@libros_bp.route('/principal')
def principal():
    libros = Libro.query.all()
    prestamos_activos = []

    if current_user.is_authenticated:
        prestamos_activos = Prestamo.query.filter_by(usuario_id=current_user.id_usuario, devuelto=False).all()

    return render_template('index.html', libros=libros, prestamos_activos=prestamos_activos)


@libros_bp.route("/reporte_pdf")
def generar_reporte_pdf():
    file_path = os.path.join('static', 'reportes', 'reporte_prestamos.pdf')
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    doc = SimpleDocTemplate(file_path, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("Reporte de Préstamos de Libros", styles['Title']))
    elements.append(Spacer(1, 12))

    data = [["Usuario", "Libro", "Fecha de Préstamo", "Fecha de Entrega"]]
    morosos = []

    usuarios = Usuario.query.all()
    for usuario in usuarios:
        prestamos = Prestamo.query.filter_by(usuario_id=usuario.id_usuario).all()
        for prestamo in prestamos:
            libro = Libro.query.get(prestamo.libro_id)
            fecha_prestamo = prestamo.fecha_salida.strftime("%d/%m/%Y")
            fecha_entrega = prestamo.fecha_devolucion.strftime("%d/%m/%Y")
            data.append([usuario.nombre, libro.titulo, fecha_prestamo, fecha_entrega])

            if prestamo.fecha_devolucion < datetime.now() and not prestamo.devuelto:
                morosos.append([usuario.nombre, fecha_prestamo, fecha_entrega])

    tabla_prestamos = Table(data, colWidths=[1.5*inch, 2*inch, 1.5*inch, 1.5*inch])
    tabla_prestamos.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    elements.append(tabla_prestamos)
    elements.append(Spacer(1, 24))

    if morosos:
        elements.append(Paragraph("Morosos", styles['Title']))
        data_morosos = [["Nombre del Usuario", "Fecha de Préstamo", "Fecha de Entrega"]]
        data_morosos.extend(morosos)

        tabla_morosos = Table(data_morosos, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
        tabla_morosos.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.red),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        elements.append(tabla_morosos)

    doc.build(elements)
    return send_file(file_path, as_attachment=True)
