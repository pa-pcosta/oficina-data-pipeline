import os
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv, find_dotenv
from supabase import create_client

load_dotenv(find_dotenv())

MESES = {
    1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril",
    5: "maio", 6: "junho", 7: "julho", 8: "agosto",
    9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro",
}

DIAS_SEMANA = {
    0: "segunda-feira", 1: "terça-feira", 2: "quarta-feira",
    3: "quinta-feira", 4: "sexta-feira", 5: "sábado", 6: "domingo",
}

DATA_INICIO = date(2024, 1, 1)
DATA_FIM    = date(2040, 12, 31)
LOTE        = 500


def main() -> None:
    supabase = create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_KEY"],
    )

    registros = gerar_registros(DATA_INICIO, DATA_FIM)
    total = len(registros)

    for i in range(0, total, LOTE):
        lote = registros[i:i + LOTE]
        supabase.table("dim_data").upsert(lote).execute()
        print(f"[OK] {min(i + LOTE, total)}/{total} registros inseridos")

    print(f"\n[OK] dim_data populada com {total} datas ({DATA_INICIO} → {DATA_FIM})")


def gerar_registros(data_inicio: date, data_fim: date) -> list[dict]:
    registros = []
    atual = data_inicio
    while atual <= data_fim:
        registros.append({
            "sk_data":          int(atual.strftime("%Y%m%d")),
            "dt_data_completa": atual.isoformat(),
            "nr_dia":           atual.day,
            "nr_mes":           atual.month,
            "nr_ano":           atual.year,
            "nr_trimestre":     (atual.month - 1) // 3 + 1,
            "nr_semana_ano":    atual.isocalendar()[1],
            "nm_mes":           MESES[atual.month],
            "nm_dia_semana":    DIAS_SEMANA[atual.weekday()],
            "fl_fim_semana":    atual.weekday() >= 5,
            "fl_feriado":       None,
        })
        atual += timedelta(days=1)
    return registros


if __name__ == "__main__":
    main()
