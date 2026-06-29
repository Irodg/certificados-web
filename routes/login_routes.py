from flask import Blueprint, render_template, request, redirect, url_for, session

from usuarios import buscar_usuario


login_bp = Blueprint("login", __name__)


from services.auth import usuario_logado


@login_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        senha = request.form.get("senha", "").strip()

        user = buscar_usuario(usuario)

        if user and user["senha"] == senha:
            session["logado"] = True
            session["usuario"] = user["usuario"]
            session["tipo"] = user["tipo"]
            session["foto"] = user["foto"]
            session["id"] = user["id"]

            return redirect(url_for("login.menu"))

        return render_template(
            "login.html",
            erro="USUÁRIO OU SENHA INVÁLIDOS."
        )

    return render_template("login.html")


@login_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login.login"))


@login_bp.route("/")
def raiz():
    if not usuario_logado():
        return redirect(url_for("login.login"))

    return redirect(url_for("login.menu"))


@login_bp.route("/menu")
def menu():
    if not usuario_logado():
        return redirect(url_for("login.login"))

    return render_template(
        "menu.html",
        usuario=session.get("usuario"),
        foto=session.get("foto"),
        tipo=session.get("tipo")
    )
