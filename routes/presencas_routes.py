from flask import Blueprint, render_template, request, redirect, url_for
from datetime import date

from services.auth import usuario_logado
from alunos import obter_alunos
from presencas import obter_ou_criar_treino_do_dia, salvar_presencas


presencas_bp = Blueprint("presencas", __name__)


@presencas_bp.route("/presencas", methods=["GET", "POST"])
def presencas():
    if not usuario_logado():
        return redirect(url_for("login.login"))

    hoje = date.today()
    treino_id = obter_ou_criar_treino_do_dia(hoje)
    alunos = obter_alunos()

    if request.method == "POST":
        alunos_presentes = request.form.getlist("alunos_presentes")
        salvar_presencas(treino_id, alunos_presentes)
        return redirect(url_for("presencas.presencas"))

    return render_template(
        "presencas.html",
        treino_id=treino_id,
        data_treino=hoje,
        alunos=alunos
    )
