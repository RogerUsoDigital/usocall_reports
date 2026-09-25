"""Job executável por cron: monitora erros altos dos lotes UsoCall."""

from datetime import date
import logging

from repositories.monitoramento_repository import MonitoramentoRepository
from repositories.report_repository import ReportRepository
from services.notifier import Notifier


logger = logging.getLogger(__name__)


def main() -> dict[str, int]:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    logger.info("Iniciando monitoramento de reports")
    novos = ignorados = erros = 0

    try:
        report_repository = ReportRepository()
        monitoramento_repository = MonitoramentoRepository()
        notifier = Notifier()
        # para teste: passar a data de incidente
        # reports = report_repository.buscar_relatorios_do_dia(date(2026, 9, 24))
        reports = report_repository.buscar_relatorios_do_dia()
        logger.info("%s reports encontrados", len(reports))
    except Exception:
        logger.exception("Não foi possível iniciar o monitoramento de reports")
        raise

    for report in reports:
        logger.info("Processando lote %s", report.lote_id)
        try:
            if monitoramento_repository.ja_registrado(report.lote_id, "erro_alto"):
                ignorados += 1
                logger.info("Lote %s já reconhecido", report.lote_id)
                continue

            monitor_id = monitoramento_repository.criar_alerta(report, "erro_alto")
            if monitor_id is None:  # proteção contra corrida com outra execução
                ignorados += 1
                continue
            novos += 1
            logger.info("Novo alerta criado para lote %s", report.lote_id)
        except Exception:
            erros += 1
            logger.exception("Erro ao registrar alerta do lote %s", report.lote_id)
            continue

        try:
            notifier.enviar_alerta(report)
        except Exception as exc:
            erros += 1
            logger.exception("Erro ao enviar alerta do lote %s", report.lote_id)
            try:
                monitoramento_repository.marcar_como_erro(monitor_id, str(exc))
            except Exception:
                logger.exception("Erro ao registrar falha do alerta do lote %s", report.lote_id)
            continue

        try:
            monitoramento_repository.marcar_como_enviado(monitor_id)
            logger.info("Alerta enviado para lote %s", report.lote_id)
        except Exception:
            erros += 1
            # O webhook já aceitou o alerta; não o marcamos como erro para evitar reenvio indevido.
            logger.exception("Alerta do lote %s foi enviado, mas não foi possível atualizar seu status", report.lote_id)

    resultado = {"novos": novos, "ignorados": ignorados, "erros": erros}
    logger.info("Processamento finalizado. Novos: %(novos)s; Ignorados: %(ignorados)s; Erros: %(erros)s", resultado)
    return resultado


if __name__ == "__main__":
    main()
