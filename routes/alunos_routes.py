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
