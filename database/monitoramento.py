"""Conexão de leitura e escrita com o banco de monitoramento."""

import logging

import mysql.connector

from config.settings import MONITORAMENTO_DB_CONFIG


logger = logging.getLogger(__name__)


def obter_conexao():
    """Abre e devolve uma conexão nova com o banco de monitoramento."""
    try:
        return mysql.connector.connect(**MONITORAMENTO_DB_CONFIG)
    except mysql.connector.Error as exc:
        logger.exception("Não foi possível conectar ao banco de monitoramento")
        raise RuntimeError("Falha ao conectar ao banco de monitoramento") from exc
