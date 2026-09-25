"""Persistência e controle de idempotência dos alertas de relatórios."""

import logging

import mysql.connector

from database.monitoramento import obter_conexao
from repositories.report_repository import Report


logger = logging.getLogger(__name__)


class MonitoramentoRepository:
    def ja_registrado(self, lote_id: int, tipo_alerta: str = "erro_alto") -> bool:
        # lote_id é UNIQUE; tipo_alerta é mantido na assinatura por compatibilidade.
        del tipo_alerta
        return self._buscar_id_por_lote(lote_id) is not None

    def criar_alerta(self, report: Report, tipo_alerta: str) -> int | None:
        """Cria um alerta pendente; retorna None se outro processo já o reconheceu."""
        sql = """
            INSERT INTO monitoramento_relatorios (
                lote_id, tipo_alerta, cliente_nome, arquivo, data_lote, percentual_erro,
                total, erro, sucesso, discando, pendente, enviado_meta, entregue_meta,
                lidos_meta, erro_meta, status_alerta, tentativas, criado_em, atualizado_em
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                'pendente', 0, NOW(), NOW()
            )
        """
        parametros = (
            report.lote_id, tipo_alerta, report.cliente_nome, report.arquivo,
            report.data_lote, report.percentual_erro, report.total, report.erro,
            report.sucesso, report.discando, report.pendente, report.enviado_meta,
            report.entregue_meta, report.lidos_meta, report.erro_meta,
        )
        conexao = obter_conexao()
        cursor = None
        try:
            cursor = conexao.cursor()
            cursor.execute(sql, parametros)
            conexao.commit()
            return cursor.lastrowid
        except mysql.connector.IntegrityError as exc:
            conexao.rollback()
            if exc.errno == 1062:
                logger.info("Lote %s já foi registrado por outra execução", report.lote_id)
                return None
            raise
        except Exception:
            conexao.rollback()
            raise
        finally:
            if cursor is not None:
                cursor.close()
            if conexao.is_connected():
                conexao.close()

    def marcar_como_enviado(self, monitor_id: int) -> None:
        self._atualizar_status(
            monitor_id,
            """UPDATE monitoramento_relatorios
               SET status_alerta = 'enviado', tentativas = tentativas + 1,
                   notificado_em = NOW(), ultimo_erro = NULL, atualizado_em = NOW()
               WHERE id = %s""",
            (monitor_id,),
        )

    def marcar_como_erro(self, monitor_id: int, erro: str) -> None:
        self._atualizar_status(
            monitor_id,
            """UPDATE monitoramento_relatorios
               SET status_alerta = 'erro', tentativas = tentativas + 1,
                   ultimo_erro = %s, atualizado_em = NOW()
               WHERE id = %s""",
            (erro[:2000], monitor_id),
        )

    def _buscar_id_por_lote(self, lote_id: int) -> int | None:
        conexao = obter_conexao()
        cursor = None
        try:
            cursor = conexao.cursor()
            cursor.execute("SELECT id FROM monitoramento_relatorios WHERE lote_id = %s", (lote_id,))
            linha = cursor.fetchone()
            return linha[0] if linha else None
        finally:
            if cursor is not None:
                cursor.close()
            if conexao.is_connected():
                conexao.close()

    @staticmethod
    def _atualizar_status(monitor_id: int, sql: str, parametros: tuple) -> None:
        conexao = obter_conexao()
        cursor = None
        try:
            cursor = conexao.cursor()
            cursor.execute(sql, parametros)
            conexao.commit()
            if cursor.rowcount != 1:
                raise LookupError(f"Alerta de monitoramento {monitor_id} não encontrado")
        except Exception:
            conexao.rollback()
            raise
        finally:
            if cursor is not None:
                cursor.close()
            if conexao.is_connected():
                conexao.close()
