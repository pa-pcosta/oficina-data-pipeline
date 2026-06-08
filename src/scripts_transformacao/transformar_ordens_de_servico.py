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
    caminho_csv = base / "ordens_de_servico" / f"{date.today().isoformat()}.csv"
    destino = base.parent.parent / "transform" / "ordens_de_servico.csv"
    destino.parent.mkdir(parents=True, exist_ok=True)

    df = transformar(caminho_csv)
    df.to_csv(destino, index=False, encoding="utf-8-sig")
    print(f"[OK] {len(df)} registros salvos em {destino}")


def transformar(caminho_csv: Path) -> pd.DataFrame:
    df = pd.read_csv(caminho_csv, sep=";", encoding="utf-8-sig", dtype=str, on_bad_lines="skip")

    df["nk_ordem_de_servico"] = pd.to_numeric(df["Ordem de servico"], errors="coerce")
    # "12 - GUSTAVO XAVIER" → 12
    df["nk_cliente"]     = df["Cliente"].str.extract(r"^(\d+)\s*-").squeeze()
    df["nk_cliente"]     = pd.to_numeric(df["nk_cliente"], errors="coerce")
    df["placa"]          = df["Placa"]
    df["km_motocicleta"] = pd.to_numeric(df["Km"], errors="coerce")
    df["dt_inclusao"]    = pd.to_datetime(df["Data Inclusao"], dayfirst=True, errors="coerce").dt.strftime("%Y-%m-%d")
    df["dt_saida"]       = pd.to_datetime(df["Saida"], dayfirst=True, errors="coerce").dt.strftime("%Y-%m-%d")
    df["valor_total"]    = df["Total"].apply(limpar_valor)
    df["valor_desconto"] = df["Desconto"].apply(limpar_valor)

    df = df[[
        "nk_ordem_de_servico", "nk_cliente", "placa",
        "km_motocicleta", "dt_inclusao", "dt_saida",
        "valor_total", "valor_desconto",
    ]]

    df = df.where(pd.notna(df), None)
    df = df.dropna(subset=["nk_ordem_de_servico"])
    df = df[df["nk_ordem_de_servico"] != 1]  # exclui OS de exemplo do ERP

    return df


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
