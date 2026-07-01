from flask import Blueprint, render_template, request, redirect, url_for
from datetime import date

from services.auth import usuario_logado
from alunos import obter_alunos
from presencas import (
    obter_ou_criar_treino_do_dia,
    salvar_presencas,
    listar_treinos,
    listar_presentes_do_treino,
    buscar_treino_por_id
)


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

@presencas_bp.route("/presencas/historico")
def historico_presencas():
    if not usuario_logado():
        return redirect(url_for("login.login"))

    treinos = listar_treinos()

    return render_template(
        "historico_presencas.html",
        treinos=treinos
    )


@presencas_bp.route("/presencas/<int:treino_id>")
def ver_presenca(treino_id):
    if not usuario_logado():
        return redirect(url_for("login.login"))

    treino = buscar_treino_por_id(treino_id)

    if not treino:
        return "Treino não encontrado.", 404

    presentes = listar_presentes_do_treino(treino_id)

    return render_template(
        "ver_presenca.html",
        treino=treino,
        presentes=presentes
    )
