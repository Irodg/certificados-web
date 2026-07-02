from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from datetime import date

from services.auth import usuario_logado
from alunos import obter_alunos
from presencas import (
    obter_ou_criar_treino_do_dia,
    salvar_presencas_standby,
    lancar_presenca_no_historico,
    listar_treinos,
    listar_presentes_do_treino,
    buscar_treino_por_id,
    listar_ids_presentes_do_treino
)


presencas_bp = Blueprint("presencas", __name__)


@presencas_bp.route("/presencas", methods=["GET", "POST"])
def presencas():
    if not usuario_logado():
        return redirect(url_for("login.login"))

    hoje = date.today()

    if hoje.weekday() not in [0, 2, 4]:
        return render_template(
            "presencas.html",
            treino_id=None,
            data_treino=hoje,
            alunos=[],
            presentes_ids=[],
            treinos=listar_treinos(),
            erro="HOJE NÃO É DIA DE TREINO. AS AULAS SÃO SEGUNDA, QUARTA E SEXTA."
        )

    treino_id = obter_ou_criar_treino_do_dia(hoje)
    alunos = obter_alunos()
    presentes_ids = listar_ids_presentes_do_treino(treino_id)

    if request.method == "POST":
        acao = request.form.get("acao")
        alunos_presentes = request.form.getlist("alunos_presentes")

        try:
            salvar_presencas_standby(treino_id, alunos_presentes)

            if acao == "lancar":
                lancar_presenca_no_historico(treino_id)

        except ValueError as erro:
            return render_template(
                "presencas.html",
                treino_id=treino_id,
                data_treino=hoje,
                alunos=alunos,
                presentes_ids=presentes_ids,
                treinos=listar_treinos(),
                erro=str(erro)
            )

        return redirect(url_for("presencas.presencas"))

    return render_template(
        "presencas.html",
        treino_id=treino_id,
        data_treino=hoje,
        alunos=alunos,
        presentes_ids=presentes_ids,
        erro=None
    )
@presencas_bp.route("/presencas/autosave", methods=["POST"])
def autosave_presencas():
    if not usuario_logado():
        return jsonify({
            "ok": False,
            "erro": "USUÁRIO NÃO LOGADO."
        }), 401

    treino_id = request.form.get("treino_id")
    alunos_presentes = request.form.getlist("alunos_presentes")

    if not treino_id:
        return jsonify({
            "ok": False,
            "erro": "TREINO NÃO INFORMADO."
        }), 400

    try:
        salvar_presencas_standby(treino_id, alunos_presentes)
    except ValueError as erro:
        return jsonify({
            "ok": False,
            "erro": str(erro)
        }), 400

    return jsonify({
        "ok": True,
        "mensagem": "PRESENÇA SALVA EM STANDBY."
    })

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
