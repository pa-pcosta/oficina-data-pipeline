import csv
import io
from datetime import date, datetime

from storage.bucket import enviar

CABECALHO = ["timestamp", "metodo", "entidade", "status", "registros_retornados", "caminho_destino", "detalhes", "erro"]


class LoggerCSV:
    def __init__(self, metodo: str):
        self.metodo = metodo
        self.nome_arquivo = f"{date.today().isoformat()}.csv"
        self.linhas = [CABECALHO]

    def registrar_sucesso(self, entidade: str, caminho: str, registros_retornados: int, detalhes: str = "{}") -> None:
        self._escrever(entidade, "sucesso", caminho, registros_retornados, detalhes, "")

    def registrar_erro(self, entidade: str, erro: str) -> None:
        self._escrever(entidade, "erro", "", 0, "{}", erro)

    def _escrever(self, entidade: str, status: str, caminho: str, registros_retornados: int, detalhes: str, erro: str) -> None:
        self.linhas.append([
            datetime.now().isoformat(timespec="seconds"),
            self.metodo,
            entidade,
            status,
            registros_retornados,
            caminho,
            detalhes,
            erro,
        ])
        buffer = io.StringIO()
        csv.writer(buffer).writerows(self.linhas)
        enviar(buffer.getvalue().encode("utf-8"), f"logs/{self.nome_arquivo}")
