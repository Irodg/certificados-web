import os
import io
import re
import uuid
import psycopg2

from flask import Flask, render_template, request, send_file, redirect, url_for, session
from werkzeug.utils import secure_filename
from PIL import Image

from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.units import mm


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "certificados_secret_key")
app.config["SESSION_PERMANENT"] = False

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

DATABASE_URL = os.environ.get("DATABASE_URL")

FUNDOS_OTIMIZADOS = {}


# ======================================================
# DATABASE
# ======================================================

def conectar_db():
    return psycopg2.connect(
        DATABASE_URL,
        sslmode="require"
    )


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


criar_tabela_usuarios()
criar_tabela_alunos()
atualizar_tabela_alunos()


# ======================================================
# CONFIG
# ======================================================

faixas = [
    "cinza/branca", "cinza", "cinza/preta",
    "amarela/branca", "amarela", "amarela/preta",
    "laranja/branca", "laranja", "laranja/preta",
    "verde/branca", "verde", "verde/preta",
    "azul", "roxa", "marrom", "preta"
]

fundos_por_faixa = {
    "cinza/branca": "fundo_cinza_branca.png",
    "cinza": "fundo_cinza.png",
    "cinza/preta": "fundo_cinza_preta.png",
    "amarela/branca": "fundo_amarela_branca.png",
    "amarela": "fundo_amarela.png",
    "amarela/preta": "fundo_amarela_preta.png",
    "laranja/branca": "fundo_laranja_branca.png",
    "laranja": "fundo_laranja.png",
    "laranja/preta": "fundo_laranja_preta.png",
    "verde/branca": "fundo_verde_branca.png",
    "verde": "fundo_verde.png",
    "verde/preta": "fundo_verde_preta.png",
    "azul": "fundo_azul.png",
    "roxa": "fundo_roxa.png",
    "marrom": "fundo_marrom.png",
    "preta": "fundo_preta.png"
}

dias = [str(i).zfill(2) for i in range(1, 32)]

meses = [
    "Janeiro", "Fevereiro", "Março", "Abril",
    "Maio", "Junho", "Julho", "Agosto",
    "Setembro", "Outubro", "Novembro", "Dezembro"
]

anos = [str(i) for i in range(2026, 2036)]

FONTE_TITULO = "Helvetica-Bold"
FONTE_TEXTO = "Helvetica"


# ======================================================
# FUNÇÕES GERAIS
# ======================================================

def usuario_logado():
    return session.get("logado") is True


def usuario_admin():
    return session.get("tipo") == "admin"


def nome_valido(nome):
    return len(nome.strip().split()) >= 2


def texto_centralizado(pdf, texto, x, y, fonte, tamanho):
    pdf.setFont(fonte, tamanho)
    pdf.drawCentredString(x, y, texto)


def tamanho_fonte_dinamico(texto, fonte, tamanho_maximo, largura_maxima):
    tamanho = tamanho_maximo

    while tamanho > 10:
        largura_texto = pdfmetrics.stringWidth(texto, fonte, tamanho)

        if largura_texto <= largura_maxima:
            return tamanho

        tamanho -= 1

    return tamanho


def quebrar_nome_por_largura(nome, fonte, tamanho, largura_quebra):
    if pdfmetrics.stringWidth(nome, fonte, tamanho) <= largura_quebra:
        return [nome]

    palavras = nome.split()
    melhor_linha_1 = ""
    melhor_linha_2 = ""
    menor_diferenca = None

    for i in range(1, len(palavras)):
        linha_1 = " ".join(palavras[:i])
        linha_2 = " ".join(palavras[i:])

        largura_1 = pdfmetrics.stringWidth(linha_1, fonte, tamanho)
        largura_2 = pdfmetrics.stringWidth(linha_2, fonte, tamanho)

        diferenca = abs(largura_1 - largura_2)

        if menor_diferenca is None or diferenca < menor_diferenca:
            menor_diferenca = diferenca
            melhor_linha_1 = linha_1
            melhor_linha_2 = linha_2

    return [melhor_linha_1, melhor_linha_2]


