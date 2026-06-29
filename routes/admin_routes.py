from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session
)

import cloudinary.uploader

from services.auth import usuario_logado, usuario_admin

from usuarios import (
    buscar_usuario,
    buscar_usuario_por_id,
    listar_usuarios,
    criar_usuario,
    alterar_usuario,
    alterar_senha,
    alterar_foto,
    excluir_usuario
)

admin_bp = Blueprint("admin", __name__)
