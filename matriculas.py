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
            criado_por INTEGER,
            whatsapp_destino TEXT
        )
    """)

    conn.commit()
    cur.close()
    conn.close()
    
def atualizar_tabela_codigos_matricula():
    conn = conectar_db()
    cur = conn.cursor()

    cur.execute("""
        ALTER TABLE codigos_matricula
        ADD COLUMN IF NOT EXISTS whatsapp_destino TEXT
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

def validar_codigo_matricula(codigo):
    conn = conectar_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, codigo, status, expira_em
        FROM codigos_matricula
        WHERE codigo = %s
    """, (codigo,))

    resultado = cur.fetchone()

    cur.close()
    conn.close()

    if not resultado:
        return False, "CÓDIGO INVÁLIDO."

    codigo_id, codigo, status, expira_em = resultado

    if status != "pendente":
        return False, "CÓDIGO JÁ UTILIZADO OU CANCELADO."

    if datetime.now() > expira_em:
        return False, "CÓDIGO EXPIRADO. SOLICITE UM NOVO CÓDIGO."

    return True, codigo
    
def criar_codigo_matricula(usuario_id, whatsapp_destino=None):
    expira_em = datetime.now() + timedelta(hours=24)

    conn = conectar_db()
    cur = conn.cursor()

    while True:
        codigo = gerar_codigo_matricula()

        cur.execute("""
            SELECT id FROM codigos_matricula
            WHERE codigo = %s
        """, (codigo,))

        existente = cur.fetchone()

        if not existente:
            break

    cur.execute("""
        INSERT INTO codigos_matricula (
            codigo,
            expira_em,
            criado_por,
            whatsapp_destino
        )
        VALUES (%s, %s, %s, %s)
        RETURNING codigo, expira_em
    """, (
        codigo,
        expira_em,
        usuario_id,
        whatsapp_destino
    ))

    resultado = cur.fetchone()

    conn.commit()
    cur.close()
    conn.close()

    return resultado
    
def marcar_codigo_como_usado(codigo, aluno_id):
    conn = conectar_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE codigos_matricula
        SET
            status = 'usado',
            usado_em = CURRENT_TIMESTAMP,
            aluno_id = %s
        WHERE codigo = %s
    """, (aluno_id, codigo))

    conn.commit()
    cur.close()
    conn.close()
    
def listar_codigos_por_status(status):
    conn = conectar_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            c.codigo,
            c.status,
            c.criado_em,
            c.expira_em,
            c.usado_em,
            a.nome,
            c.whatsapp_destino
        FROM codigos_matricula c
        LEFT JOIN alunos a ON a.id = c.aluno_id
        WHERE c.status = %s
        ORDER BY c.usado_em DESC NULLS LAST, c.criado_em DESC
    """, (status,))

    codigos = cur.fetchall()

    cur.close()
    conn.close()

    return codigos

def atualizar_codigos_expirados():
    conn = conectar_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE codigos_matricula
        SET status = 'expirado'
        WHERE status = 'pendente'
        AND expira_em < CURRENT_TIMESTAMP
    """)

    conn.commit()
    cur.close()
    conn.close()
