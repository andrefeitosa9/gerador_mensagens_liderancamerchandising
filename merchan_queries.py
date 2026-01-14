"""Queries SQL para o relatório de aderência ao roteiro (Merchan)."""

from __future__ import annotations

from datetime import date

from config import (
    CHECKIN_VALIDOS,
    GRUPOS_ECONOMICOS_IMPORTANTES,
    REDES_IMPORTANTES,
    TABLE_AREA_MERCHAN,
    TABLE_FERIADO_MERCHAN,
    TABLE_MONITORAMENTO,
    TABLE_TELEFONE_LIDERANCA,
)
from database import sql_date


def _checkin_in_list_sql() -> str:
    # ('Manual','Manual e GPS')
    itens = ", ".join([f"'{x}'" for x in CHECKIN_VALIDOS])
    return f"({itens})"


def _fora_do_roteiro_nao_sql(alias: str = "mp") -> str:
    """Predicate to keep only visits that are NOT off-route.

    Business rule: only count visits where ForaDoRoteiro == 'Não'.
    We use an accent/case-insensitive collation so 'Nao'/'NÃO' also match.
    """
    col = f"{alias}.ForaDoRoteiro"
    return (
        "LTRIM(RTRIM(ISNULL(" + col + ", 'Não'))) "
        "COLLATE Latin1_General_CI_AI = 'Nao'"
    )


def _not_holiday_sql(alias: str = "mp", date_col: str = "DataVisita") -> str:
    """Predicate to exclude holidays from adherence calculation.

    If CAST(<alias>.<date_col> AS DATE) exists in dimFeriadoMerchan, the row is ignored.
    """
    col = f"{alias}.{date_col}"
    return (
        "NOT EXISTS ("
        f"SELECT 1 FROM {TABLE_FERIADO_MERCHAN} f "
        f"WHERE f.data = CAST({col} AS DATE)"
        ")"
    )


def leaders_with_area_and_phone_sql() -> str:
    return f"""
SELECT DISTINCT
    a.colaborador_superior,
    a.area_merchan,
    t.telefone
FROM {TABLE_AREA_MERCHAN} a
LEFT JOIN {TABLE_TELEFONE_LIDERANCA} t
    ON t.nome_colaborador = a.colaborador_superior
""".strip()


def overall_adherence_sql(dt_start: date, dt_end: date) -> str:
    start = sql_date(dt_start)
    end = sql_date(dt_end)
    checkins = _checkin_in_list_sql()
    fora_ok = _fora_do_roteiro_nao_sql("mp")
    not_holiday = _not_holiday_sql("mp", "DataVisita")

    return f"""
SELECT
    SUM(CASE WHEN mp.tipocheckin IN {checkins} THEN 1 ELSE 0 END) AS visitas_feitas,
    COUNT(mp.visitaid) AS visitas_planejadas,
    CAST(
        (CAST(SUM(CASE WHEN mp.tipocheckin IN {checkins} THEN 1 ELSE 0 END) AS FLOAT) /
        NULLIF(COUNT(mp.visitaid), 0)) * 100
    AS DECIMAL(10,2)) AS aderencia_pct
FROM {TABLE_MONITORAMENTO} mp
WHERE mp.DataVisita >= CAST('{start}' AS DATE)
  AND mp.DataVisita < CAST('{end}' AS DATE)
    AND {fora_ok}
        AND {not_holiday}
""".strip()