def desenhar_nome_dinamico(
    pdf,
    nome,
    centro_x,
    y_nome,
    fonte,
    tamanho_maximo,
    largura_maxima,
    largura_quebra
):
    tamanho_nome = tamanho_fonte_dinamico(
        nome,
        fonte,
        tamanho_maximo,
        largura_maxima
    )

    nome_linhas = quebrar_nome_por_largura(
        nome,
        fonte,
        tamanho_nome,
        largura_quebra
    )

    if len(nome_linhas) == 2:
        maior_linha = max(
            nome_linhas,
            key=lambda linha: pdfmetrics.stringWidth(
                linha,
                fonte,
                tamanho_nome
            )
        )

        tamanho_nome = tamanho_fonte_dinamico(
            maior_linha,
            fonte,
            tamanho_maximo,
            largura_maxima
        )

        espacamento_linha = 8 * mm

        texto_centralizado(
            pdf,
            nome_linhas[0],
            centro_x,
            y_nome + (espacamento_linha / 2),
            fonte,
            tamanho_nome
        )

        texto_centralizado(
            pdf,
            nome_linhas[1],
            centro_x,
            y_nome - (espacamento_linha / 2),
            fonte,
            tamanho_nome
        )

    else:
        texto_centralizado(
            pdf,
            nome_linhas[0],
            centro_x,
            y_nome,
            fonte,
            tamanho_nome
        )


def desenhar_faixa_dinamica(
    pdf,
    texto_faixa,
    centro_x,
    y_faixa,
    fonte,
    tamanho_maximo,
    largura_maxima
):
    tamanho_faixa = tamanho_fonte_dinamico(
        texto_faixa,
        fonte,
        tamanho_maximo,
        largura_maxima
    )

    texto_centralizado(
        pdf,
        texto_faixa,
        centro_x,
        y_faixa,
        fonte,
        tamanho_faixa
    )


def quebrar_texto(texto, fonte, tamanho, largura_maxima):
    palavras = texto.split()
    linhas = []
    linha_atual = ""

    for palavra in palavras:
        teste = palavra if linha_atual == "" else linha_atual + " " + palavra

        if pdfmetrics.stringWidth(teste, fonte, tamanho) <= largura_maxima:
            linha_atual = teste
        else:
            linhas.append(linha_atual)
            linha_atual = palavra

    if linha_atual:
        linhas.append(linha_atual)

    return linhas


def desenhar_paragrafo(
    pdf,
    texto,
    x,
    y,
    largura_maxima,
    fonte,
    tamanho,
    entrelinha
):
    pdf.setFont(fonte, tamanho)

    linhas = quebrar_texto(
        texto,
        fonte,
        tamanho,
        largura_maxima
    )

    for i, linha in enumerate(linhas):
        if i == len(linhas) - 1:
            pdf.drawString(x, y, linha)
        else:
            palavras_linha = linha.split()

            if len(palavras_linha) == 1:
                pdf.drawString(x, y, linha)
            else:
                largura_sem_espacos = sum(
                    pdfmetrics.stringWidth(palavra, fonte, tamanho)
                    for palavra in palavras_linha
                )

                quantidade_espacos = len(palavras_linha) - 1
                largura_total_espacos = largura_maxima - largura_sem_espacos
                espaco_extra = largura_total_espacos / quantidade_espacos

                x_atual = x

                for palavra in palavras_linha:
                    pdf.drawString(x_atual, y, palavra)

                    largura_palavra = pdfmetrics.stringWidth(
                        palavra,
                        fonte,
                        tamanho
                    )

                    x_atual += largura_palavra + espaco_extra

        y -= entrelinha

    return y


def criar_logo_transparente(caminho_logo, opacidade=0.10):
    imagem = Image.open(caminho_logo).convert("RGBA")

    alpha = imagem.getchannel("A")
    alpha = alpha.point(lambda p: int(p * opacidade))
    imagem.putalpha(alpha)

    buffer = io.BytesIO()
    imagem.save(buffer, format="PNG")
    buffer.seek(0)

    return ImageReader(buffer)


# ======================================================
# SEDE / FUNDO
# ======================================================

