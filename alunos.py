from database import conectar_db
from datetime import datetime
import cloudinary.uploader

import io
from PIL import Image, ImageOps

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
            numero_matricula TEXT UNIQUE,
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
        "ALTER TABLE alunos ADD COLUMN IF NOT EXISTS data_matricula DATE DEFAULT CURRENT_DATE",
        "ALTER TABLE alunos ADD COLUMN IF NOT EXISTS numero_matricula TEXT UNIQUE"
    ]

    for comando in comandos:
        cur.execute(comando)

    conn.commit()
    cur.close()
    conn.close()


def converter_data_para_banco(data):
    data = (data or "").strip()

    if data == "":
        return None

    try:
        return datetime.strptime(data, "%d/%m/%Y").date()
    except ValueError:
        return None
        
def cpf_aluno_ja_cadastrado(cpf):
    cpf = ''.join(filter(str.isdigit, cpf or ""))

    if cpf == "":
        return False

    conn = conectar_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id
        FROM alunos
        WHERE cpf = %s
        LIMIT 1
    """, (cpf,))

    existe = cur.fetchone() is not None

    cur.close()
    conn.close()

    return existe

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
    foto_url,
    numero_matricula=None,
    data_matricula=None
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
            foto_url,
            numero_matricula,
            data_matricula
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        nome,
        data_nascimento,
        cpf or None,
        cpf_responsavel or None,
        responsavel,
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
        numero_matricula,
        data_matricula
    ))

    aluno_id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return aluno_id


def salvar_aluno_do_formulario(form, files, numero_matricula=None):
    foto = files.get("foto_camera") or files.get("foto_galeria") or files.get("foto")
    foto_url = ""

    cpf = ''.join(filter(str.isdigit, form.get("cpf", "")))

    if cpf_aluno_ja_cadastrado(cpf):
        raise ValueError("JÁ EXISTE UM ALUNO CADASTRADO COM ESTE CPF.")
    
    if foto and foto.filename != "":
        imagem = Image.open(foto)
        imagem = ImageOps.exif_transpose(imagem)
        imagem = imagem.convert("RGB")
        imagem.thumbnail((700, 700))
    
        buffer = io.BytesIO()
        imagem.save(buffer, format="JPEG", quality=60, optimize=True)
        buffer.seek(0)
    
        upload = cloudinary.uploader.upload(
            buffer,
            folder="alunos_crist_oss",
            resource_type="image",
            transformation=[
                {"width": 600, "height": 600, "crop": "fill", "gravity": "face"},
                {"quality": "auto", "fetch_format": "auto"}
            ]
        )
    
        foto_url = upload.get("secure_url", "")

    data_matricula = converter_data_para_banco(form.get("data_matricula", ""))

    if data_matricula is None:
        data_matricula = datetime.now().date()

    return criar_aluno(
        form.get("nome", "").strip().upper(),
        converter_data_para_banco(form.get("data_nascimento", "")),
        cpf,
        form.get("responsavel", "").strip().upper(),
        ''.join(filter(str.isdigit, form.get("cpf_responsavel", ""))),
        form.get("telefone", "").strip(),
        form.get("endereco", "").strip().upper(),
        form.get("faixa", "").strip(),
        form.get("graus", "").strip(),
        form.get("sede", "").strip().upper(),
        form.get("status", "ativo").strip(),
        form.get("motivo_desligamento", "").strip().upper(),
        converter_data_para_banco(form.get("data_desligamento", "")),
        form.get("observacoes", "").strip().upper(),
        foto_url,
        numero_matricula,
        data_matricula
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
            data_matricula,
            numero_matricula
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
    observacoes,
    data_matricula,
    foto_url=None
):
    conn = conectar_db()
    cur = conn.cursor()

    if foto_url:
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
                observacoes = %s,
                data_matricula = %s,
                foto_url = %s
            WHERE id = %s
        """, (
            nome,
            data_nascimento,
            cpf or None,
            responsavel,
            cpf_responsavel or None,
            telefone,
            endereco,
            faixa,
            graus,
            sede,
            status,
            motivo_desligamento,
            data_desligamento,
            observacoes,
            data_matricula,
            foto_url,
            aluno_id
        ))
    else:
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
                observacoes = %s,
                data_matricula = %s
            WHERE id = %s
        """, (
            nome,
            data_nascimento,
            cpf or None,
            responsavel,
            cpf_responsavel or None,
            telefone,
            endereco,
            faixa,
            graus,
            sede,
            status,
            motivo_desligamento,
            data_desligamento,
            observacoes,
            data_matricula,
            aluno_id
        ))

    conn.commit()
    cur.close()
    conn.close()


def excluir_aluno(aluno_id):
    conn = conectar_db()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM alunos
        WHERE id = %s
    """, (aluno_id,))

    conn.commit()
    cur.close()
    conn.close()


def obter_alunos():
    conn = conectar_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,                 -- 0
            nome,               -- 1
            faixa,              -- 2
            graus,              -- 3
            sede,               -- 4
            status,             -- 5
            foto_url,           -- 6
            numero_matricula    -- 7
        FROM alunos
        WHERE status = 'ativo'
        ORDER BY nome
    """)

    alunos = cur.fetchall()

    cur.close()
    conn.close()

    return alunos
