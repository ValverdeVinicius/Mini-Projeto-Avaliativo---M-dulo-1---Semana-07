#!/usr/bin/env python3
"""
Mini-Projeto Avaliativo - Modulo 1 - Semana 07
Festa em Cena - analise exploratoria dos pedidos de Halloween.

O programa le halloween_vendas.csv com Pandas, preserva o arquivo original,
padroniza textos, valida quantidade/preco, converte datas com datetime.strptime,
investiga a regra de entrega e gera um relatorio manual no terminal.

Uso:
    python main.py
    python main.py caminho/para/halloween_vendas.csv

Requisitos: Python 3.10+ e pandas.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

# O caminho e resolvido a partir deste arquivo para o script funcionar em
# qualquer diretorio de trabalho, desde que o CSV esteja junto do main.py.
ARQUIVO_PADRAO = Path(__file__).resolve().with_name("halloween_vendas.csv")

COLUNAS_OBRIGATORIAS = [
    "pedido_id",
    "data_venda",
    "produto",
    "categoria",
    "canal_venda",
    "cidade",
    "quantidade",
    "preco_unitario",
    "custo_unitario",
    "desconto_pct",
    "status_pedido",
    "publico",
    "tamanho",
    "data_entrega",
]

# Dicionario de padronizacao: a chave e a forma normalizada (minuscula, sem
# espacos extras) e o valor e o rotulo oficial usado nas contagens.
CANAIS_CANONICOS = {
    "mercado": "Mercado",
    "loja física": "Loja física",
    "loja fisica": "Loja física",
    "web": "Web",
}
CANAIS_VALIDOS = set(CANAIS_CANONICOS.values())

FORMATO_DATA = "%Y-%m-%d %H:%M:%S"
FORMATO_DATA_BR = "%d/%m/%Y"
STATUS_CANCELADO = "cancelado"


def carregar_dados(caminho: str | Path) -> tuple[pd.DataFrame, dict[str, int]]:
    """Le o CSV como texto e devolve o DataFrame mais a contagem inicial de vazios.

    Decisoes:
    - dtype=str: todos os campos sao lidos como texto, como pede o enunciado.
    - keep_default_na=False: uma celula vazia continua sendo "" em vez de virar
      NaN automaticamente. Isso torna os problemas visiveis e evita imputacao
      silenciosa de valores.
    - O arquivo e apenas lido; nenhuma escrita e feita no CSV original.
    - As colunas originais de categoria, canal, data de venda e data de entrega
      sao copiadas para colunas *_original antes de qualquer transformacao.
    """
    caminho = Path(caminho)
    if not caminho.is_file():
        raise FileNotFoundError(
            f"CSV nao encontrado em '{caminho}'. "
            "Coloque halloween_vendas.csv na mesma pasta do main.py."
        )

    try:
        df = pd.read_csv(
            caminho,
            sep=",",
            encoding="utf-8",
            dtype=str,
            keep_default_na=False,
        )
    except UnicodeDecodeError as exc:
        raise ValueError("O CSV precisa estar em UTF-8.") from exc

    faltantes = [coluna for coluna in COLUNAS_OBRIGATORIAS if coluna not in df.columns]
    if faltantes:
        raise ValueError(
            "Colunas obrigatorias ausentes no CSV: " + ", ".join(faltantes)
        )

    # Revisao inicial de nulos: conta celulas vazias por coluna, sem alterar nada.
    nulos = {
        coluna: int((df[coluna].astype(str).str.strip() == "").sum())
        for coluna in df.columns
    }

    # Preservamos o texto recebido para auditoria e para a apresentacao brasileira.
    for coluna in ("categoria", "canal_venda", "data_venda", "data_entrega"):
        df[f"{coluna}_original"] = df[coluna].copy()

    return df, nulos


def normalizar_categoria(valor: str) -> str:
    """Padroniza uma categoria com strip, lower e re.sub.

    A expressao regular remove pontuacao, digitos e simbolos, preservando letras
    (inclusive acentuadas, caso apareçam em outra base) e espacos. Depois,
    espacos repetidos sao reduzidos a um. Se nada restar, usamos o valor
    solicitado "sem categoria". A comparacao final e feita em minusculas.
    """
    if valor is None:
        return "sem categoria"

    texto = str(valor).strip().lower()
    # [a-zà-öø-ÿ] cobre letras latinas minusculas, com ou sem acento; \s preserva
    # espacos para depois normalizarmos espacos repetidos.
    texto = re.sub(r"[^a-zà-öø-ÿ\s]", "", texto)
    texto = re.sub(r"\s+", " ", texto).strip()

    if texto == "":
        return "sem categoria"
    return texto


def _categoria_tinha_formatacao_irregular(valor: str) -> bool:
    """Indica se a categoria nao vazia precisava de limpeza de espacos/pontuacao.

    A mudanca de caixa (lower) e aplicada a todas as categorias e, por isso, nao
    e contada aqui. Esta funcao mede apenas os residuos de formatacao que a
    limpeza precisou corrigir, para que a contagem seja interpretavel.
    """
    if not valor or not str(valor).strip():
        return False

    original = str(valor)
    sem_pontuacao = re.sub(r"[^A-Za-zÀ-ÖØ-öø-ÿ\s]", "", original)
    sem_espacos_extras = re.sub(r"\s+", " ", sem_pontuacao).strip()

    return (original != original.strip()) or (sem_espacos_extras != original.strip())


def normalizar_canal(valor: str) -> str:
    """Devolve o rotulo oficial do canal ou "" quando o valor nao e reconhecido.

    O strip e o lower removem variacoes de caixa e espacos. O dicionario evita
    que " web ", "Web" e "WEB" sejam tratados como canais diferentes. Valores
    desconhecidos nao sao inventados: ficam vazios e sao excluidos das contagens
    por canal, com o total de exclusoes informado no relatorio.
    """
    if valor is None:
        return ""

    texto = re.sub(r"\s+", " ", str(valor).strip().lower())
    return CANAIS_CANONICOS.get(texto, "")


def padronizar_textos(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Aplica as regras de categoria e canal, devolvendo o DataFrame e as contagens."""
    novo = df.copy()

    categorias_antes = novo["categoria_original"].copy()
    canais_antes = novo["canal_venda_original"].copy()

    # List comprehension deixa explicito que cada valor passa pela funcao de
    # normalizacao; o resultado final e sempre texto.
    novo["categoria"] = [normalizar_categoria(valor) for valor in categorias_antes]
    novo["canal_venda"] = [normalizar_canal(valor) for valor in canais_antes]

    # Um canal so entra nas contagens se for um dos tres rotulos oficiais.
    novo["canal_reconhecido"] = novo["canal_venda"].isin(CANAIS_VALIDOS)
    novo.loc[~novo["canal_reconhecido"], "canal_venda"] = ""

    categorias_vazias = sum(1 for valor in categorias_antes if not str(valor).strip())
    categorias_nao_vazias = len(categorias_antes) - categorias_vazias
    categorias_alteradas = sum(
        1
        for valor in categorias_antes
        if _categoria_tinha_formatacao_irregular(str(valor))
    )
    categorias_mudanca_textual = sum(
        1
        for original, final in zip(categorias_antes, novo["categoria"])
        if str(original).strip() and final != str(original)
    )
    canais_vazios = sum(1 for valor in canais_antes if not str(valor).strip())
    canais_alterados = sum(
        1
        for original, final in zip(canais_antes, novo["canal_venda"])
        if str(original).strip() and final and final != str(original)
    )
    canais_nao_reconhecidos = int((~novo["canal_reconhecido"]).sum())

    stats = {
        "categorias_vazias_preenchidas": categorias_vazias,
        "categorias_nao_vazias": categorias_nao_vazias,
        "categorias_nao_vazias_alteradas": categorias_alteradas,
        "categorias_mudanca_textual": categorias_mudanca_textual,
        "canais_vazios": canais_vazios,
        "canais_alterados": canais_alterados,
        "canais_nao_reconhecidos": canais_nao_reconhecidos,
    }
    return novo, stats


