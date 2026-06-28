import secrets
import string
from datetime import datetime, timedelta

from database import conectar_db


def criar_tabela_codigos_matricula():
    conn = conectar_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS codigos_matricula (
            id SERIAL PRIMARY KEY,
            codigo TEXT UNIQUE NOT NULL,
            status TEXT NOT NULL DEFAULT 'pendente',
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expira_em TIMESTAMP NOT NULL,
            usado_em TIMESTAMP,
            aluno_id INTEGER,
            criado_por INTEGER
        )
    """)

    conn.commit()
    cur.close()
    conn.close()


def atualizar_tabela_alunos_matricula():
    conn = conectar_db()
    cur = conn.cursor()

    cur.execute("""
        ALTER TABLE alunos
        ADD COLUMN IF NOT EXISTS numero_matricula TEXT UNIQUE
    """)

    conn.commit()
    cur.close()
    conn.close()


def gerar_codigo_matricula(tamanho=8):
    caracteres = string.ascii_uppercase + string.digits

    return "".join(
        secrets.choice(caracteres)
        for _ in range(tamanho)
    )


def criar_codigo_matricula(usuario_id):
    codigo = gerar_codigo_matricula()
    expira_em = datetime.now() + timedelta(hours=24)

    conn = conectar_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO codigos_matricula (
            codigo,
            expira_em,
            criado_por
        )
        VALUES (%s, %s, %s)
        RETURNING codigo, expira_em
    """, (
        codigo,
        expira_em,
        usuario_id
    ))

    resultado = cur.fetchone()

    conn.commit()
    cur.close()
    conn.close()

    return resultado
