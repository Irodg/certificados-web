from database import conectar_db


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