def validar_numeros(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Valida quantidade e preco sem preencher ou corrigir valores.

    Regras justificadas:
    - quantidade deve ser um inteiro maior que zero. Quantidade negativa, zero,
      vazia, nao numerica ou fracionaria e marcada como invalida. Nao usamos
      media/mediana para substituir, pois isso inventaria unidades vendidas.
    - preco_unitario deve estar preenchido e ser maior ou igual a zero. Zero e
      aceito pela regra (pode representar promocao/cortesia); vazio, texto nao
      numerico ou negativo e invalido. Nao imputamos preco.
    - As flags permitem contar ocorrencias por campo e a uniao de pedidos
      afetados sem somar duas vezes o mesmo pedido.
    """
    novo = df.copy()

    quantidade_texto = novo["quantidade"].fillna("").astype(str).str.strip()
    preco_texto = novo["preco_unitario"].fillna("").astype(str).str.strip()

    quantidade_num = pd.to_numeric(quantidade_texto, errors="coerce")
    preco_num = pd.to_numeric(preco_texto, errors="coerce")

    quantidade_vazia = quantidade_texto == ""
    quantidade_nao_numerica = quantidade_num.isna() & ~quantidade_vazia
    quantidade_nao_positiva = quantidade_num.notna() & (quantidade_num <= 0)
    quantidade_nao_inteira = (
        quantidade_num.notna() & (quantidade_num > 0) & (quantidade_num % 1 != 0)
    )
    quantidade_invalida = (
        quantidade_vazia
        | quantidade_nao_numerica
        | quantidade_nao_positiva
        | quantidade_nao_inteira
    )

    preco_vazio = preco_texto == ""
    preco_nao_numerico = preco_num.isna() & ~preco_vazio
    preco_negativo = preco_num.notna() & (preco_num < 0)
    preco_invalido = preco_vazio | preco_nao_numerico | preco_negativo

    # As colunas de flags documentam o problema sem alterar o dado recebido.
    novo["quantidade_invalida"] = quantidade_invalida
    novo["preco_invalido"] = preco_invalido
    novo["problema_numerico"] = quantidade_invalida | preco_invalido

    stats = {
        "quantidade_invalida": int(quantidade_invalida.sum()),
        "quantidade_vazia": int(quantidade_vazia.sum()),
        "quantidade_nao_numerica": int(quantidade_nao_numerica.sum()),
        "quantidade_nao_positiva": int(quantidade_nao_positiva.sum()),
        "quantidade_nao_inteira": int(quantidade_nao_inteira.sum()),
        "preco_invalido": int(preco_invalido.sum()),
        "preco_vazio": int(preco_vazio.sum()),
        "preco_nao_numerico": int(preco_nao_numerico.sum()),
        "preco_negativo": int(preco_negativo.sum()),
        "pedidos_com_problema_numerico": int((quantidade_invalida | preco_invalido).sum()),
        "sobreposicao_quantidade_preco": int(
            (quantidade_invalida & preco_invalido).sum()
        ),
    }
    return novo, stats


def converter_datas(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Converte data_venda com datetime.strptime e cria as partes da data.

    - O texto original permanece em data_venda_original.
    - Datas vazias ou invalidas sao marcadas, viram NaT e NAO sao substituidas
      pela data de hoje nem por uma data inventada. O processamento continua.
    - ano, mes, dia e hora sao extraidos do objeto datetime.
    - A apresentacao brasileira e criada explicitamente com strftime("%d/%m/%Y").
    """
    novo = df.copy()

    datas: list[datetime | None] = []
    status: list[str] = []
    anos: list[int | None] = []
    meses: list[int | None] = []
    dias: list[int | None] = []
    horas: list[int | None] = []
    datas_br: list[str] = []

    for valor in novo["data_venda_original"]:
        texto = str(valor).strip()

        if texto == "":
            datas.append(None)
            status.append("vazia")
            anos.append(None)
            meses.append(None)
            dias.append(None)
            horas.append(None)
            datas_br.append("")
            continue

        try:
            data = datetime.strptime(texto, FORMATO_DATA)
        except (TypeError, ValueError):
            # ValueError cobre formatos invalidos; o loop segue para os demais.
            datas.append(None)
            status.append("invalida")
            anos.append(None)
            meses.append(None)
            dias.append(None)
            horas.append(None)
            datas_br.append("")
            continue

        datas.append(data)
        status.append("valida")
        anos.append(data.year)
        meses.append(data.month)
        dias.append(data.day)
        horas.append(data.hour)
        datas_br.append(data.strftime(FORMATO_DATA_BR))

    novo["data_venda_dt"] = pd.to_datetime(
        pd.Series(datas, index=novo.index), errors="coerce"
    )
    novo["data_venda_status"] = status
    novo["data_venda_invalida"] = [s != "valida" for s in status]
    novo["ano"] = pd.array(anos, dtype="Int64")
    novo["mes"] = pd.array(meses, dtype="Int64")
    novo["dia"] = pd.array(dias, dtype="Int64")
    novo["hora"] = pd.array(horas, dtype="Int64")
    novo["data_venda_br"] = datas_br

    pedidos_invalidos = novo.loc[
        novo["data_venda_invalida"], "pedido_id"
    ].tolist()
    stats: dict[str, Any] = {
        "validas": int((~novo["data_venda_invalida"]).sum()),
        "invalidas": int((novo["data_venda_status"] == "invalida").sum()),
        "vazias": int((novo["data_venda_status"] == "vazia").sum()),
        "pedidos_invalidos": pedidos_invalidos,
    }
    return novo, stats


def analisar_entregas(df: pd.DataFrame) -> dict[str, Any]:
    """Investiga a hipotese: toda data_entrega vazia pertence a pedido Cancelado?

    A regra e apenas investigada; status e datas de entrega nao sao alterados.
    O grupo "sem entrega e outros status" e o contraexemplo que torna a hipotese
    falsa, caso exista. Tambem contamos os cancelados e os cancelados com entrega
    para deixar clara a diferenca entre a hipotese testada e a relacao inversa.
    """
    sem_entrega = (
        df["data_entrega_original"].fillna("").astype(str).str.strip() == ""
    )
    cancelado = (
        df["status_pedido"].fillna("").astype(str).str.strip().str.casefold()
        == STATUS_CANCELADO
    )

    sem_entrega_cancelados = sem_entrega & cancelado
    sem_entrega_outros = sem_entrega & ~cancelado

    exemplos = df.loc[
        sem_entrega_outros,
        ["pedido_id", "status_pedido", "canal_venda", "data_venda_original"],
    ].head(3)

    return {
        "sem_data_entrega": int(sem_entrega.sum()),
        "cancelados_total": int(cancelado.sum()),
        "sem_entrega_cancelados": int(sem_entrega_cancelados.sum()),
        "sem_entrega_outros": int(sem_entrega_outros.sum()),
        "cancelados_com_entrega": int((~sem_entrega & cancelado).sum()),
        "hipotese_verdadeira": bool(sem_entrega_outros.sum() == 0),
        "exemplos_outros": exemplos.to_dict("records"),
    }


def contar_por_canal(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Conta pedidos por canal reconhecido, incluindo todos os status.

    Nao filtramos Cancelado/Concluido/Devolvido: a contagem e de pedidos
    registrados, nao de vendas concluidas. Canais vazios ou desconhecidos ficam
    de fora e o total de exclusoes e devolvido separadamente.
    """
    reconhecidos = df.loc[df["canal_reconhecido"]].copy()
    contagem = (
        reconhecidos["canal_venda"]
        .value_counts()
        .to_frame("pedidos")
        .reset_index()
        .rename(columns={"canal_venda": "canal"})
    )
    total = len(reconhecidos)
    if total:
        contagem["percentual"] = (contagem["pedidos"] / total * 100).round(1)
    else:
        contagem["percentual"] = 0.0

    contagem = contagem.sort_values("pedidos", ascending=False).reset_index(drop=True)
    return contagem, {
        "total_reconhecido": total,
        "exclusoes": int((~df["canal_reconhecido"]).sum()),
    }


def contar_por_ano_mes(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Conta pedidos por ano e mes, usando somente data_venda valida.

    Agrupamos por duas colunas (ano e mes) para nao misturar 2024 e 2025.
    Todos os status entram; pedidos com data invalida/vazia sao excluidos e
    informados no total de exclusoes.
    """
    validos = df.loc[df["data_venda_dt"].notna()].copy()
    contagem = (
        validos.groupby(["ano", "mes"], dropna=True)
        .size()
        .to_frame("pedidos")
        .reset_index()
    )
    contagem["ano"] = contagem["ano"].astype(int)
    contagem["mes"] = contagem["mes"].astype(int)
    contagem["ano_mes"] = (
        contagem["ano"].astype(str)
        + "-"
        + contagem["mes"].astype(str).str.zfill(2)
    )
    contagem = contagem.sort_values(["ano", "mes"]).reset_index(drop=True)

    if len(validos):
        contagem["percentual"] = (contagem["pedidos"] / len(validos) * 100).round(1)
    else:
        contagem["percentual"] = 0.0

    return contagem, {
        "total_com_data_valida": len(validos),
        "exclusoes": int((~df["data_venda_dt"].notna()).sum()),
    }


def _lista_limitada(valores: list[Any], limite: int = 10) -> str:
    """Formata uma lista curta para o relatorio, sem esconder o total."""
    if not valores:
        return "nenhum"
    mostrados = ", ".join(str(valor) for valor in valores[:limite])
    if len(valores) > limite:
        mostrados += f", ... (+{len(valores) - limite})"
    return mostrados


def imprimir_relatorio(df: pd.DataFrame, nulos: dict[str, int]) -> None:
    """Executa as transformacoes e imprime o relatorio manual completo."""
    total_linhas = len(df)
    total_colunas = len([coluna for coluna in df.columns if not coluna.endswith("_original")])

    print("=" * 78)
    print("FESTA EM CENA - ANALISE EXPLORATORIA DOS PEDIDOS DE HALLOWEEN")
    print("=" * 78)
    print(f"Total de linhas lidas: {total_linhas}")
    print(f"Total de colunas: {total_colunas}")

    print("\nPrimeiros 3 registros (texto original, antes das transformacoes):")
    colunas_exibir = [
        "pedido_id",
        "data_venda",
        "produto",
        "categoria",
        "canal_venda",
        "quantidade",
        "preco_unitario",
        "status_pedido",
        "data_entrega",
    ]
    print(df[colunas_exibir].head(3).to_string(index=False))

    print("\nRevisao de celulas vazias no CSV original:")
    colunas_com_vazio = {col: qtd for col, qtd in nulos.items() if qtd > 0}
    if colunas_com_vazio:
        for coluna, quantidade in colunas_com_vazio.items():
            print(f"  {coluna}: {quantidade}")
    else:
        print("  nenhuma celula vazia")
    print(f"  Total de celulas vazias: {sum(nulos.values())}")

    # ----- Transformacoes -----
    df, stats_texto = padronizar_textos(df)
    df, stats_numeros = validar_numeros(df)
    df, stats_datas = converter_datas(df)
    stats_entrega = analisar_entregas(df)
    contagem_canal, info_canal = contar_por_canal(df)
    contagem_ano_mes, info_ano_mes = contar_por_ano_mes(df)

    # ----- Categorias e canais -----
    print("\n" + "-" * 78)
    print("1. PADRONIZACAO DE TEXTO (CATEGORIA E CANAL)")
    print("-" * 78)
    print(
        "Categorias vazias preenchidas com 'sem categoria': "
        f"{stats_texto['categorias_vazias_preenchidas']}"
    )
    print(
        "Categorias nao vazias alteradas (espacos/pontuacao): "
        f"{stats_texto['categorias_nao_vazias_alteradas']} "
        f"de {stats_texto['categorias_nao_vazias']}"
    )
    print(
        "  Obs.: .lower() foi aplicado a todas as categorias nao vazias "
        f"({stats_texto['categorias_mudanca_textual']} tiveram texto final "
        "diferente do original); a contagem acima destaca apenas as que "
        "tinham espacos ou pontuacao."
    )
    print("\nCategorias apos a padronizacao:")
    contagem_categorias = (
        df["categoria"].value_counts().to_frame("pedidos").reset_index()
    )
    contagem_categorias.columns = ["categoria", "pedidos"]
    print(contagem_categorias.to_string(index=False))
    print(
        "\nCanais: "
        f"{stats_texto['canais_alterados']} valores alterados; "
        f"{stats_texto['canais_nao_reconhecidos']} nao reconhecidos; "
        f"{stats_texto['canais_vazios']} vazios."
    )

    # ----- Numeros -----
    print("\n" + "-" * 78)
    print("2. VALIDACAO NUMERICA (SEM IMPUTACAO)")
    print("-" * 78)
    print(
        f"Quantidade invalida: {stats_numeros['quantidade_invalida']} "
        f"[vazias: {stats_numeros['quantidade_vazia']}; "
        f"nao numericas: {stats_numeros['quantidade_nao_numerica']}; "
        f"menores ou iguais a zero: {stats_numeros['quantidade_nao_positiva']}; "
        f"nao inteiras: {stats_numeros['quantidade_nao_inteira']}]"
    )
    print(
        f"Preco unitario invalido: {stats_numeros['preco_invalido']} "
        f"[vazios: {stats_numeros['preco_vazio']}; "
        f"nao numericos: {stats_numeros['preco_nao_numerico']}; "
        f"negativos: {stats_numeros['preco_negativo']}]"
    )
    print(
        "Pedidos com problema numerico (uniao, sem somar em dobro): "
        f"{stats_numeros['pedidos_com_problema_numerico']} "
        "(interseccao quantidade/preco: "
        f"{stats_numeros['sobreposicao_quantidade_preco']})"
    )

    # ----- Datas -----
    print("\n" + "-" * 78)
    print("3. DATAS DE VENDA")
    print("-" * 78)
    print(f"Datas validas: {stats_datas['validas']}")
    print(f"Datas invalidas: {stats_datas['invalidas']}")
    print(f"Datas vazias: {stats_datas['vazias']}")
    print(
        "Pedidos com data invalida: "
        f"{_lista_limitada(stats_datas['pedidos_invalidos'])}"
    )

    exemplo = df.loc[df["data_venda_status"] == "valida"].head(1)
    if len(exemplo):
        linha = exemplo.iloc[0]
        print(
            "Exemplo de preservacao/conversao: "
            f"pedido {linha['pedido_id']} | "
            f"original \"{linha['data_venda_original']}\" -> "
            f"{linha['data_venda_br']} | "
            f"ano={linha['ano']}, mes={linha['mes']}, "
            f"dia={linha['dia']}, hora={linha['hora']}"
        )

    # ----- Regra de entrega -----
    print("\n" + "-" * 78)
    print("4. REGRA DE NEGOCIO: ENTREGA SEM DATA")
    print("-" * 78)
    print(f"Pedidos sem data de entrega: {stats_entrega['sem_data_entrega']}")
    print(
        "  - sem entrega e Cancelado: "
        f"{stats_entrega['sem_entrega_cancelados']}"
    )
    print(
        "  - sem entrega e outros status: "
        f"{stats_entrega['sem_entrega_outros']}"
    )
    print(f"Total de pedidos cancelados: {stats_entrega['cancelados_total']}")
    print(
        "Cancelados com data de entrega: "
        f"{stats_entrega['cancelados_com_entrega']}"
    )
    conclusao = "VERDADEIRA" if stats_entrega["hipotese_verdadeira"] else "FALSA"
    print(
        "Hipotese 'toda data_entrega vazia => status Cancelado': "
        f"{conclusao}"
    )
    if not stats_entrega["hipotese_verdadeira"]:
        print(
            f"  Contraexemplos encontrados: "
            f"{stats_entrega['sem_entrega_outros']}"
        )
        print("  Exemplos do grupo sem entrega e com outro status:")
        for exemplo_entrega in stats_entrega["exemplos_outros"]:
            print(
                "   ",
                f"pedido_id={exemplo_entrega['pedido_id']} | "
                f"status={exemplo_entrega['status_pedido']} | "
                f"canal={exemplo_entrega['canal_venda']} | "
                f"data_venda={exemplo_entrega['data_venda_original']}",
            )
    print("  Status e datas de entrega nao foram alterados.")

    # ----- Contagem por canal -----
    print("\n" + "-" * 78)
    print("5. PEDIDOS POR CANAL (TODOS OS STATUS)")
    print("-" * 78)
    if len(contagem_canal):
        print(contagem_canal.to_string(index=False))
    else:
        print("Nenhum canal reconhecido.")
    print(
        f"Total reconhecido: {info_canal['total_reconhecido']} | "
        f"Excluidos (canal vazio/desconhecido): {info_canal['exclusoes']}"
    )
    print("  Observacao: a contagem inclui Cancelado, Concluido e Devolvido.")

    # ----- Contagem por ano-mes -----
    print("\n" + "-" * 78)
    print("6. PEDIDOS POR ANO-MES (TODOS OS STATUS, DATAS VALIDAS)")
    print("-" * 78)
    if len(contagem_ano_mes):
        exibir_ano_mes = contagem_ano_mes[
            ["ano_mes", "pedidos", "percentual"]
        ].copy()
        print(exibir_ano_mes.to_string(index=False))
    else:
        print("Nenhuma data valida para agrupar.")
    print(
        f"Total com data valida: {info_ano_mes['total_com_data_valida']} | "
        f"Excluidos por data invalida/vazia: {info_ano_mes['exclusoes']}"
    )
    print("  Observacao: agrupamos por ano e mes; 2024-10 e 2025-10 sao linhas distintas.")
    print("  Observacao: a contagem inclui todos os status, nao apenas concluidos.")

    # ----- Descobertas -----
    print("\n" + "-" * 78)
    print("7. DUAS DESCOBERTAS")
    print("-" * 78)
    if len(contagem_canal):
        canal_top = contagem_canal.iloc[0]
        print(
            "Descoberta por canal: "
            f"{canal_top['canal']} concentra {int(canal_top['pedidos'])} "
            f"dos {info_canal['total_reconhecido']} pedidos reconhecidos "
            f"({canal_top['percentual']:.1f}%)."
        )
        if len(contagem_canal) > 1:
            segundo = contagem_canal.iloc[1]
            print(
                f"  Comparacao: {segundo['canal']} tem "
                f"{int(segundo['pedidos'])} pedidos "
                f"({segundo['percentual']:.1f}%)."
            )
        print(
            "  Interpretacao: o canal Web e o maior ponto de registro de pedidos "
            "nesta base ficticia; isso pode orientar atencao comercial e de estoque."
        )
        print(
            "  Limitacao: contar pedidos nao e medir receita nem vendas concluidas; "
            "ha 19 pedidos com problema numerico e a base e ficticia, sem "
            "representatividade do mercado real."
        )

    if len(contagem_ano_mes):
        outubro = contagem_ano_mes.loc[contagem_ano_mes["mes"] == 10]
        total_outubro = int(outubro["pedidos"].sum())
        ano_mes_top = contagem_ano_mes.iloc[
            int(contagem_ano_mes["pedidos"].idxmax())
        ]
        agosto = contagem_ano_mes.loc[contagem_ano_mes["mes"] == 8]
        total_agosto = int(agosto["pedidos"].sum())
        print(
            "Descoberta por periodo: outubro soma "
            f"{total_outubro} dos {info_ano_mes['total_com_data_valida']} "
            "pedidos com data valida "
            f"({total_outubro / info_ano_mes['total_com_data_valida'] * 100:.1f}%), "
            f"com o maior mes isolado em {ano_mes_top['ano_mes']} "
            f"({int(ano_mes_top['pedidos'])} pedidos)."
        )
        print(
            f"  Comparacao: agosto soma {total_agosto} pedidos "
            f"({total_agosto / info_ano_mes['total_com_data_valida'] * 100:.1f}%)."
        )
        print(
            "  Interpretacao: ha concentracao em outubro nos dois anos, coerente "
            "com a sazonalidade do Halloween."
        )
        print(
            "  Limitacao: a base cobre apenas agosto a novembro; 4 datas invalidas "
            "foram excluidas e todos os status entram, entao nao se trata de "
            "receita nem de vendas concluidas. Nao e possivel provar causalidade."
        )

    print("\n" + "=" * 78)
    print("Observacao final: as contagens representam pedidos registrados,")
    print("nao receita ou vendas concluidas. O CSV original nao foi alterado.")
    print("=" * 78)


def main(caminho_csv: str | Path = ARQUIVO_PADRAO) -> int:
    """Carrega os dados e gera o relatorio. Retorna 0 em caso de sucesso."""
    df, nulos = carregar_dados(caminho_csv)
    imprimir_relatorio(df, nulos)
    return 0


def criar_parser() -> argparse.ArgumentParser:
    """Configura a interface de linha de comando."""
    parser = argparse.ArgumentParser(
        description=(
            "Le e analisa halloween_vendas.csv sem alterar o arquivo original."
        )
    )
    parser.add_argument(
        "csv",
        nargs="?",
        default=str(ARQUIVO_PADRAO),
        help=(
            "Caminho do CSV. Por padrao, usa halloween_vendas.csv na mesma "
            "pasta deste script."
        ),
    )
    return parser


def cli(argv: list[str] | None = None) -> int:
    """Ponto de entrada com tratamento amigavel de erros de arquivo/coluna."""
    args = criar_parser().parse_args(argv)
    try:
        return main(args.csv)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(cli())
