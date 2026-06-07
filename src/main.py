import argparse
import importlib.util
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from logs.logger_csv import LoggerCSV

DIRETORIO_SCRIPTS = Path(__file__).parent / "scripts_selenium"


def importar_script(caminho: Path):
    especificacao_modulo = importlib.util.spec_from_file_location(caminho.stem, caminho)
    modulo = importlib.util.module_from_spec(especificacao_modulo)
    especificacao_modulo.loader.exec_module(modulo)
    return modulo


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--carga-inicial", action="store_true")
    args = parser.parse_args()

    if args.carga_inicial:
        tipo = "carga_completa"
        data_inicio = None
        data_fim = None
    else:
        tipo = "incremental"
        hoje = date.today()
        ultimo_sabado = hoje - timedelta(days=(hoje.weekday() + 2) % 7 or 7)
        data_inicio = (ultimo_sabado - timedelta(days=6)).strftime("%d/%m/%Y")
        data_fim = ultimo_sabado.strftime("%d/%m/%Y")

    logger = LoggerCSV(metodo="selenium")

    for script in DIRETORIO_SCRIPTS.glob("*.py"):
        print(f"\n[→] Iniciando {script.name}...")
        importar_script(script).executar_extracao(logger, data_inicio=data_inicio, data_fim=data_fim, tipo=tipo)
        print(f"[OK] {script.name} concluído")
