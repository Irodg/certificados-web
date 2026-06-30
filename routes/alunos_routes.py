import io
import cloudinary.uploader
from PIL import Image, ImageOps

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for
)

from services.auth import usuario_logado

from alunos import (
    obter_alunos,
    salvar_aluno_do_formulario,
    buscar_aluno_por_id,
    atualizar_aluno,
    excluir_aluno,
    converter_data_para_banco
)

from usuarios import buscar_usuario_por_id

from matriculas import (
    criar_codigo_matricula,
    marcar_codigo_como_usado
)


alunos_bp = Blueprint("alunos", __name__)

@alunos_bp.route("/alunos")
def alunos():
    if not usuario_logado():
        return redirect(url_for("login.login"))

    return render_template("alunos.html")


@alunos_bp.route("/alunos/novo", methods=["GET", "POST"])
def novo_aluno():
    if not usuario_logado():
        return redirect(url_for("login.login"))

    faixas = [
        "cinza/branca", "cinza", "cinza/preta",
        "amarela/branca", "amarela", "amarela/preta",
        "laranja/branca", "laranja", "laranja/preta",
        "verde/branca", "verde", "verde/preta",
        "azul", "roxa", "marrom", "preta"
    ]

    if request.method == "POST":
        codigo, expira_em = criar_codigo_matricula(None)

        try:
            aluno_id = salvar_aluno_do_formulario(
                request.form,
                request.files,
                numero_matricula=codigo
            )
        except ValueError as erro:
            return render_template(
                "aluno_form.html",
                aluno=None,
                faixas=faixas,
                editando=False,
                erro=str(erro)
            )

        marcar_codigo_como_usado(codigo, aluno_id)

        return redirect(url_for("alunos.ver_aluno", aluno_id=aluno_id))

    return render_template(
        "aluno_form.html",
        aluno=None,
        faixas=faixas,
        editando=False
    )


@alunos_bp.route("/alunos/listar")
def listar_alunos():
    if not usuario_logado():
        return redirect(url_for("login.login"))

    alunos = obter_alunos()

    return render_template(
        "listar_alunos.html",
        alunos=alunos
    )


@alunos_bp.route("/alunos/buscar")
def buscar_aluno():
    if not usuario_logado():
        return redirect(url_for("login.login"))

    return "<h2>Busca de alunos em construção</h2>"


@alunos_bp.route("/alunos/<int:aluno_id>")
def ver_aluno(aluno_id):
    if not usuario_logado():
        return redirect(url_for("login.login"))

    aluno = buscar_aluno_por_id(aluno_id)

    if not aluno:
        return "Aluno não encontrado.", 404

    return render_template(
        "ver_aluno.html",
        aluno=aluno
    )


@alunos_bp.route("/alunos/<int:aluno_id>/editar", methods=["GET", "POST"])
def editar_aluno(aluno_id):
    if not usuario_logado():
        return redirect(url_for("login.login"))

    faixas = [
        "cinza/branca", "cinza", "cinza/preta",
        "amarela/branca", "amarela", "amarela/preta",
        "laranja/branca", "laranja", "laranja/preta",
        "verde/branca", "verde", "verde/preta",
        "azul", "roxa", "marrom", "preta"
    ]

    aluno = buscar_aluno_por_id(aluno_id)

    if not aluno:
        return "Aluno não encontrado.", 404

    if request.method == "POST":
        foto = (
            request.files.get("foto_camera")
            or request.files.get("foto_galeria")
        )

        foto_url = None

        if foto and foto.filename != "":
            imagem = Image.open(foto)
            imagem = ImageOps.exif_transpose(imagem)
            imagem = imagem.convert("RGB")
            imagem.thumbnail((900, 900))

            buffer = io.BytesIO()
            imagem.save(buffer, format="JPEG", quality=75, optimize=True)
            buffer.seek(0)

            upload = cloudinary.uploader.upload(
                buffer,
                folder="alunos_crist_oss",
                resource_type="image",
                transformation=[
                    {"width": 600, "height": 600, "crop": "fill", "gravity": "face"},
                    {"quality": "auto", "fetch_format": "auto"}
                ]
            )

            foto_url = upload.get("secure_url", "")

        atualizar_aluno(
            aluno_id,
            request.form.get("nome", "").strip().upper(),
            converter_data_para_banco(request.form.get("data_nascimento", "")),
            ''.join(filter(str.isdigit, request.form.get("cpf", ""))),
            request.form.get("responsavel", "").strip().upper(),
            ''.join(filter(str.isdigit, request.form.get("cpf_responsavel", ""))),
            request.form.get("telefone", "").strip(),
            request.form.get("endereco", "").strip().upper(),
            request.form.get("faixa", "").strip(),
            request.form.get("graus", "").strip(),
            request.form.get("sede", "").strip().upper(),
            request.form.get("status", "ativo").strip(),
            request.form.get("motivo_desligamento", "").strip().upper(),
            converter_data_para_banco(request.form.get("data_desligamento", "")),
            request.form.get("observacoes", "").strip().upper(),
            converter_data_para_banco(request.form.get("data_matricula", "")),
            foto_url
        )

        return redirect(url_for("alunos.ver_aluno", aluno_id=aluno_id))

    return render_template(
        "aluno_form.html",
        aluno=aluno,
        faixas=faixas,
        editando=True
    )


@alunos_bp.route("/alunos/<int:aluno_id>/excluir", methods=["POST"])
def excluir_aluno_rota(aluno_id):
    if not usuario_logado():
        return redirect(url_for("login.login"))

    from flask import session

    senha = request.form.get("senha", "").strip()
    usuario_atual = buscar_usuario_por_id(session["id"])

    if not usuario_atual or usuario_atual["senha"] != senha:
        return "Senha incorreta. Exclusão cancelada.", 403

    aluno = buscar_aluno_por_id(aluno_id)

    if not aluno:
        return "Aluno não encontrado.", 404

    excluir_aluno(aluno_id)

    return redirect(url_for("alunos.listar_alunos"))


@alunos_bp.route("/alunos/<int:aluno_id>/ficha")
def ficha_aluno(aluno_id):
    if not usuario_logado():
        return redirect(url_for("login.login"))

    aluno = buscar_aluno_por_id(aluno_id)

    if not aluno:
        return "Aluno não encontrado.", 404

    return render_template(
        "ficha_aluno.html",
        aluno=aluno
    )
