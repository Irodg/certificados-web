import io
from PIL import Image, ImageOps

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

@admin_bp.route("/minha-conta", methods=["GET", "POST"])
def minha_conta():
    if not usuario_logado():
        return redirect(url_for("login.login"))

    usuario_atual = buscar_usuario_por_id(session["id"])

    mensagem = None
    erro = None

    if request.method == "POST":
        novo_usuario = request.form.get("novo_usuario", "").strip()
        nova_senha = request.form.get("nova_senha", "").strip()
        foto = request.files.get("foto_camera") or request.files.get("foto_galeria")

        if novo_usuario != "":
            existente = buscar_usuario(novo_usuario)

            if existente and existente["id"] != usuario_atual["id"]:
                erro = "USUÁRIO JÁ EXISTE."
            else:
                alterar_usuario(usuario_atual["id"], novo_usuario)
                session["usuario"] = novo_usuario

        if not erro and nova_senha != "":
            alterar_senha(usuario_atual["id"], nova_senha)

        if not erro and foto and foto.filename != "":
            imagem = Image.open(foto)
            imagem = ImageOps.exif_transpose(imagem)
            imagem = imagem.convert("RGB")
            imagem.thumbnail((900, 900))
        
            buffer = io.BytesIO()
            imagem.save(buffer, format="JPEG", quality=75, optimize=True)
            buffer.seek(0)
        
            upload = cloudinary.uploader.upload(
                buffer,
                folder="usuarios_crist_oss",
                resource_type="image",
                transformation=[
                    {"width": 600, "height": 600, "crop": "fill", "gravity": "face"},
                    {"quality": "auto", "fetch_format": "auto"}
                ]
            )

            foto_url = upload.get("secure_url", "")

            alterar_foto(usuario_atual["id"], foto_url)
            session["foto"] = foto_url

        if not erro:
            mensagem = "CONTA ATUALIZADA COM SUCESSO."
            usuario_atual = buscar_usuario_por_id(session["id"])

    return render_template(
        "minha_conta.html",
        usuario=usuario_atual,
        mensagem=mensagem,
        erro=erro
    )


@admin_bp.route("/admin", methods=["GET", "POST"])
def admin():
    if not usuario_logado():
        return redirect(url_for("login.login"))

    if not usuario_admin():
        return redirect(url_for("login.menu"))

    mensagem = None
    erro = None

    if request.method == "POST":
        acao = request.form.get("acao")

        if acao == "criar":
            novo_usuario = request.form.get("novo_usuario", "").strip()
            nova_senha = request.form.get("nova_senha", "").strip()
            tipo = request.form.get("tipo", "comum").strip()

            if novo_usuario == "" or nova_senha == "":
                erro = "PREENCHA USUÁRIO E SENHA."
            elif buscar_usuario(novo_usuario):
                erro = "ESSE USUÁRIO JÁ EXISTE."
            else:
                criar_usuario(novo_usuario, nova_senha, tipo)
                mensagem = "USUÁRIO CRIADO COM SUCESSO."

        elif acao == "alterar_senha":
            usuario_id = int(request.form.get("usuario_id"))
            nova_senha = request.form.get("nova_senha", "").strip()

            if nova_senha == "":
                erro = "DIGITE A NOVA SENHA."
            else:
                alterar_senha(usuario_id, nova_senha)
                mensagem = "SENHA ALTERADA COM SUCESSO."

        elif acao == "excluir":
            usuario_id = int(request.form.get("usuario_id"))

            if usuario_id == session["id"]:
                erro = "VOCÊ NÃO PODE EXCLUIR SUA PRÓPRIA CONTA."
            else:
                excluir_usuario(usuario_id)
                mensagem = "USUÁRIO EXCLUÍDO COM SUCESSO."

    return render_template(
        "admin.html",
        usuarios=listar_usuarios(),
        mensagem=mensagem,
        erro=erro
    )
