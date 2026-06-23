import os
from dotenv import load_dotenv, find_dotenv
from supabase import create_client

load_dotenv(find_dotenv())

BUCKET = "raw"

_cliente = None


def enviar(conteudo: bytes, caminho_remoto: str) -> None:
    sb = _obter_cliente()
    sb.storage.from_(BUCKET).upload(
        path=caminho_remoto,
        file=conteudo,
        file_options={"content-type": "text/csv", "upsert": "true"},
    )


def _obter_cliente():
    global _cliente
    if _cliente is None:
        _cliente = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
    return _cliente