def normalizar_texto(texto):
    texto = texto.strip().lower()

    trocas = {
        "á": "a", "à": "a", "ã": "a", "â": "a",
        "é": "e", "ê": "e",
        "í": "i",
        "ó": "o", "ô": "o", "õ": "o",
        "ú": "u",
        "ç": "c"
    }

    for original, novo in trocas.items():
        texto = texto.replace(original, novo)

    texto = re.sub(r"[^a-z0-9\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()


def identificar_sede(sede_digitada):
    sede_normalizada = normalizar_texto(sede_digitada)

    if sede_normalizada == "":
        return None

    aliases_baturite = [
        "baturite",
        "baturit",
        "batturtite",
        "batturite",
        "baturrite",
        "baturyte",
        "btrt"
    ]

    for alias in aliases_baturite:
        if alias in sede_normalizada:
            return "baturite"

    return None


def prefixo_sede(sede_digitada):
    sede = identificar_sede(sede_digitada)

    prefixos = {
        "baturite": "btrt"
    }

    return prefixos.get(sede)


def obter_fundo_por_faixa_e_sede(faixa, sede=""):
    prefixo = prefixo_sede(sede)
    nome_faixa = faixa.replace("/", "_")

    if prefixo:
        arquivo_sede = f"{prefixo}_{nome_faixa}.png"
        caminho_sede = os.path.join(app.root_path, "fundos", arquivo_sede)

        if os.path.exists(caminho_sede):
            return arquivo_sede

    return fundos_por_faixa.get(faixa)


# ======================================================
# FUNDO OTIMIZADO
# ======================================================

def obter_fundo_otimizado(caminho_fundo):
    if caminho_fundo in FUNDOS_OTIMIZADOS:
        return FUNDOS_OTIMIZADOS[caminho_fundo]

    imagem = Image.open(caminho_fundo).convert("RGB")

    imagem.thumbnail(
        (2200, 1600),
        Image.Resampling.LANCZOS
    )

    buffer = io.BytesIO()

    imagem.save(
        buffer,
        format="JPEG",
        quality=86,
        optimize=True
    )

    buffer.seek(0)

    fundo = ImageReader(buffer)

    FUNDOS_OTIMIZADOS[caminho_fundo] = fundo

    return fundo


# ======================================================
# CERTIFICADO
# ======================================================

def desenhar_certificado_na_pagina(pdf, nome, faixa, dia, mes, ano, sede=""):
    nome = nome.strip().upper()
    data_certificado = f"{dia} de {mes} de {ano}"
    cor_da_faixa = f"FAIXA {faixa.upper()}"

    largura, altura = landscape(A4)
    centro_x = largura / 2

    nome_fundo = obter_fundo_por_faixa_e_sede(faixa, sede)

    if nome_fundo:
        caminho_fundo = os.path.join(app.root_path, "fundos", nome_fundo)

        if os.path.exists(caminho_fundo):
            fundo = obter_fundo_otimizado(caminho_fundo)

            pdf.drawImage(
                fundo,
                0,
                0,
                width=largura,
                height=altura
            )

    topo_bloco = altura - (30 * mm)
    fim_bloco = altura - (120 * mm)

    linhas = 8
    espacamento = (topo_bloco - fim_bloco) / (linhas - 1)

    y_certificado_base = topo_bloco
    y_certifico = topo_bloco - (espacamento * 1)
    y_nome_base = topo_bloco - (espacamento * 1.8)
    y_graduou = topo_bloco - (espacamento * 3)
    y_faixa_base = topo_bloco - (espacamento * 3.8)
    y_exame = topo_bloco - (espacamento * 5)
    y_equipe = topo_bloco - (espacamento * 6)
    y_data = fim_bloco

    ajuste_titulo = -4 * mm

    y_certificado = y_certificado_base + ajuste_titulo
    y_nome = y_nome_base + ajuste_titulo
    y_faixa = y_faixa_base + ajuste_titulo

    largura_nome_maxima = 185 * mm
    largura_quebra_nome = 150 * mm

    # largura menor só para a faixa, para não bater nas logos do fundo
    largura_faixa_maxima = 125 * mm

    texto_centralizado(
        pdf,
        "CERTIFICADO",
        centro_x,
        y_certificado,
        FONTE_TITULO,
        40
    )

    texto_centralizado(
        pdf,
        "CERTIFICO QUE O ATLETA",
        centro_x,
        y_certifico,
        FONTE_TEXTO,
        18
    )

    desenhar_nome_dinamico(
        pdf,
        nome,
        centro_x,
        y_nome,
        FONTE_TITULO,
        25,
        largura_nome_maxima,
        largura_quebra_nome
    )

    texto_centralizado(
        pdf,
        "GRADUOU-SE COM MÉRITO A",
        centro_x,
        y_graduou,
        FONTE_TEXTO,
        18
    )

    desenhar_faixa_dinamica(
        pdf,
        cor_da_faixa,
        centro_x,
        y_faixa,
        FONTE_TITULO,
        40,
        largura_faixa_maxima
    )

    texto_centralizado(
        pdf,
        "COM EXAME DE GRADUAÇÃO CONCEDIDO",
        centro_x,
        y_exame,
        FONTE_TEXTO,
        18
    )

    texto_centralizado(
        pdf,
        "PELA EQUIPE CRIST OSS BJJ.",
        centro_x,
        y_equipe,
        FONTE_TEXTO,
        18
    )

    texto_centralizado(
        pdf,
        data_certificado,
        centro_x,
        y_data,
        FONTE_TEXTO,
        18
    )


def gerar_pdf_certificado(nome, faixa, dia, mes, ano, sede=""):
    buffer = io.BytesIO()

    pdf = canvas.Canvas(
        buffer,
        pagesize=landscape(A4)
    )

    desenhar_certificado_na_pagina(
        pdf,
        nome,
        faixa,
        dia,
        mes,
        ano,
        sede
    )

    pdf.save()
    buffer.seek(0)

    return buffer


def aliases_faixas():
    return {
        "cinza/branca": "cinza/branca",
        "cinza branca": "cinza/branca",
        "cinza": "cinza",
        "cinza/preta": "cinza/preta",
        "cinza preta": "cinza/preta",

        "amarela/branca": "amarela/branca",
        "amarela branca": "amarela/branca",
        "amarelo/branco": "amarela/branca",
        "amarelo branco": "amarela/branca",
        "amarela": "amarela",
        "amarelo": "amarela",
        "amarela/preta": "amarela/preta",
        "amarela preta": "amarela/preta",
        "amarelo/preto": "amarela/preta",
        "amarelo preto": "amarela/preta",

        "laranja/branca": "laranja/branca",
        "laranja branca": "laranja/branca",
        "laranja": "laranja",
        "laranja/preta": "laranja/preta",
        "laranja preta": "laranja/preta",

        "verde/branca": "verde/branca",
        "verde branca": "verde/branca",
        "verde": "verde",
        "verde/preta": "verde/preta",
        "verde preta": "verde/preta",

        "azul": "azul",
        "roxa": "roxa",
        "roxo": "roxa",
        "marrom": "marrom",
        "marron": "marrom",
        "preta": "preta",
        "preto": "preta"
    }


def extrair_certificados_em_lote(texto):
    texto = texto.replace("\r", "\n")

    aliases = aliases_faixas()

    padrao = "|".join(
        re.escape(k)
        for k in sorted(aliases.keys(), key=len, reverse=True)
    )

    regex = re.compile(
        rf"\b({padrao})\b",
        re.IGNORECASE
    )

    certificados = []
    inicio = 0

    for match in regex.finditer(texto):
        nome = texto[inicio:match.start()]
        faixa_detectada = match.group(1).lower()
        faixa = aliases[faixa_detectada]

        nome = re.sub(r"[\n,;:-]+", " ", nome)
        nome = re.sub(r"\s+", " ", nome).strip()

        if nome and nome_valido(nome):
            certificados.append({
                "nome": nome.upper(),
                "faixa": faixa
            })

        inicio = match.end()

    return certificados


def gerar_pdf_certificados_lote(texto_lote, dia, mes, ano, sede=""):
    certificados = extrair_certificados_em_lote(texto_lote)

    if not certificados:
        return None, []

    if len(certificados) > 50:
        return "LIMITE", certificados

    buffer = io.BytesIO()

    pdf = canvas.Canvas(
        buffer,
        pagesize=landscape(A4)
    )

    for index, item in enumerate(certificados):
        desenhar_certificado_na_pagina(
            pdf,
            item["nome"],
            item["faixa"],
            dia,
            mes,
            ano,
            sede
        )

        if index < len(certificados) - 1:
            pdf.showPage()

    pdf.save()
    buffer.seek(0)

    return buffer, certificados
# ======================================================
# DECLARAÇÃO
# ======================================================

def gerar_pdf_declaracao(
    tipo,
    nome_aluno,
    nome_responsavel,
    cpf_responsavel,
    graus,
    dia,
    mes,
    ano
):
    nome_aluno = nome_aluno.strip().upper()
    nome_responsavel = nome_responsavel.strip().upper()
    cpf_responsavel = cpf_responsavel.strip()
    graus = graus.strip()

    data = f"{dia} de {mes} de {ano}"

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)

    largura, altura = A4
    centro_x = largura / 2

    margem_x = 25 * mm
    largura_texto = largura - (50 * mm)

    logo_path = os.path.join(app.root_path, "static", "logo_crist_oss.png")
    ibjjf_path = os.path.join(app.root_path, "static", "IBJJF.png")

    if os.path.exists(logo_path):
        marca = criar_logo_transparente(logo_path, 0.08)
        tamanho_marca = 130 * mm

        pdf.drawImage(
            marca,
            centro_x - (tamanho_marca / 2),
            (altura / 2) - (tamanho_marca / 2),
            width=tamanho_marca,
            height=tamanho_marca,
            mask="auto"
        )

    if tipo == "frequencia":
        titulo = "DECLARAÇÃO DE FREQUÊNCIA E PARTICIPAÇÃO"
    else:
        titulo = "DECLARAÇÃO DE AUSÊNCIA PARA EVENTO"

    pdf.setFont("Helvetica-Bold", 15)
    pdf.drawCentredString(centro_x, altura - (30 * mm), titulo)

    y = altura - (50 * mm)

    if tipo == "frequencia":
        paragrafo_1 = (
            f"A ESCOLA CRIST OSS BJJ, inscrita no CNPJ sob o nº "
            f"44.227.964/0001-42, localizada no bairro Conjunto Ceará, "
            f"nº 348, Fortaleza/CE, declara, para os devidos fins, "
            f"que o(a) aluno(a) {nome_aluno} realiza regularmente o curso "
            f"de Jiu-Jitsu, com frequência assídua às segundas, quartas "
            f"e sextas-feiras, sob orientação do Professor Leandro Marques, "
            f"faixa preta {graus} graus, portador do CPF nº 725.598.963-20."
        )

        paragrafo_2 = (
            f"Declaramos, ainda, que a participação do(a) aluno(a) ocorre "
            f"mediante autorização de seu/sua responsável legal, "
            f"{nome_responsavel}, portador(a) do CPF nº {cpf_responsavel}."
        )

    else:
        paragrafo_1 = (
            f"A ESCOLA CRIST OSS BJJ, inscrita no CNPJ sob o nº "
            f"44.227.964/0001-42, declara, para os devidos fins, "
            f"que o(a) aluno(a) {nome_aluno} precisou ausentar-se de suas "
            f"atividades regulares no dia {data}, em razão de participação "
            f"em evento promovido pela ESCOLA CRIST OSS BJJ, sob supervisão "
            f"do Professor Leandro Marques, faixa preta {graus} graus, "
            f"portador do CPF nº 725.598.963-20."
        )

        paragrafo_2 = (
            f"Declaramos, ainda, que a participação do(a) aluno(a) no referido "
            f"evento ocorreu mediante autorização de seu/sua responsável legal, "
            f"{nome_responsavel}, portador(a) do CPF nº {cpf_responsavel}."
        )

    y = desenhar_paragrafo(
        pdf,
        paragrafo_1,
        margem_x,
        y,
        largura_texto,
        "Helvetica",
        12,
        7 * mm
    )

    y -= 8 * mm

    y = desenhar_paragrafo(
        pdf,
        paragrafo_2,
        margem_x,
        y,
        largura_texto,
        "Helvetica",
        12,
        7 * mm
    )

    if tipo == "evento":
        y -= 10 * mm
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawCentredString(
            centro_x,
            y,
            "DESDE JÁ, AGRADECEMOS A COMPREENSÃO."
        )

    pdf.setFont("Helvetica", 12)

    pdf.drawCentredString(
        centro_x,
        78 * mm,
        "Fortaleza/CE, ____/____/________."
    )

    pdf.drawCentredString(
        centro_x,
        65 * mm,
        "________________________________________________________________"
    )

    pdf.setFont("Helvetica-Bold", 12)

    pdf.drawCentredString(
        centro_x,
        56 * mm,
        "PROFESSOR LEANDRO MARQUES"
    )

    if os.path.exists(ibjjf_path):
        ibjjf = ImageReader(ibjjf_path)

        pdf.drawImage(
            ibjjf,
            centro_x - (12 * mm),
            35 * mm,
            width=24 * mm,
            height=16 * mm,
            preserveAspectRatio=True,
            mask="auto"
        )

    pdf.setFont("Helvetica", 11)

    pdf.drawCentredString(
        centro_x,
        28 * mm,
        "IBJJF: 348820"
    )

    pdf.drawCentredString(
        centro_x,
        18 * mm,
        "CNPJ: 44.227.964/0001-42"
    )

    pdf.save()
    buffer.seek(0)

    return buffer


