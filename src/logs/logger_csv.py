import csv
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


class LoggerCSV:
    def __init__(self, metodo: str):
        destino = os.environ["DESTINO_LOGS"]
        os.makedirs(destino, exist_ok=True)
        self.metodo = metodo
        self.caminho_log = os.path.join(destino, "historico_extracoes.csv")
        self._garantir_cabecalho()

    def _garantir_cabecalho(self) -> None:
        if not Path(self.caminho_log).exists():
            with open(self.caminho_log, "w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(
                    ["timestamp", "metodo", "entidade", "status", "registros_retornados", "caminho_destino", "detalhes", "erro"]
                )

    def registrar_sucesso(self, entidade: str, caminho: str, registros_retornados: int, detalhes: str = "{}") -> None:
        self._escrever(entidade, "sucesso", caminho, registros_retornados, detalhes, "")

    def registrar_erro(self, entidade: str, erro: str) -> None:
        self._escrever(entidade, "erro", "", 0, "{}", erro)

    def _escrever(self, entidade: str, status: str, caminho: str, registros_retornados: int, detalhes: str, erro: str) -> None:
        with open(self.caminho_log, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([
                datetime.now().isoformat(timespec="seconds"),
                self.metodo,
                entidade,
                status,
                registros_retornados,
                caminho,
                detalhes,
                erro,
            ])
