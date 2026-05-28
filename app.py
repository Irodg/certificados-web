import os
import io
import uuid
import psycopg2

from flask import (
    Flask,
    render_template,
    request,
    send_file,
    redirect,
    url_for,
    session
)

from werkzeug.utils import secure_filename
from PIL import Image

from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.units import mm


# ======================================================
# APP
# ======================================================

app = Flask(__name__)

app.secret_key = "certificados_secret_key"

# ======================================================
# UPLOADS
# ======================================================

UPLOAD_FOLDER = "static/uploads"

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ======================================================
# DATABASE
# ======================================================

DATABASE_URL = os.environ.get(
    "DATABASE_URL"
)


def conectar_db():

    return psycopg2.connect(
        DATABASE_URL
    )


def criar_tabela_usuarios():

    conn = conectar_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (

            id SERIAL PRIMARY KEY,

            usuario TEXT UNIQUE NOT NULL,

            senha TEXT NOT NULL,

            tipo TEXT NOT NULL DEFAULT 'comum',

            foto TEXT NOT NULL DEFAULT 'default.png'
        )
    """)

    conn.commit()

    # ==============================================
    # CRIA ADMIN AUTOMÁTICO
    # ==============================================

    cur.execute("""
        SELECT * FROM usuarios
        WHERE usuario = 'admin'
    """)

    admin = cur.fetchone()

    if not admin:

        cur.execute("""
            INSERT INTO usuarios (
                usuario,
                senha,
                tipo,
                foto
            )

            VALUES (
                'admin',
                '1234',
                'admin',
                'default.png'
            )
        """)

        conn.commit()

    cur.close()
    conn.close()


criar_tabela_usuarios()

# ======================================================
# USUÁRIOS
# ======================================================

def buscar_usuario(usuario):

    conn = conectar_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            usuario,
            senha,
            tipo,
            foto

        FROM usuarios

        WHERE usuario = %s
    """, (usuario,))

    resultado = cur.fetchone()

    cur.close()
    conn.close()

    if not resultado:
        return None

    return {
        "id": resultado[0],
        "usuario": resultado[1],
        "senha": resultado[2],
        "tipo": resultado[3],
        "foto": resultado[4]
    }


def buscar_usuario_por_id(user_id):

    conn = conectar_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            usuario,
            senha,
            tipo,
            foto

        FROM usuarios

        WHERE id = %s
    """, (user_id,))

    resultado = cur.fetchone()

    cur.close()
    conn.close()

    if not resultado:
        return None

    return {
        "id": resultado[0],
        "usuario": resultado[1],
        "senha": resultado[2],
        "tipo": resultado[3],
        "foto": resultado[4]
    }


def listar_usuarios():

    conn = conectar_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            usuario,
            senha,
            tipo,
            foto

        FROM usuarios

        ORDER BY id ASC
    """)

    resultados = cur.fetchall()

    cur.close()
    conn.close()

    usuarios = []

    for r in resultados:

        usuarios.append({
            "id": r[0],
            "usuario": r[1],
            "senha": r[2],
            "tipo": r[3],
            "foto": r[4]
        })

    return usuarios


def criar_usuario(
    usuario,
    senha,
    tipo="comum"
):

    conn = conectar_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO usuarios (
            usuario,
            senha,
            tipo,
            foto
        )

        VALUES (
            %s,
            %s,
            %s,
            'default.png'
        )
    """, (
        usuario,
        senha,
        tipo
    ))

    conn.commit()

    cur.close()
    conn.close()


def alterar_senha(
    user_id,
    nova_senha
):

    conn = conectar_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE usuarios

        SET senha = %s

        WHERE id = %s
    """, (
        nova_senha,
        user_id
    ))

    conn.commit()

    cur.close()
    conn.close()


