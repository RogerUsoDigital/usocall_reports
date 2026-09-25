"""Envio de alertas de relatórios ao webhook configurado."""

from datetime import date, datetime
from typing import Any

import requests

from config.settings import ALERT_WEBHOOK_TIMEOUT, ALERT_WEBHOOK_URL
from repositories.report_repository import Report


class Notifier:
    def __init__(self, webhook_url: str | None = None, timeout: int | None = None):
        self.webhook_url = webhook_url or ALERT_WEBHOOK_URL
        self.timeout = timeout or ALERT_WEBHOOK_TIMEOUT
        if not self.webhook_url:
            raise ValueError("ALERT_WEBHOOK_URL não foi configurada")

    def enviar_alerta(self, report: Report) -> dict[str, Any]:
        response = requests.post(
            self.webhook_url,
            json=self._montar_payload(report),
            headers={"Content-Type": "application/json"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        try:
            corpo: Any = response.json()
        except ValueError:
            corpo = response.text
        return {"status_code": response.status_code, "response": corpo}

    @staticmethod
    def _montar_payload(report: Report) -> dict[str, Any]:
        return {
            "tipo_alerta": "erro_alto",
            "lote_id": report.lote_id,
            "cliente": report.cliente_nome,
            "arquivo": report.arquivo,
            "data_lote": Notifier._serializar(report.data_lote),
            "percentual_erro": float(report.percentual_erro),
            "total": report.total,
            "erro": report.erro,
            "sucesso": report.sucesso,
            "discando": report.discando,
            "pendente": report.pendente,
            "enviado_meta": report.enviado_meta,
            "entregue_meta": report.entregue_meta,
            "lidos_meta": report.lidos_meta,
            "erro_meta": report.erro_meta,
        }

    @staticmethod
    def _serializar(valor: date | datetime | None) -> str | None:
        return valor.isoformat(sep=" ") if isinstance(valor, datetime) else (
            valor.isoformat() if isinstance(valor, date) else None
        )
