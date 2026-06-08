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
    caminho_csv = base.parent.parent / "transform" / "itens_ordens_de_servico.csv"

    sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
    df = pd.read_csv(caminho_csv, encoding="utf-8-sig", dtype=str)

    carregar(df, sb)


def carregar(df: pd.DataFrame, sb) -> None:
    df["nk_ordem_servico"]  = df["nk_ordem_servico"].apply(para_inteiro)
    df["nk_codigo_origem"]  = df["nk_codigo_origem"].apply(para_inteiro)
    df = df.astype(object).where(pd.notnull(df), None)

    # lookup bulk: nk_ordem_servico → sk_ordem_servico
    nk_os_list = df["nk_ordem_servico"].dropna().astype(int).unique().tolist()
    result = sb.table("fact_ordem_de_servico") \
               .select("sk_ordem_de_servico, nk_ordem_de_servico") \
               .in_("nk_ordem_de_servico", nk_os_list) \
               .execute()
    mapa_os = {row["nk_ordem_de_servico"]: row["sk_ordem_de_servico"] for row in result.data}

    # apenas itens cujas OS já estão no DW
    df = df[df["nk_ordem_servico"].isin(mapa_os.keys())].copy()

    if df.empty:
        print("[OK] Nenhum item para carregar.")
        return

    # idempotência: remove itens existentes das OS que vamos reinserir
    os_no_dw = list(mapa_os.keys())
    sb.table("fact_item_os").delete().in_("nk_ordem_servico", os_no_dw).execute()

    registros = []
    for _, row in df.iterrows():
        registros.append(sanitizar({
            "sk_ordem_servico":  mapa_os[row["nk_ordem_servico"]],
            "nk_ordem_servico":  row["nk_ordem_servico"],
            "tipo":              row["tipo"],
            "nk_codigo_origem":  row["nk_codigo_origem"],
            "descricao":         row["descricao"],
            "quantidade":        row["quantidade"],
            "vl_unitario":       row["vl_unitario"],
            "vl_total":          row["vl_total"],
            "vl_desconto":       row["vl_desconto"],
            "fl_aprovado":       row["fl_aprovado"],
        }))

    total = len(registros)
    for i in range(0, total, LOTE):
        lote = registros[i:i + LOTE]
        sb.table("fact_item_os").insert(lote).execute()
        print(f"[OK] {min(i + LOTE, total)}/{total} itens carregados")

    print(f"\n[OK] fact_item_os: {total} registros")


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