# ======================================================
# ROTAS LOGIN / MENU
# ======================================================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        senha = request.form.get("senha", "").strip()

        user = buscar_usuario(usuario)

        if user and user["senha"] == senha:
            session["logado"] = True
            session["usuario"] = user["usuario"]
            session["tipo"] = user["tipo"]
            session["foto"] = user["foto"]
            session["id"] = user["id"]

            return redirect(url_for("menu"))

        return render_template(
            "login.html",
            erro="USUÁRIO OU SENHA INVÁLIDOS."
        )

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
def raiz():
    if not usuario_logado():
        return redirect(url_for("login"))

    return redirect(url_for("menu"))


@app.route("/menu")
def menu():
    if not usuario_logado():
        return redirect(url_for("login"))

    return render_template(
        "menu.html",
        usuario=session.get("usuario"),
        foto=session.get("foto"),
        tipo=session.get("tipo")
    )


# ======================================================
# ROTAS CONTA / ADMIN
# ======================================================

@app.route("/minha-conta", methods=["GET", "POST"])
def minha_conta():
    if not usuario_logado():
        return redirect(url_for("login"))

    usuario_atual = buscar_usuario_por_id(session["id"])

    mensagem = None
    erro = None

    if request.method == "POST":
        novo_usuario = request.form.get("novo_usuario", "").strip()
        nova_senha = request.form.get("nova_senha", "").strip()
        foto = request.files.get("foto")

        if novo_usuario != "":
            existente = buscar_usuario(novo_usuario)

            if existente and existente["id"] != usuario_atual["id"]:
                erro = "USUÁRIO JÁ EXISTE."
            else:
                alterar_usuario(usuario_atual["id"], novo_usuario)
                session["usuario"] = novo_usuario

        if not erro and nova_senha != "":
            alterar_senha(usuario_atual["id"], nova_senha)

        if not erro and foto and foto.filename != "":
            nome_arquivo = str(uuid.uuid4()) + ".jpg"

            caminho = os.path.join(
                app.config["UPLOAD_FOLDER"],
                secure_filename(nome_arquivo)
            )

            imagem = Image.open(foto)
            imagem = imagem.convert("RGB")
            imagem.thumbnail((600, 600))
            imagem.save(
                caminho,
                format="JPEG",
                quality=75,
                optimize=True
            )

            alterar_foto(usuario_atual["id"], nome_arquivo)
            session["foto"] = nome_arquivo

        if not erro:
            mensagem = "CONTA ATUALIZADA COM SUCESSO."
            usuario_atual = buscar_usuario_por_id(session["id"])

    return render_template(
        "minha_conta.html",
        usuario=usuario_atual,
        mensagem=mensagem,
        erro=erro
    )


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not usuario_logado():
        return redirect(url_for("login"))

    if not usuario_admin():
        return redirect(url_for("menu"))

    mensagem = None
    erro = None

    if request.method == "POST":
        acao = request.form.get("acao")

        if acao == "criar":
            novo_usuario = request.form.get("novo_usuario", "").strip()
            nova_senha = request.form.get("nova_senha", "").strip()
            tipo = request.form.get("tipo", "comum").strip()

            if novo_usuario == "" or nova_senha == "":
                erro = "PREENCHA USUÁRIO E SENHA."

            elif buscar_usuario(novo_usuario):
                erro = "ESSE USUÁRIO JÁ EXISTE."

            else:
                criar_usuario(novo_usuario, nova_senha, tipo)
                mensagem = "USUÁRIO CRIADO COM SUCESSO."

        elif acao == "alterar_senha":
            usuario_id = int(request.form.get("usuario_id"))
            nova_senha = request.form.get("nova_senha", "").strip()

            if nova_senha == "":
                erro = "DIGITE A NOVA SENHA."
            else:
                alterar_senha(usuario_id, nova_senha)
                mensagem = "SENHA ALTERADA COM SUCESSO."

        elif acao == "excluir":
            usuario_id = int(request.form.get("usuario_id"))

            if usuario_id == session["id"]:
                erro = "VOCÊ NÃO PODE EXCLUIR SUA PRÓPRIA CONTA."
            else:
                excluir_usuario(usuario_id)
                mensagem = "USUÁRIO EXCLUÍDO COM SUCESSO."

    return render_template(
        "admin.html",
        usuarios=listar_usuarios(),
        mensagem=mensagem,
        erro=erro
    )