def area_totals_sql(dt_start: date, dt_end: date) -> str:
    start = sql_date(dt_start)
    end = sql_date(dt_end)
    checkins = _checkin_in_list_sql()
    fora_ok = _fora_do_roteiro_nao_sql("mp")
    not_holiday = _not_holiday_sql("mp", "DataVisita")

    return f"""
SELECT
    ISNULL(dam.area_merchan, 'Não Identificada') AS area_merchan,
    SUM(CASE WHEN mp.tipocheckin IN {checkins} THEN 1 ELSE 0 END) AS visitas_feitas,
    COUNT(mp.visitaid) AS visitas_planejadas,
    CAST(
        (CAST(SUM(CASE WHEN mp.tipocheckin IN {checkins} THEN 1 ELSE 0 END) AS FLOAT) /
        NULLIF(COUNT(mp.visitaid), 0)) * 100
    AS DECIMAL(10,2)) AS aderencia_pct
FROM {TABLE_MONITORAMENTO} mp
LEFT JOIN {TABLE_AREA_MERCHAN} dam
    ON dam.colaborador_superior = mp.ColaboradorSuperior
WHERE mp.DataVisita >= CAST('{start}' AS DATE)
  AND mp.DataVisita < CAST('{end}' AS DATE)
    AND {fora_ok}
        AND {not_holiday}
GROUP BY dam.area_merchan
ORDER BY area_merchan ASC
""".strip()


def leader_area_total_sql(leader_name: str, dt_start: date, dt_end: date) -> str:
    start = sql_date(dt_start)
    end = sql_date(dt_end)
    checkins = _checkin_in_list_sql()
    leader_escaped = leader_name.replace("'", "''")
    fora_ok = _fora_do_roteiro_nao_sql("mp")
    not_holiday = _not_holiday_sql("mp", "DataVisita")

    return f"""
SELECT
    ISNULL(dam.area_merchan, 'Não Identificada') AS area_merchan,
    SUM(CASE WHEN mp.tipocheckin IN {checkins} THEN 1 ELSE 0 END) AS visitas_feitas,
    COUNT(mp.visitaid) AS visitas_planejadas,
    CAST(
        (CAST(SUM(CASE WHEN mp.tipocheckin IN {checkins} THEN 1 ELSE 0 END) AS FLOAT) /
        NULLIF(COUNT(mp.visitaid), 0)) * 100
    AS DECIMAL(10,2)) AS aderencia_pct
FROM {TABLE_MONITORAMENTO} mp
LEFT JOIN {TABLE_AREA_MERCHAN} dam
    ON dam.colaborador_superior = mp.ColaboradorSuperior
WHERE mp.ColaboradorSuperior = '{leader_escaped}'
  AND mp.DataVisita >= CAST('{start}' AS DATE)
  AND mp.DataVisita < CAST('{end}' AS DATE)
    AND {fora_ok}
        AND {not_holiday}
GROUP BY dam.area_merchan
""".strip()


def area_total_by_area_sql(area_name: str, dt_start: date, dt_end: date) -> str:
    """Total da área (independente do líder), usando o mapeamento em dimAreaMerchan."""
    start = sql_date(dt_start)
    end = sql_date(dt_end)
    checkins = _checkin_in_list_sql()
    area_escaped = area_name.replace("'", "''")
    fora_ok = _fora_do_roteiro_nao_sql("mp")
    not_holiday = _not_holiday_sql("mp", "DataVisita")

    return f"""
SELECT
    ISNULL(dam.area_merchan, 'Não Identificada') AS area_merchan,
    SUM(CASE WHEN mp.tipocheckin IN {checkins} THEN 1 ELSE 0 END) AS visitas_feitas,
    COUNT(mp.visitaid) AS visitas_planejadas,
    CAST(
        (CAST(SUM(CASE WHEN mp.tipocheckin IN {checkins} THEN 1 ELSE 0 END) AS FLOAT) /
        NULLIF(COUNT(mp.visitaid), 0)) * 100
    AS DECIMAL(10,2)) AS aderencia_pct
FROM {TABLE_MONITORAMENTO} mp
LEFT JOIN {TABLE_AREA_MERCHAN} dam
    ON dam.colaborador_superior = mp.ColaboradorSuperior
WHERE ISNULL(dam.area_merchan, 'Não Identificada') = '{area_escaped}'
  AND mp.DataVisita >= CAST('{start}' AS DATE)
  AND mp.DataVisita < CAST('{end}' AS DATE)
    AND {fora_ok}
        AND {not_holiday}
GROUP BY dam.area_merchan
""".strip()


