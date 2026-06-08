import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


def main() -> None:
    caminho_csv = Path(os.environ["DOWNLOAD_BASE_SELENIUM"]) / "clientes" / f"{date.today().isoformat()}.csv"
    destino = Path(os.environ["DOWNLOAD_BASE_SELENIUM"]).parent.parent / "transform" / "clientes.csv"
    destino.parent.mkdir(parents=True, exist_ok=True)

    df = transformar(caminho_csv)
    df.to_csv(destino, index=False, encoding="utf-8-sig")
    print(f"[OK] {len(df)} registros salvos em {destino}")


def transformar(caminho_csv: Path) -> pd.DataFrame:
    df = pd.read_csv(caminho_csv, sep=";", encoding="utf-8-sig", dtype=str)

    df = df.rename(columns={
        "id_cliente":    "nk_cliente",
        "nome":          "nome",
        "bairro":        "bairro",
        "cidade":        "cidade",
        "uf":            "uf",
        "cpf":           "cpf",
        "cnpj":          "cnpj",
        "pessoa":        "fl_tipo_pessoa",
        "datacadastro":  "dt_cadastro",
        "datanascimento": "dt_nascimento",
    })

    df = df[[
        "nk_cliente", "nome", "bairro", "cidade", "uf",
        "cpf", "cnpj", "fl_tipo_pessoa", "dt_cadastro", "dt_nascimento",
    ]]

    df["nk_cliente"]     = pd.to_numeric(df["nk_cliente"], errors="coerce")
    df["fl_tipo_pessoa"] = df["fl_tipo_pessoa"].map({"1": "PF", "2": "PJ"})
    df["dt_cadastro"]    = pd.to_datetime(df["dt_cadastro"], dayfirst=True, errors="coerce").dt.strftime("%Y-%m-%d")
    df["dt_nascimento"]  = pd.to_datetime(df["dt_nascimento"], dayfirst=True, errors="coerce").dt.strftime("%Y-%m-%d")

    df = df.where(pd.notna(df), None)
    df = df.dropna(subset=["nk_cliente"])

    return df


if __name__ == "__main__":
    main()