# ======================================================
# ROTAS CERTIFICADO
# ======================================================

@app.route("/certificado", methods=["GET"])
def certificado():
    if not usuario_logado():
        return redirect(url_for("login"))

    return render_template(
        "index.html",
        faixas=faixas,
        dias=dias,
        meses=meses,
        anos=anos
    )


@app.route("/certificados-lote", methods=["GET"])
def certificados_lote():
    if not usuario_logado():
        return redirect(url_for("login"))

    return render_template(
        "certificados_lote.html",
        dias=dias,
        meses=meses,
        anos=anos
    )


@app.route("/gerar", methods=["POST"])
def gerar():
    if not usuario_logado():
        return redirect(url_for("login"))

    nome = request.form.get("nome", "").strip()
    faixa = request.form.get("faixa", "").strip()
    sede = request.form.get("sede", "").strip()
    dia = request.form.get("dia", "").strip()
    mes = request.form.get("mes", "").strip()
    ano = request.form.get("ano", "").strip()

    if not nome_valido(nome):
        return "Erro: digite o nome completo do aluno.", 400

    if faixa not in faixas:
        return "Erro: faixa inválida.", 400

    if dia not in dias or mes not in meses or ano not in anos:
        return "Erro: data inválida.", 400

    return render_template(
        "visualizar.html",
        nome=nome,
        faixa=faixa,
        sede=sede,
        dia=dia,
        mes=mes,
        ano=ano
    )


