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
