import importlib.util
import sys
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
    
    logger = LoggerCSV(metodo="selenium")
    
    for script in DIRETORIO_SCRIPTS.glob("*.py"):
        print(f"\n[→] Iniciando {script.name}...")
        importar_script(script).executar_extracao(logger)
        print(f"[OK] {script.name} concluído")