def leader_collaborators_sql(leader_name: str, dt_start: date, dt_end: date) -> str:
    start = sql_date(dt_start)
    end = sql_date(dt_end)
    checkins = _checkin_in_list_sql()
    leader_escaped = leader_name.replace("'", "''")
    fora_ok = _fora_do_roteiro_nao_sql("mp")
    not_holiday = _not_holiday_sql("mp", "DataVisita")

    return f"""
SELECT
    mp.Colaborador AS colaborador,
    SUM(CASE WHEN mp.tipocheckin IN {checkins} THEN 1 ELSE 0 END) AS visitas_feitas,
    COUNT(mp.visitaid) AS visitas_planejadas,
    CAST(
        (CAST(SUM(CASE WHEN mp.tipocheckin IN {checkins} THEN 1 ELSE 0 END) AS FLOAT) /
        NULLIF(COUNT(mp.visitaid), 0)) * 100
    AS DECIMAL(10,2)) AS aderencia_pct
FROM {TABLE_MONITORAMENTO} mp
WHERE mp.ColaboradorSuperior = '{leader_escaped}'
  AND mp.DataVisita >= CAST('{start}' AS DATE)
  AND mp.DataVisita < CAST('{end}' AS DATE)
    AND {fora_ok}
        AND {not_holiday}
GROUP BY mp.Colaborador
""".strip()


def area_collaborators_sql(area_name: str, dt_start: date, dt_end: date) -> str:
    """Colaboradores da área (não por líder).

    Considera todos os ColaboradorSuperior cuja área em dimAreaMerchan = area_name,
    e agrega por mp.Colaborador.
    """
    start = sql_date(dt_start)
    end = sql_date(dt_end)
    checkins = _checkin_in_list_sql()
    area_escaped = area_name.replace("'", "''")
    fora_ok = _fora_do_roteiro_nao_sql("mp")
    not_holiday = _not_holiday_sql("mp", "DataVisita")

    return f"""
SELECT
    mp.Colaborador AS colaborador,
    SUM(CASE WHEN mp.tipocheckin IN {checkins} THEN 1 ELSE 0 END) AS visitas_feitas,
    COUNT(mp.visitaid) AS visitas_planejadas,
    CAST(
        (CAST(SUM(CASE WHEN mp.tipocheckin IN {checkins} THEN 1 ELSE 0 END) AS FLOAT) /
        NULLIF(COUNT(mp.visitaid), 0)) * 100
    AS DECIMAL(10,2)) AS aderencia_pct
FROM {TABLE_MONITORAMENTO} mp
INNER JOIN {TABLE_AREA_MERCHAN} dam
    ON dam.colaborador_superior = mp.ColaboradorSuperior
WHERE ISNULL(dam.area_merchan, 'Não Identificada') = '{area_escaped}'
  AND mp.DataVisita >= CAST('{start}' AS DATE)
  AND mp.DataVisita < CAST('{end}' AS DATE)
    AND {fora_ok}
        AND {not_holiday}
GROUP BY mp.Colaborador
""".strip()