@app.route("/gerar-lote", methods=["POST"])
def gerar_lote():
    if not usuario_logado():
        return redirect(url_for("login"))

    texto_lote = request.form.get("texto_lote", "").strip()
    sede = request.form.get("sede", "").strip()
    dia = request.form.get("dia", "").strip()
    mes = request.form.get("mes", "").strip()
    ano = request.form.get("ano", "").strip()

    if dia not in dias or mes not in meses or ano not in anos:
        return "Erro: data inválida.", 400

    pdf_buffer, certificados = gerar_pdf_certificados_lote(
        texto_lote,
        dia,
        mes,
        ano,
        sede
    )

    if pdf_buffer == "LIMITE":
        return "Erro: gere no máximo 50 certificados por vez.", 400

    if not pdf_buffer:
        return "Erro: nenhum certificado encontrado. Verifique se cada nome tem uma faixa depois.", 400

    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=False,
        download_name="certificados_em_lote.pdf"
    )


@app.route("/pdf", methods=["GET"])
def pdf():
    if not usuario_logado():
        return redirect(url_for("login"))

    nome = request.args.get("nome", "").strip()
    faixa = request.args.get("faixa", "").strip()
    sede = request.args.get("sede", "").strip()
    dia = request.args.get("dia", "").strip()
    mes = request.args.get("mes", "").strip()
    ano = request.args.get("ano", "").strip()

    if not nome_valido(nome):
        return "Erro: nome inválido.", 400

    if faixa not in faixas:
        return "Erro: faixa inválida.", 400

    if dia not in dias or mes not in meses or ano not in anos:
        return "Erro: data inválida.", 400

    pdf_buffer = gerar_pdf_certificado(
        nome,
        faixa,
        dia,
        mes,
        ano,
        sede
    )

    nome_arquivo = nome.upper().replace(" ", "_").replace("/", "_")

    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=False,
        download_name=f"certificado_{nome_arquivo}.pdf"
    )


