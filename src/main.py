import subprocess
import sys
from pathlib import Path

DIRETORIO_SCRIPTS = Path(__file__).parent / "selenium"

if __name__ == "__main__":
    scripts_de_extracao = DIRETORIO_SCRIPTS.glob("*.py")
    for script in scripts_de_extracao:
        print(f"\n[→] Iniciando {script.name}...")
        subprocess.run([sys.executable, str(script)], check=True)
        print(f"[OK] {script.name} concluído")
