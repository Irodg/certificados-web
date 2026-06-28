from database import conectar_db
import cloudinary.uploader

def criar_tabela_alunos():
    conn = conectar_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS alunos (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            data_nascimento DATE,
            cpf TEXT UNIQUE,
            responsavel TEXT,
            cpf_responsavel TEXT,
            telefone TEXT,
            endereco TEXT,
            faixa TEXT,
            graus TEXT,
            sede TEXT,
            status TEXT DEFAULT 'ativo',
            motivo_desligamento TEXT,
            data_desligamento DATE,
            observacoes TEXT,
            foto_url TEXT,
            data_matricula DATE DEFAULT CURRENT_DATE,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    cur.close()
    conn.close()


def atualizar_tabela_alunos():
    conn = conectar_db()
    cur = conn.cursor()

    comandos = [
        "ALTER TABLE alunos ADD COLUMN IF NOT EXISTS graus TEXT",
        "ALTER TABLE alunos ADD COLUMN IF NOT EXISTS motivo_desligamento TEXT",
        "ALTER TABLE alunos ADD COLUMN IF NOT EXISTS data_desligamento DATE",
        "ALTER TABLE alunos ADD COLUMN IF NOT EXISTS data_matricula DATE DEFAULT CURRENT_DATE"
    ]

    for comando in comandos:
        cur.execute(comando)

    conn.commit()
    cur.close()
    conn.close()


def criar_aluno(
    nome,
    data_nascimento,
    cpf,
    responsavel,
    cpf_responsavel,
    telefone,
    endereco,
    faixa,
    graus,
    sede,
    status,
    motivo_desligamento,
    data_desligamento,
    observacoes,
    foto_url
):
    conn = conectar_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO alunos (
            nome,
            data_nascimento,
            cpf,
            responsavel,
            cpf_responsavel,
            telefone,
            endereco,
            faixa,
            graus,
            sede,
            status,
            motivo_desligamento,
            data_desligamento,
            observacoes,
            foto_url
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        nome,
        data_nascimento or None,
        cpf,
        responsavel,
        cpf_responsavel,
        telefone,
        endereco,
        faixa,
        graus,
        sede,
        status,
        motivo_desligamento,
        data_desligamento or None,
        observacoes,
        foto_url
    ))

    conn.commit()
    cur.close()
    conn.close()


def salvar_aluno_do_formulario(form, files):
    foto = files.get("foto")
    foto_url = ""

    if foto and foto.filename != "":
        upload = cloudinary.uploader.upload(
            foto,
            folder="alunos_crist_oss",
            resource_type="image",
            transformation=[
                {"width": 600, "height": 600, "crop": "fill", "gravity": "face"},
                {"quality": "auto", "fetch_format": "auto"}
            ]
        )
        foto_url = upload.get("secure_url", "")

    criar_aluno(
        form.get("nome", "").strip().upper(),
        form.get("data_nascimento", "").strip(),
        form.get("cpf", "").strip(),
        form.get("responsavel", "").strip().upper(),
        form.get("cpf_responsavel", "").strip(),
        form.get("telefone", "").strip(),
        form.get("endereco", "").strip().upper(),
        form.get("faixa", "").strip(),
        form.get("graus", "").strip(),
        form.get("sede", "").strip().upper(),
        form.get("status", "ativo").strip(),
        form.get("motivo_desligamento", "").strip().upper(),
        form.get("data_desligamento", "").strip(),
        form.get("observacoes", "").strip().upper(),
        foto_url
    )
    
def buscar_aluno_por_id(aluno_id):
    conn = conectar_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            nome,
            data_nascimento,
            cpf,
            responsavel,
            cpf_responsavel,
            telefone,
            endereco,
            faixa,
            graus,
            sede,
            status,
            motivo_desligamento,
            data_desligamento,
            observacoes,
            foto_url,
            data_matricula
        FROM alunos
        WHERE id = %s
    """, (aluno_id,))

    aluno = cur.fetchone()

    cur.close()
    conn.close()

    return aluno
    
def atualizar_aluno(
    aluno_id,
    nome,
    data_nascimento,
    cpf,
    responsavel,
    cpf_responsavel,
    telefone,
    endereco,
    faixa,
    graus,
    sede,
    status,
    motivo_desligamento,
    data_desligamento,
    observacoes
):
    conn = conectar_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE alunos
        SET
            nome = %s,
            data_nascimento = %s,
            cpf = %s,
            responsavel = %s,
            cpf_responsavel = %s,
            telefone = %s,
            endereco = %s,
            faixa = %s,
            graus = %s,
            sede = %s,
            status = %s,
            motivo_desligamento = %s,
            data_desligamento = %s,
            observacoes = %s
        WHERE id = %s
    """, (
        nome,
        data_nascimento or None,
        cpf,
        responsavel,
        cpf_responsavel,
        telefone,
        endereco,
        faixa,
        graus,
        sede,
        status,
        motivo_desligamento,
        data_desligamento or None,
        observacoes,
        aluno_id
    ))

    conn.commit()
    cur.close()
    conn.close()

def obter_alunos():
    conn = conectar_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            nome,
            faixa,
            graus,
            sede,
            status,
            foto_url
        FROM alunos
        ORDER BY nome
    """)

    alunos = cur.fetchall()

    cur.close()
    conn.close()

    return alunos
