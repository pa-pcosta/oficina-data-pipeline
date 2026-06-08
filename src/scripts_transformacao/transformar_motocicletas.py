import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


def main() -> None:
    caminho_csv = Path(os.environ["DOWNLOAD_BASE_SELENIUM"]) / "motocicletas" / f"{date.today().isoformat()}.csv"
    destino = Path(os.environ["DOWNLOAD_BASE_SELENIUM"]).parent.parent / "transform" / "motocicletas.csv"
    destino.parent.mkdir(parents=True, exist_ok=True)

    df = transformar(caminho_csv)
    df.to_csv(destino, index=False, encoding="utf-8-sig")
    print(f"[OK] {len(df)} registros salvos em {destino}")


def transformar(caminho_csv: Path) -> pd.DataFrame:
    df = pd.read_csv(caminho_csv, sep=";", encoding="utf-8-sig", dtype=str)

    df = df.rename(columns={
        "id_veiculo": "nk_motocicleta",
        "Placa":      "placa",
        "Marca":      "marca",
        "Modelo":     "modelo",
        "Versao":     "versao",
        "Cor":        "cor",
        "ano":        "ano",
        "Chassi":     "chassi",
    })

    df = df[[
        "nk_motocicleta", "placa", "marca", "modelo",
        "versao", "cor", "ano", "chassi",
    ]]

    df["nk_motocicleta"] = pd.to_numeric(df["nk_motocicleta"], errors="coerce")
    df["ano"]            = df["ano"].apply(extrair_ano_modelo)

    df = df.where(pd.notna(df), None)
    df = df.dropna(subset=["nk_motocicleta"])

    return df


def extrair_ano_modelo(valor) -> str | None:
    if not valor or pd.isna(valor):
        return None
    partes = str(valor).split("|")
    # prefere ano_modelo (2º parte), fallback para ano_fabricacao (1ª parte)
    ano_raw = partes[1].strip() if len(partes) > 1 and partes[1].strip() else partes[0].strip()
    if not ano_raw or ano_raw == "0":
        return None
    try:
        yy = int(ano_raw)
    except ValueError:
        return None
    # 2 dígitos → 4 dígitos: >= 40 considera 1900s (ex: 89 → 1989), < 40 considera 2000s (ex: 15 → 2015)
    return str(1900 + yy if yy >= 40 else 2000 + yy)


if __name__ == "__main__":
    main()
