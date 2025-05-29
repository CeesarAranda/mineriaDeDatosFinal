from flask import Blueprint, render_template, request, redirect, url_for
from models import db, Autor

autores_bp = Blueprint("autores", __name__, template_folder="../templates/autores")

@autores_bp.route("/")
def lista_autores():
    autores = Autor.query.all()
    return render_template("lista.html", autores=autores)

@autores_bp.route("/crear", methods=["GET", "POST"])
def crear_autor():
    if request.method == "POST":
        nuevo = Autor(nombre=request.form["nombre"])
        db.session.add(nuevo)
        db.session.commit()
        return redirect(url_for("autores.lista_autores"))
    return render_template("crear.html")