def unidades_importantes_sql(
    dt_start: date,
    dt_end_exclusive: date,
    *,
    include_grupos: bool = True,
    include_redes: bool = True,
) -> str:
    """Aderência por unidades importantes (Grupos Econômicos e/ou Redes).

    Observação: o período é [dt_start, dt_end_exclusive).
    """
    start = sql_date(dt_start)
    end = sql_date(dt_end_exclusive)
    checkins = _checkin_in_list_sql()
    fora_ok = _fora_do_roteiro_nao_sql("mp")
    not_holiday = _not_holiday_sql("mp", "DataVisita")

    if not include_grupos and not include_redes:
        # Query vazia (retorna 0 linhas)
        return (
            "SELECT TOP 0 '' AS unidade, CAST(NULL AS DECIMAL(10,2)) AS aderencia_pct, "
            "0 AS visitas_feitas, 0 AS visitas_planejadas"
        )

    ge_in = ", ".join([f"'{x.replace("'", "''")}'" for x in GRUPOS_ECONOMICOS_IMPORTANTES])
    rede_in = ", ".join([f"'{x.replace("'", "''")}'" for x in REDES_IMPORTANTES])

    union_parts: list[str] = []

    if include_grupos:
        union_parts.append(
            f"""
    SELECT
        dge.nomegrupo AS Unidade_Agregadora,
        bc.visitaid,
        bc.tipocheckin
    FROM BaseComCodigo bc
    INNER JOIN bi_rbdistrib.dbo.dimgrupoeconomico dge ON dge.codcliente = bc.codcliente_limpo
    WHERE dge.nomegrupo IN ({ge_in})
""".rstrip()
        )

    if include_redes:
        union_parts.append(
            f"""
    SELECT
        drc.nomeRede AS Unidade_Agregadora,
        bc.visitaid,
        bc.tipocheckin
    FROM BaseComCodigo bc
    INNER JOIN bi_rbdistrib.dbo.dimcliente dc ON dc.codCliente = bc.codcliente_limpo
    INNER JOIN BI_RBDISTRIB.dbo.dimRedeCliente drc ON drc.codRede = dc.codRede
    WHERE drc.nomeRede IN ({rede_in})
""".rstrip()
        )

    union_sql = "\n\n    UNION ALL\n\n".join(union_parts)

    return f"""
WITH BaseLimpa AS (
    SELECT
        mp.visitaid,
        mp.tipocheckin,
        mp.DataVisita,
        mp.ColaboradorSuperior,
        LTRIM(RTRIM(LEFT(mp.pontodevenda, CHARINDEX('-', mp.pontodevenda + '-') - 1))) AS cod_extraido
    FROM {TABLE_MONITORAMENTO} mp
    WHERE mp.DataVisita >= CAST('{start}' AS DATE)
      AND mp.DataVisita < CAST('{end}' AS DATE)
            AND {fora_ok}
                            AND {not_holiday}
),
BaseComCodigo AS (
    SELECT
        *,
        CASE
            WHEN ISNUMERIC(cod_extraido) = 1 AND cod_extraido <> '' THEN CAST(cod_extraido AS INT)
            ELSE 99999
        END AS codcliente_limpo
    FROM BaseLimpa
),
UniaoVisoes AS (
{union_sql}
)
SELECT
    Unidade_Agregadora AS unidade,
    CAST(
        (CAST(SUM(CASE WHEN tipocheckin IN {checkins} THEN 1 ELSE 0 END) AS FLOAT) /
        NULLIF(COUNT(visitaid), 0)) * 100
    AS DECIMAL(10,2)) AS aderencia_pct,
    SUM(CASE WHEN tipocheckin IN {checkins} THEN 1 ELSE 0 END) AS visitas_feitas,
    COUNT(visitaid) AS visitas_planejadas
FROM UniaoVisoes
GROUP BY Unidade_Agregadora
ORDER BY visitas_planejadas DESC
""".strip()


def grupo_rede_month_sql(month_start: date, month_end_exclusive: date) -> str:
    # Compatibilidade: retorna grupos + redes
    return unidades_importantes_sql(
        month_start, month_end_exclusive, include_grupos=True, include_redes=True
    )


def grupos_importantes_sql(dt_start: date, dt_end_exclusive: date) -> str:
    return unidades_importantes_sql(dt_start, dt_end_exclusive, include_grupos=True, include_redes=False)


def redes_importantes_sql(dt_start: date, dt_end_exclusive: date) -> str:
    return unidades_importantes_sql(dt_start, dt_end_exclusive, include_grupos=False, include_redes=True)
