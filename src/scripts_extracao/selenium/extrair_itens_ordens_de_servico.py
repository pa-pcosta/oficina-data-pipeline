import csv
import json
import os
import sys
import glob
import time
import shutil
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv, find_dotenv
from logs.logger import LoggerExtracao
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager

# ── Carregar variáveis de ambiente ───────────────────────────────────────────
load_dotenv(find_dotenv())

URL_LOGIN         = os.environ["SISTEMA_LOGIN_URL"]
ID_OFICINA        = os.environ["SISTEMA_ID_OFICINA"]
USUARIO           = os.environ["SISTEMA_USUARIO"]
SENHA             = os.environ["SISTEMA_SENHA"]

URL_RELATORIO     = os.environ["SISTEMA_BASE_URL"] + "/P_LISTAR_OS.ASP"

DIRETORIO_DESTINO = os.path.join(os.environ["DOWNLOAD_BASE_SELENIUM"], "itens_ordens_de_servico")

NOME_ARQUIVO = f"{date.today().isoformat()}.csv"


# ── Configuração do navegador e download ─────────────────────────────────────
def configurar_navegador(diretorio_destino: str) -> webdriver.Chrome:
    os.makedirs(diretorio_destino, exist_ok=True)
    options = Options()
    options.add_experimental_option("prefs", {
        "download.default_directory": os.path.abspath(diretorio_destino),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    })
    # options.add_argument("--headless")
    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options,
    )


def aguardar_carregamento_resultados(espera: WebDriverWait) -> None:
    espera.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".swal2-container")))


def aguardar_download_e_renomear_arquivo(diretorio_destino: str, nome_final: str, timeout: int = 30) -> str:
    inicio = time.time()
    while True:
        arquivos = [
            f for f in glob.glob(os.path.join(diretorio_destino, "*.csv"))
            if not f.endswith(".crdownload")
        ]
        if arquivos:
            arquivo_baixado = max(arquivos, key=os.path.getctime)
            destino = os.path.join(diretorio_destino, nome_final)
            shutil.move(arquivo_baixado, destino)
            return destino
        if time.time() - inicio > timeout:
            raise TimeoutError(f"Download não concluído em {timeout}s")
        time.sleep(0.5)


# ── Extração ─────────────────────────────────────────────────────────────────
def main() -> None:
    from logs.logger_csv import LoggerCSV
    executar_extracao(LoggerCSV(metodo="selenium"))


def executar_extracao(logger: LoggerExtracao, data_inicio: str = None, data_fim: str = None, tipo: str = "incremental") -> None:
    navegador = configurar_navegador(DIRETORIO_DESTINO)
    espera    = WebDriverWait(navegador, 15)

    try:
        # 1. Login
        navegador.get(URL_LOGIN)
        espera.until(EC.presence_of_element_located((By.ID, "chave"))).send_keys(ID_OFICINA)
        time.sleep(0.5)
        navegador.find_element(By.ID, "usuario").send_keys(USUARIO)
        time.sleep(0.5)
        navegador.find_element(By.ID, "senha").send_keys(SENHA)
        time.sleep(0.5)
        navegador.find_element(By.ID, "btnLogar").click()
        espera.until(lambda d: "login" not in d.current_url.lower())

        # 2. Navegar até o relatório
        navegador.get(URL_RELATORIO)

        # 3. Selecionar filtro por data de saída
        select = Select(espera.until(EC.presence_of_element_located((By.ID, "DATA_TIPO"))))
        select.select_by_value("2")

        # 4. Preencher datas (se None, deixa em branco — sistema retorna tudo)
        if data_inicio:
            navegador.find_element(By.ID, "DATA_INICIAL").send_keys(data_inicio)
            time.sleep(0.5)
        if data_fim:
            navegador.find_element(By.ID, "DATA_FINAL").send_keys(data_fim)
            time.sleep(0.5)

        # 5. Buscar — sem isso o export ignora o filtro e baixa todos os itens
        navegador.execute_script("buscarOrdensServico();")
        aguardar_carregamento_resultados(espera)

        # 6. Exportar detalhado (itens por OS, encoding cp1252)
        navegador.execute_script("exportarCSVDetalhado();")

        # 7. Aguardar download, renomear e confirmar
        caminho = aguardar_download_e_renomear_arquivo(DIRETORIO_DESTINO, NOME_ARQUIVO)
        with open(caminho, encoding="utf-8-sig", newline="") as _f:
            registros_retornados = sum(1 for _ in csv.reader(_f, delimiter=";")) - 1
        detalhes = json.dumps({"tipo": tipo, "periodo_consulta": {"data_inicio": data_inicio, "data_fim": data_fim}})
        logger.registrar_sucesso("itens_ordens_de_servico", caminho, registros_retornados, detalhes)
        print(f"[OK] Arquivo salvo em: {caminho}")
        if data_inicio or data_fim:
            print(f"[OK] Período extraído: {data_inicio} → {data_fim}")

    except Exception as e:
        logger.registrar_erro("itens_ordens_de_servico", str(e))
        raise
    finally:
        navegador.quit()


if __name__ == "__main__":
    main()
