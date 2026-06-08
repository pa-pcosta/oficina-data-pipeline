import os
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


def main() -> None:
    base = Path(os.environ["DOWNLOAD_BASE_SELENIUM"])
    hoje = date.today().isoformat()
    caminho_itens    = base / "itens_ordens_de_servico" / f"{hoje}.csv"
    caminho_produtos = base / "produtos"                / f"{hoje}.csv"
    caminho_servicos = base / "servicos"                / f"{hoje}.csv"
    destino = base.parent.parent / "transform" / "itens_ordens_de_servico.csv"
    destino.parent.mkdir(parents=True, exist_ok=True)

    df = transformar(caminho_itens, caminho_produtos, caminho_servicos)
    df.to_csv(destino, index=False, encoding="utf-8-sig")
    print(f"[OK] {len(df)} registros salvos em {destino}")


def transformar(caminho_itens: Path, caminho_produtos: Path, caminho_servicos: Path) -> pd.DataFrame:
    df       = pd.read_csv(caminho_itens,    sep=";", encoding="utf-8-sig", dtype=str)
    produtos = pd.read_csv(caminho_produtos, sep=";", encoding="utf-8-sig", dtype=str, usecols=["id_produto", "descricao"])
    servicos = pd.read_csv(caminho_servicos, sep=";", encoding="utf-8-sig", dtype=str, usecols=["id_servico", "servico"])

    produtos["id_produto"] = pd.to_numeric(produtos["id_produto"], errors="coerce")
    servicos["id_servico"] = pd.to_numeric(servicos["id_servico"], errors="coerce")
    # {id: descricao_normalizada} para lookup por id+descricao simultaneamente
    map_produtos = dict(zip(produtos["id_produto"], produtos["descricao"].str.strip().str.upper()))
    map_servicos = dict(zip(servicos["id_servico"], servicos["servico"].str.strip().str.upper()))

    df["nk_ordem_servico"] = pd.to_numeric(df["Ordem de servico"],        errors="coerce")
    df["nk_codigo_origem"] = pd.to_numeric(df["Codigo Produtos Servicos"], errors="coerce")
    df["descricao"]        = df["Descricao Produtos Servicos"]
    df["quantidade"]       = df["Quantidade"].apply(limpar_valor)
    df["vl_unitario"]      = df["Valor Unitario"].apply(limpar_valor)
    df["vl_total"]         = df["Total"].apply(limpar_valor)
    df["vl_desconto"]      = df["Desconto Produtos Servicos"].apply(limpar_valor)
    df["fl_aprovado"]      = df["Aprovado"].map({"Aprovado": True})
    df["tipo"]             = df.apply(
        lambda row: inferir_tipo(row["nk_codigo_origem"], row["descricao"], map_produtos, map_servicos),
        axis=1,
    )

    df = df[[
        "nk_ordem_servico", "nk_codigo_origem", "tipo", "descricao",
        "quantidade", "vl_unitario", "vl_total", "vl_desconto", "fl_aprovado",
    ]]

    df = df.where(pd.notna(df), None)
    df = df.dropna(subset=["nk_ordem_servico", "descricao"])

    return df


def inferir_tipo(codigo, descricao: str, map_produtos: dict, map_servicos: dict) -> str | None:
    try:
        c = int(codigo)
    except (TypeError, ValueError):
        return None
    if not descricao or pd.isna(descricao):
        return None
    desc = str(descricao).strip().upper()
    if map_produtos.get(c) == desc:
        return "produto"
    if map_servicos.get(c) == desc:
        return "servico"
    return None


def limpar_valor(valor: str) -> float | None:
    if pd.isna(valor):
        return None
    limpo = re.sub(r"R\$\s*", "", str(valor)).replace(".", "").replace(",", ".")
    try:
        return float(limpo)
    except ValueError:
        return None


if __name__ == "__main__":
    main()