# ======================================================
# ROTAS DECLARAÇÕES
# ======================================================

@app.route("/declaracao")
def declaracao_menu():
    if not usuario_logado():
        return redirect(url_for("login"))

    return render_template("declaracao_menu.html")


@app.route("/declaracao/frequencia")
def declaracao_frequencia():
    if not usuario_logado():
        return redirect(url_for("login"))

    return render_template(
        "declaracao_form.html",
        tipo="frequencia",
        titulo="DECLARAÇÃO DE FREQUÊNCIA E PARTICIPAÇÃO",
        dias=dias,
        meses=meses,
        anos=anos
    )


@app.route("/declaracao/evento")
def declaracao_evento():
    if not usuario_logado():
        return redirect(url_for("login"))

    return render_template(
        "declaracao_form.html",
        tipo="evento",
        titulo="DECLARAÇÃO DE AUSÊNCIA PARA EVENTO",
        dias=dias,
        meses=meses,
        anos=anos
    )


@app.route("/declaracao/visualizar", methods=["POST"])
def declaracao_visualizar():
    if not usuario_logado():
        return redirect(url_for("login"))

    tipo = request.form.get("tipo", "").strip()
    nome_aluno = request.form.get("nome_aluno", "").strip()
    nome_responsavel = request.form.get("nome_responsavel", "").strip()
    cpf_responsavel = request.form.get("cpf_responsavel", "").strip()
    graus = request.form.get("graus", "").strip()
    dia = request.form.get("dia", "").strip()
    mes = request.form.get("mes", "").strip()
    ano = request.form.get("ano", "").strip()

    if tipo not in ["frequencia", "evento"]:
        return "Erro: tipo de declaração inválido.", 400

    if not nome_valido(nome_aluno):
        return "Erro: informe o nome completo do aluno.", 400

    if not nome_valido(nome_responsavel):
        return "Erro: informe o nome completo do responsável.", 400

    if cpf_responsavel == "":
        return "Erro: informe o CPF do responsável.", 400

    if graus == "":
        return "Erro: informe o número de graus do professor.", 400

    return render_template(
        "visualizar_declaracao.html",
        tipo=tipo,
        nome_aluno=nome_aluno,
        nome_responsavel=nome_responsavel,
        cpf_responsavel=cpf_responsavel,
        graus=graus,
        dia=dia,
        mes=mes,
        ano=ano
    )


