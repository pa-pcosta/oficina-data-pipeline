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

    df = df.where(pd.notna(df), None)
    df = df.dropna(subset=["nk_motocicleta"])

    return df


if __name__ == "__main__":
    main()
