import os
import glob
import time
import shutil
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ── Variáveis de ambiente ────────────────────────────────────────────────────
load_dotenv(Path(__file__).parent.parent / ".env")

LOGIN_URL    = os.environ["SISTEMA_LOGIN_URL"]
ID_OFICINA   = os.environ["SISTEMA_ID_OFICINA"]
USUARIO      = os.environ["SISTEMA_USUARIO"]
SENHA        = os.environ["SISTEMA_SENHA"]

RELATORIO_URL = os.environ["SISTEMA_BASE_URL"] + "/P_LISTAR_PLACAS.ASP"

DOWNLOAD_DIR = os.path.join(os.environ["DOWNLOAD_BASE"], "motocicletas")
NOME_ARQUIVO = f"{date.today().isoformat()}.csv"


# ── Utilitários ──────────────────────────────────────────────────────────────
def configurar_driver(download_dir: str) -> webdriver.Chrome:
    os.makedirs(download_dir, exist_ok=True)
    options = Options()
    options.add_experimental_option("prefs", {
        "download.default_directory": os.path.abspath(download_dir),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    })
    # options.add_argument("--headless")
    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options,
    )


def aguardar_e_renomear(download_dir: str, nome_final: str, timeout: int = 30) -> str:
    inicio = time.time()
    while True:
        arquivos = [
            f for f in glob.glob(os.path.join(download_dir, "*.csv"))
            if not f.endswith(".crdownload")
        ]
        if arquivos:
            arquivo_baixado = max(arquivos, key=os.path.getctime)
            destino = os.path.join(download_dir, nome_final)
            shutil.move(arquivo_baixado, destino)
            return destino
        if time.time() - inicio > timeout:
            raise TimeoutError(f"Download não concluído em {timeout}s")
        time.sleep(0.5)


# ── Extração ─────────────────────────────────────────────────────────────────
def run_extraction():
    driver = configurar_driver(DOWNLOAD_DIR)
    wait   = WebDriverWait(driver, 15)

    try:
        # 1. Login
        driver.get(LOGIN_URL)
        wait.until(EC.presence_of_element_located((By.ID, "chave"))).send_keys(ID_OFICINA)
        time.sleep(0.5)
        driver.find_element(By.ID, "usuario").send_keys(USUARIO)
        time.sleep(0.5)
        driver.find_element(By.ID, "senha").send_keys(SENHA)
        time.sleep(0.5)
        driver.find_element(By.ID, "btnLogar").click()
        wait.until(lambda d: "login" not in d.current_url.lower())

        # 2. Navegar até o relatório
        driver.get(RELATORIO_URL)

        # 3. Exportar — chama a função diretamente, sem abrir o dropdown
        driver.execute_script("exportarCSV();")

        # 4. Aguardar download, renomear e confirmar
        caminho = aguardar_e_renomear(DOWNLOAD_DIR, NOME_ARQUIVO)
        print(f"[OK] Arquivo salvo em: {caminho}")

    finally:
        driver.quit()


if __name__ == "__main__":
    run_extraction()
