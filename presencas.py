from database import conectar_db
from datetime import datetime


def criar_tabela_presencas():
    conn = conectar_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS presencas_treino (
            id SERIAL PRIMARY KEY,
            data_treino DATE NOT NULL UNIQUE,
            dia_semana TEXT,
            horario TEXT DEFAULT '18:00',
            status TEXT DEFAULT 'standby',
            lancado_em TIMESTAMP,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS presencas_alunos (
            id SERIAL PRIMARY KEY,
            treino_id INTEGER REFERENCES presencas_treino(id) ON DELETE CASCADE,
            aluno_id INTEGER REFERENCES alunos(id) ON DELETE CASCADE,
            presente BOOLEAN DEFAULT TRUE,
            registrado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(treino_id, aluno_id)
        )
    """)

    conn.commit()
    cur.close()
    conn.close()

def atualizar_tabela_presencas():
    conn = conectar_db()
    cur = conn.cursor()

    comandos = [
        "ALTER TABLE presencas_treino ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'standby'",
        "ALTER TABLE presencas_treino ADD COLUMN IF NOT EXISTS lancado_em TIMESTAMP"
    ]

    for comando in comandos:
        cur.execute(comando)

    conn.commit()
    cur.close()
    conn.close()


def obter_ou_criar_treino_do_dia(data_treino):
    conn = conectar_db()
    cur = conn.cursor()

    dias = {
        0: "SEGUNDA",
        1: "TERÇA",
        2: "QUARTA",
        3: "QUINTA",
        4: "SEXTA",
        5: "SÁBADO",
        6: "DOMINGO"
    }

    dia_semana = dias[data_treino.weekday()]

    cur.execute("""
        SELECT id FROM presencas_treino
        WHERE data_treino = %s
    """, (data_treino,))

    treino = cur.fetchone()

    if treino:
        treino_id = treino[0]
    else:
        cur.execute("""
            INSERT INTO presencas_treino (
                data_treino,
                dia_semana
            )
            VALUES (%s, %s)
            RETURNING id
        """, (data_treino, dia_semana))

        treino_id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return treino_id

def salvar_presencas(treino_id, alunos_presentes):
    conn = conectar_db()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM presencas_alunos
        WHERE treino_id = %s
    """, (treino_id,))

    for aluno_id in alunos_presentes:
        cur.execute("""
            INSERT INTO presencas_alunos (
                treino_id,
                aluno_id,
                presente
            )
            VALUES (%s, %s, TRUE)
        """, (treino_id, aluno_id))

    conn.commit()
    cur.close()
    conn.close()

def listar_treinos():
    conn = conectar_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            t.id,
            t.data_treino,
            t.dia_semana,
            t.horario,
            COUNT(pa.id) AS total_presentes
        FROM presencas_treino t
        LEFT JOIN presencas_alunos pa ON pa.treino_id = t.id
        GROUP BY t.id
        ORDER BY t.data_treino DESC
    """)

    treinos = cur.fetchall()

    cur.close()
    conn.close()

    return treinos


def listar_presentes_do_treino(treino_id):
    conn = conectar_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            a.id,
            a.nome,
            a.faixa,
            a.graus,
            a.sede,
            a.foto_url
        FROM presencas_alunos pa
        JOIN alunos a ON a.id = pa.aluno_id
        WHERE pa.treino_id = %s
        ORDER BY a.nome
    """, (treino_id,))

    presentes = cur.fetchall()

    cur.close()
    conn.close()

    return presentes


def buscar_treino_por_id(treino_id):
    conn = conectar_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            data_treino,
            dia_semana,
            horario
        FROM presencas_treino
        WHERE id = %s
    """, (treino_id,))

    treino = cur.fetchone()

    cur.close()
    conn.close()

    return treino