def alterar_usuario(
    user_id,
    novo_usuario
):

    conn = conectar_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE usuarios

        SET usuario = %s

        WHERE id = %s
    """, (
        novo_usuario,
        user_id
    ))

    conn.commit()

    cur.close()
    conn.close()


def alterar_foto(
    user_id,
    foto
):

    conn = conectar_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE usuarios

        SET foto = %s

        WHERE id = %s
    """, (
        foto,
        user_id
    ))

    conn.commit()

    cur.close()
    conn.close()


def excluir_usuario(user_id):

    conn = conectar_db()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM usuarios

        WHERE id = %s
    """, (user_id,))

    conn.commit()

    cur.close()
    conn.close()


# ======================================================
# AUTH
# ======================================================

def usuario_logado():
    return session.get("logado") is True


def usuario_admin():
    return session.get("tipo") == "admin"


# ======================================================
# LOGIN
# ======================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        usuario = request.form.get(
            "usuario",
            ""
        ).strip()

        senha = request.form.get(
            "senha",
            ""
        ).strip()

        user = buscar_usuario(usuario)

        if user and user["senha"] == senha:

            session["logado"] = True
            session["usuario"] = user["usuario"]
            session["tipo"] = user["tipo"]
            session["foto"] = user["foto"]
            session["id"] = user["id"]

            return redirect(
                url_for("menu")
            )

        return render_template(
            "login.html",
            erro="USUÁRIO OU SENHA INVÁLIDOS."
        )

    return render_template(
        "login.html"
    )


@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# ======================================================
# MENU
# ======================================================

@app.route("/")
def raiz():

    if not usuario_logado():
        return redirect(
            url_for("login")
        )

    return redirect(
        url_for("menu")
    )


@app.route("/menu")
def menu():

    if not usuario_logado():
        return redirect(
            url_for("login")
        )

    return render_template(
        "menu.html",
        usuario=session.get("usuario"),
        foto=session.get("foto"),
        tipo=session.get("tipo")
    )


# ======================================================
# MINHA CONTA
# ======================================================

@app.route(
    "/minha-conta",
    methods=["GET", "POST"]
)
def minha_conta():

    if not usuario_logado():
        return redirect(
            url_for("login")
        )

    usuario_atual = buscar_usuario_por_id(
        session["id"]
    )

    mensagem = None
    erro = None

    if request.method == "POST":

        novo_usuario = request.form.get(
            "novo_usuario",
            ""
        ).strip()

        nova_senha = request.form.get(
            "nova_senha",
            ""
        ).strip()

        foto = request.files.get("foto")

        # ==============================================
        # ALTERAR FOTO
        # ==============================================

        if foto and foto.filename != "":

            extensao = foto.filename.split(".")[-1]

            nome_arquivo = (
                str(uuid.uuid4())
                + ".jpg"
            )

            caminho = os.path.join(
                app.config["UPLOAD_FOLDER"],
                secure_filename(nome_arquivo)
            )

            imagem = Image.open(foto)

            imagem = imagem.convert("RGB")

            imagem.thumbnail((600, 600))

            imagem.save(
                caminho,
                format="JPEG",
                quality=75,
                optimize=True
            )

            alterar_foto(
                usuario_atual["id"],
                nome_arquivo
            )

            session["foto"] = nome_arquivo

        # ==============================================
        # ALTERAR LOGIN
        # ==============================================

        if novo_usuario != "":

            existente = buscar_usuario(
                novo_usuario
            )

            if (
                existente
                and
                existente["id"] != usuario_atual["id"]
            ):

                erro = (
                    "USUÁRIO JÁ EXISTE."
                )

            else:

                alterar_usuario(
                    usuario_atual["id"],
                    novo_usuario
                )

                session["usuario"] = novo_usuario

        # ==============================================
        # ALTERAR SENHA
        # ==============================================

        if not erro and nova_senha != "":

            alterar_senha(
                usuario_atual["id"],
                nova_senha
            )

        if not erro:

            mensagem = (
                "CONTA ATUALIZADA."
            )

            usuario_atual = buscar_usuario_por_id(
                session["id"]
            )

    return render_template(
        "minha_conta.html",
        usuario=usuario_atual,
        mensagem=mensagem,
        erro=erro
    )
