"""Configurações centralizadas da rotina de monitoramento."""

import os
from pathlib import Path

from dotenv import load_dotenv


# Carrega sempre o .env da raiz do projeto, independentemente de onde o job foi chamado.
load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def _database_config(prefix: str, legacy_prefix: str | None = None) -> dict:
    """Monta a configuração de um banco aceitando o prefixo legado, se houver."""
    def get(name: str, default: str | None = None) -> str | None:
        return os.getenv(f"{prefix}_{name}") or (
            os.getenv(f"{legacy_prefix}_{name}") if legacy_prefix else None
        ) or default

    return {
        "host": get("HOST"),
        "port": int(get("PORT", "3306")),
        "database": get("NAME"),
        "user": get("USER"),
        "password": get("PASSWORD"),
    }


USOCALL_DB_CONFIG = _database_config("USOCALL_DB")
# MONITOR_DB_* é aceito temporariamente para não quebrar instalações existentes.
MONITORAMENTO_DB_CONFIG = _database_config("MONITORAMENTO_DB", "MONITOR_DB")

ALERT_WEBHOOK_URL = os.getenv("ALERT_WEBHOOK_URL")
ALERT_WEBHOOK_TIMEOUT = int(os.getenv("ALERT_WEBHOOK_TIMEOUT", "30"))
