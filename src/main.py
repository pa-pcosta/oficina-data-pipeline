import argparse
import importlib.util
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from logs.logger_csv import LoggerCSV

DIRETORIO_SRC           = Path(__file__).parent
DIRETORIO_EXTRACAO      = DIRETORIO_SRC / "scripts_extracao" / "selenium"
DIRETORIO_TRANSFORMACAO = DIRETORIO_SRC / "scripts_transformacao"
DIRETORIO_CARREGAMENTO  = DIRETORIO_SRC / "scripts_carregamento"

# entidades que seguem o fluxo completo até o DW, na ordem de carga (respeita as FKs).
# produtos e servicos são extraídos, mas servem apenas de lookup na transformação de itens.
ENTIDADES_DW = ["clientes", "motocicletas", "ordens_de_servico", "itens_ordens_de_servico"]


def main() -> None:
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

    print("\n══════════ EXTRAÇÃO ══════════")
    for script in sorted(DIRETORIO_EXTRACAO.glob("extrair_*.py")):
        print(f"\n[→] {script.name}...")
        importar_script(script).executar_extracao(logger, data_inicio=data_inicio, data_fim=data_fim, tipo=tipo)
        print(f"[OK] {script.name} concluído")

    print("\n══════════ TRANSFORMAÇÃO + CARREGAMENTO ══════════")
    for entidade in ENTIDADES_DW:
        print(f"\n[→] {entidade}...")
        importar_script(DIRETORIO_TRANSFORMACAO / f"transformar_{entidade}.py").main()
        importar_script(DIRETORIO_CARREGAMENTO / f"carregar_{entidade}.py").main()
        print(f"[OK] {entidade} concluído")

    print("\n✓ Pipeline finalizado.")


def importar_script(caminho: Path):
    especificacao_modulo = importlib.util.spec_from_file_location(caminho.stem, caminho)
    modulo = importlib.util.module_from_spec(especificacao_modulo)
    especificacao_modulo.loader.exec_module(modulo)
    return modulo


if __name__ == "__main__":
    main()