@app.route("/declaracao/pdf")
def declaracao_pdf():
    if not usuario_logado():
        return redirect(url_for("login"))

    tipo = request.args.get("tipo", "").strip()
    nome_aluno = request.args.get("nome_aluno", "").strip()
    nome_responsavel = request.args.get("nome_responsavel", "").strip()
    cpf_responsavel = request.args.get("cpf_responsavel", "").strip()
    graus = request.args.get("graus", "").strip()
    dia = request.args.get("dia", "").strip()
    mes = request.args.get("mes", "").strip()
    ano = request.args.get("ano", "").strip()

    if tipo not in ["frequencia", "evento"]:
        return "Erro: tipo de declaração inválido.", 400

    if not nome_valido(nome_aluno):
        return "Erro: nome do aluno inválido.", 400

    if not nome_valido(nome_responsavel):
        return "Erro: nome do responsável inválido.", 400

    if cpf_responsavel == "":
        return "Erro: CPF inválido.", 400

    if graus == "":
        return "Erro: grau inválido.", 400

    pdf_buffer = gerar_pdf_declaracao(
        tipo,
        nome_aluno,
        nome_responsavel,
        cpf_responsavel,
        graus,
        dia,
        mes,
        ano
    )

    nome_arquivo = nome_aluno.upper().replace(" ", "_").replace("/", "_")

    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=False,
        download_name=f"declaracao_{nome_arquivo}.pdf"
    )


# ======================================================
# START
# ======================================================

if __name__ == "__main__":
    app.run(debug=True)
