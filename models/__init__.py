
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .libros import Libro
from .autores import Autor
from .categorias import Categoria
from .usuarios import Usuario
from .prestamo import Prestamo