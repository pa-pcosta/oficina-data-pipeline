import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from dotenv import load_dotenv, find_dotenv
from supabase import create_client

load_dotenv(find_dotenv())

LOTE = 500


def main() -> None:
    base = Path(os.environ["DOWNLOAD_BASE_SELENIUM"])
    caminho_csv = base.parent.parent / "transform" / "motocicletas.csv"

    sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
    df = pd.read_csv(caminho_csv, encoding="utf-8-sig", dtype=str)

    carregar(df, sb)


def carregar(df: pd.DataFrame, sb) -> None:
    df["nk_motocicleta"] = df["nk_motocicleta"].apply(para_inteiro)
    df = df.astype(object).where(pd.notnull(df), None)

    registros = [sanitizar(r) for r in df.to_dict(orient="records")]
    total = len(registros)

    for i in range(0, total, LOTE):
        lote = registros[i:i + LOTE]
        sb.table("dim_motocicleta").upsert(lote, on_conflict="nk_motocicleta").execute()
        print(f"[OK] {min(i + LOTE, total)}/{total} motocicletas carregadas")

    print(f"\n[OK] dim_motocicleta: {total} registros")


def sanitizar(registro: dict) -> dict:
    import math
    resultado = {}
    for k, v in registro.items():
        if v is None:
            resultado[k] = None
        elif isinstance(v, float):
            if math.isnan(v):
                resultado[k] = None
            elif v == int(v):
                resultado[k] = int(v)
            else:
                resultado[k] = v
        else:
            resultado[k] = v
    return resultado


def para_inteiro(valor) -> int | None:
    try:
        return int(float(valor))
    except (TypeError, ValueError):
        return None


if __name__ == "__main__":
    main()
