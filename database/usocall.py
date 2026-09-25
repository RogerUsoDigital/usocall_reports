"""Conexão somente leitura com o banco UsoCall."""

import logging

import mysql.connector

from config.settings import USOCALL_DB_CONFIG


logger = logging.getLogger(__name__)


def obter_conexao():
    """Abre e devolve uma conexão nova com o banco UsoCall."""
    try:
        return mysql.connector.connect(**USOCALL_DB_CONFIG)
    except mysql.connector.Error as exc:
        logger.exception("Não foi possível conectar ao banco UsoCall")
        raise RuntimeError("Falha ao conectar ao banco UsoCall") from exc
