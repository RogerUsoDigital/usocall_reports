"""Consulta dos relatórios de lote disponíveis no UsoCall."""

import logging
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Any

from database.usocall import obter_conexao


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Report:
    cliente_nome: str
    lote_id: int
    arquivo: str | None
    data_lote: datetime
    status_descricao: str | None
    usuario_nome: str | None
    status_id: int | None
    fluxo_whatsapp_id: int | None
    tipo_lote_descricao: str | None
    data_agendamento: datetime | None
    data_agendamento_final: datetime | None
    campanha_nome: str | None
    sucesso: int | None
    discando: int | None
    pendente: int | None
    erro: int | None
    total: int | None
    enviado_meta: int | None
    entregue_meta: int | None
    lidos_meta: int | None
    erro_meta: int | None
    percentual_erro: float
    percentual_erro_meta: float


class ReportRepository:
    QUERY = """
        SELECT
            CLI_NOME AS cliente_nome,
            LML_ID AS lote_id,
            LML_ARQUIVO AS arquivo,
            LML_DATA AS data_lote,
            SML_DESCRICAO AS status_descricao,
            USU_NOME AS usuario_nome,
            SML_ID AS status_id,
            LML_ID_FLUXO_WHATSAPP AS fluxo_whatsapp_id,
            TLO_DESCRICAO AS tipo_lote_descricao,
            LML_DATA_AGENDAMENTO AS data_agendamento,
            LML_DATA_AGENDAMENTO_FINAL AS data_agendamento_final,
            CAM_NOME AS campanha_nome,
            sucesso, discando, pendente, erro, total,
            ENVIADO_META AS enviado_meta,
            ENTREGUE_META AS entregue_meta,
            LIDOS_META AS lidos_meta,
            ERRO_META AS erro_meta,
            CASE WHEN COALESCE(total, 0) > 0
                THEN ROUND((erro / total) * 100, 2) ELSE 0 END AS percentual_erro,
            CASE WHEN COALESCE(ENVIADO_META, 0) > 0
                THEN ROUND((ERRO_META / ENVIADO_META) * 100, 2) ELSE 0 END AS percentual_erro_meta
        FROM tab_lote_mailing
        INNER JOIN tab_status_mailing ON LML_STATUS = SML_ID
        INNER JOIN tab_usuario ON LML_USUARIO = USU_ID
        INNER JOIN tab_tipo_lote ON TLO_ID = LML_TIPO
        INNER JOIN tab_campanha ON CAM_ID = LML_CAMPANHA
        INNER JOIN tab_cliente ON CAM_CLIENTE = CLI_ID
        LEFT JOIN tab_dash_hsm ON ID_MAILING = LML_ID
        LEFT JOIN tab_dash_detalhamento ON LOTE = LML_ID
        WHERE LML_DATA >= %s AND LML_DATA < %s
        HAVING percentual_erro > 15
        ORDER BY LML_ID
    """

    def buscar_relatorios_do_dia(self, data_referencia: date | None = None) -> list[Report]:
        """Busca os relatórios com erro alto da data informada ou do dia atual."""
        data_consulta = data_referencia or datetime.now().date()
        inicio_dia = datetime.combine(data_consulta, time.min)
        fim_dia = inicio_dia + timedelta(days=1)
        conexao = None
        cursor = None
        try:
            conexao = obter_conexao()
            cursor = conexao.cursor(dictionary=True)
            cursor.execute(self.QUERY, (inicio_dia, fim_dia))
            return [self._criar_report(linha) for linha in cursor.fetchall()]
        except Exception:
            logger.exception("Erro ao buscar relatórios do dia no UsoCall")
            raise
        finally:
            if cursor is not None:
                cursor.close()
            if conexao is not None and conexao.is_connected():
                conexao.close()

    @staticmethod
    def _criar_report(linha: dict[str, Any]) -> Report:
        return Report(**linha)
