import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from dotenv import load_dotenv, find_dotenv
from supabase import create_client

load_dotenv(find_dotenv())

LOTE = 200


def main() -> None:
    base = Path(os.environ["DOWNLOAD_BASE_SELENIUM"])
    caminho_csv = base.parent.parent / "transform" / "ordens_de_servico.csv"

    sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
    df = pd.read_csv(caminho_csv, encoding="utf-8-sig", dtype=str)

    carregar(df, sb)


def carregar(df: pd.DataFrame, sb) -> None:
    # apenas OS finalizadas entram no DW
    df = df[df["dt_saida"].notna()].copy()
    df["nk_ordem_de_servico"] = df["nk_ordem_de_servico"].apply(para_inteiro)
    df["nk_cliente"]          = df["nk_cliente"].apply(para_inteiro)
    df["km_motocicleta"]      = df["km_motocicleta"].apply(para_inteiro)

    # sk_data a partir de "YYYY-MM-DD" → int YYYYMMDD
    df["data_inclusao"] = df["dt_inclusao"].apply(data_para_sk)
    df["data_saida"]    = df["dt_saida"].apply(data_para_sk)

    df = df.astype(object).where(pd.notnull(df), None)

    # lookup bulk: nk_cliente → sk_cliente
    nk_clientes = df["nk_cliente"].dropna().astype(int).unique().tolist()
    mapa_cliente = buscar_sk(sb, "dim_cliente", "nk_cliente", "sk_cliente", nk_clientes)

    # lookup bulk: placa → sk_motocicleta
    placas = df["placa"].dropna().unique().tolist()
    mapa_moto = buscar_sk(sb, "dim_motocicleta", "placa", "sk_motocicleta", placas)

    registros = []
    sem_cliente = 0
    for _, row in df.iterrows():
        sk_cliente = mapa_cliente.get(row["nk_cliente"])
        if sk_cliente is None:
            sem_cliente += 1
            continue

        registros.append(sanitizar({
            "nk_ordem_de_servico": row["nk_ordem_de_servico"],
            "sk_cliente":          sk_cliente,
            "sk_motocicleta":      mapa_moto.get(row["placa"]),
            "km_motocicleta":      row["km_motocicleta"],
            "data_inclusao":       row["data_inclusao"],
            "data_saida":          row["data_saida"],
            "valor_total":         row["valor_total"],
            "valor_desconto":      row["valor_desconto"],
        }))

    if sem_cliente:
        print(f"[AVISO] {sem_cliente} OS ignoradas — nk_cliente não encontrado em dim_cliente")

    total = len(registros)
    for i in range(0, total, LOTE):
        lote = registros[i:i + LOTE]
        sb.table("fact_ordem_de_servico").upsert(lote, on_conflict="nk_ordem_de_servico").execute()
        print(f"[OK] {min(i + LOTE, total)}/{total} ordens carregadas")

    print(f"\n[OK] fact_ordem_de_servico: {total} registros")


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


def buscar_sk(sb, tabela: str, col_nk: str, col_sk: str, valores: list) -> dict:
    if not valores:
        return {}
    result = sb.table(tabela).select(f"{col_sk}, {col_nk}").in_(col_nk, valores).execute()
    return {row[col_nk]: row[col_sk] for row in result.data}


def data_para_sk(valor: str) -> int | None:
    if not valor or pd.isna(valor):
        return None
    return int(str(valor).replace("-", ""))


def para_inteiro(valor) -> int | None:
    try:
        return int(float(valor))
    except (TypeError, ValueError):
        return None


if __name__ == "__main__":
    main()
