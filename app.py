import os
import io

from flask import Flask, render_template, request, send_file
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.units import mm


app = Flask(__name__)

# ======================================================
# CONFIG
# ======================================================

faixas = [
    "cinza/branca",
    "cinza",
    "cinza/preta",
    "amarela/branca",
    "amarela",
    "amarela/preta",
    "laranja/branca",
    "laranja",
    "laranja/preta",
    "verde/branca",
    "verde",
    "verde/preta",
    "azul",
    "roxa",
    "marrom",
    "preta"
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
# FUNÇÕES
# ======================================================

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
    largura_nome = pdfmetrics.stringWidth(nome, fonte, tamanho)

    if largura_nome <= largura_quebra:
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

    if len(nome_linhas) == 1:
        texto_centralizado(
            pdf,
            nome_linhas[0],
            centro_x,
            y_nome,
            fonte,
            tamanho_nome
        )

    else:
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


def gerar_pdf_certificado(nome, faixa, dia, mes, ano):
    nome = nome.strip().upper()
    data_certificado = f"{dia} de {mes} de {ano}"
    cor_da_faixa = f"FAIXA {faixa.upper()}"

    buffer = io.BytesIO()

    pdf = canvas.Canvas(
        buffer,
        pagesize=landscape(A4)
    )

    largura, altura = landscape(A4)
    centro_x = largura / 2

    # ==================================================
    # FUNDO
    # ==================================================

    nome_fundo = fundos_por_faixa[faixa]

    caminho_fundo = os.path.join(
        app.root_path,
        "fundos",
        nome_fundo
    )

    if os.path.exists(caminho_fundo):
        fundo = ImageReader(caminho_fundo)

        pdf.drawImage(
            fundo,
            0,
            0,
            width=largura,
            height=altura
        )

    # ==================================================
    # MEDIDAS
    # ==================================================

    fonte_titulo = FONTE_TITULO
    fonte_texto = FONTE_TEXTO

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

    tamanho_faixa = tamanho_fonte_dinamico(
        cor_da_faixa,
        fonte_titulo,
        40,
        largura_nome_maxima
    )

    # ==================================================
    # TEXTOS
    # ==================================================

    texto_centralizado(
        pdf,
        "CERTIFICADO",
        centro_x,
        y_certificado,
        fonte_titulo,
        40
    )

    texto_centralizado(
        pdf,
        "CERTIFICO QUE O ATLETA",
        centro_x,
        y_certifico,
        fonte_texto,
        18
    )

    desenhar_nome_dinamico(
        pdf,
        nome,
        centro_x,
        y_nome,
        fonte_titulo,
        25,
        largura_nome_maxima,
        largura_quebra_nome
    )

    texto_centralizado(
        pdf,
        "GRADUOU-SE COM MÉRITO A",
        centro_x,
        y_graduou,
        fonte_texto,
        18
    )

    texto_centralizado(
        pdf,
        cor_da_faixa,
        centro_x,
        y_faixa,
        fonte_titulo,
        tamanho_faixa
    )

    texto_centralizado(
        pdf,
        "COM EXAME DE GRADUAÇÃO CONCEDIDO",
        centro_x,
        y_exame,
        fonte_texto,
        18
    )

    texto_centralizado(
        pdf,
        "PELA EQUIPE CRIST OSS BJJ.",
        centro_x,
        y_equipe,
        fonte_texto,
        18
    )

    texto_centralizado(
        pdf,
        data_certificado,
        centro_x,
        y_data,
        fonte_texto,
        18
    )

    pdf.save()

    buffer.seek(0)

    return buffer


# ======================================================
# ROTAS
# ======================================================

@app.route("/", methods=["GET"])
def index():
    return render_template(
        "index.html",
        faixas=faixas,
        dias=dias,
        meses=meses,
        anos=anos
    )


@app.route("/gerar", methods=["POST"])
def gerar():
    nome = request.form.get("nome", "").strip()
    faixa = request.form.get("faixa", "").strip()
    dia = request.form.get("dia", "").strip()
    mes = request.form.get("mes", "").strip()
    ano = request.form.get("ano", "").strip()

    if not nome_valido(nome):
        return "Erro: digite o nome completo do aluno.", 400

    if faixa not in faixas:
        return "Erro: faixa inválida.", 400

    if dia not in dias or mes not in meses or ano not in anos:
        return "Erro: data inválida.", 400

    pdf_buffer = gerar_pdf_certificado(
        nome,
        faixa,
        dia,
        mes,
        ano
    )

    nome_arquivo = nome.upper().replace(" ", "_").replace("/", "_")

    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=False,
        download_name=f"certificado_{nome_arquivo}.pdf"
    )


# ======================================================
# START
# ======================================================

if __name__ == "__main__":
    app.run(debug=True)
