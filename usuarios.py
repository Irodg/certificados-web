from database import conectar_db


def criar_tabela_usuarios():
    conn = conectar_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            usuario TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            tipo TEXT NOT NULL DEFAULT 'comum',
            foto TEXT NOT NULL DEFAULT 'default.png'
        )
    """)

    conn.commit()

    cur.execute("""
        SELECT id FROM usuarios
        WHERE usuario = 'admin'
    """)

    admin = cur.fetchone()

    if not admin:
        cur.execute("""
            INSERT INTO usuarios (usuario, senha, tipo, foto)
            VALUES ('admin', '1234', 'admin', 'default.png')
        """)
        conn.commit()

    cur.close()
    conn.close()


def buscar_usuario(usuario):
    conn = conectar_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, usuario, senha, tipo, foto
        FROM usuarios
        WHERE usuario = %s
    """, (usuario,))

    resultado = cur.fetchone()

    cur.close()
    conn.close()

    if not resultado:
        return None

    return {
        "id": resultado[0],
        "usuario": resultado[1],
        "senha": resultado[2],
        "tipo": resultado[3],
        "foto": resultado[4]
    }


def buscar_usuario_por_id(user_id):
    conn = conectar_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, usuario, senha, tipo, foto
        FROM usuarios
        WHERE id = %s
    """, (user_id,))

    resultado = cur.fetchone()

    cur.close()
    conn.close()

    if not resultado:
        return None

    return {
        "id": resultado[0],
        "usuario": resultado[1],
        "senha": resultado[2],
        "tipo": resultado[3],
        "foto": resultado[4]
    }


def listar_usuarios():
    conn = conectar_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, usuario, senha, tipo, foto
        FROM usuarios
        ORDER BY id ASC
    """)

    resultados = cur.fetchall()

    cur.close()
    conn.close()

    return [
        {
            "id": r[0],
            "usuario": r[1],
            "senha": r[2],
            "tipo": r[3],
            "foto": r[4]
        }
        for r in resultados
    ]


def criar_usuario(usuario, senha, tipo):
    conn = conectar_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO usuarios (usuario, senha, tipo, foto)
        VALUES (%s, %s, %s, 'default.png')
    """, (usuario, senha, tipo))

    conn.commit()
    cur.close()
    conn.close()


def alterar_usuario(user_id, novo_usuario):
    conn = conectar_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE usuarios
        SET usuario = %s
        WHERE id = %s
    """, (novo_usuario, user_id))

    conn.commit()
    cur.close()
    conn.close()


def alterar_senha(user_id, nova_senha):
    conn = conectar_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE usuarios
        SET senha = %s
        WHERE id = %s
    """, (nova_senha, user_id))

    conn.commit()
    cur.close()
    conn.close()


def alterar_foto(user_id, foto):
    conn = conectar_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE usuarios
        SET foto = %s
        WHERE id = %s
    """, (foto, user_id))

    conn.commit()
    cur.close()
    conn.close()


def excluir_usuario(user_id):
    conn = conectar_db()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM usuarios
        WHERE id = %s
    """, (user_id,))

    conn.commit()
    cur.close()
    conn.close()
