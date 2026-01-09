"""Montagem das mensagens de WhatsApp do relatório de Merchan."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from config import AREAS_ORDEM_PADRAO


@dataclass(frozen=True)
class AdherenceMetric:
    visitas_feitas: int
    visitas_planejadas: int
    aderencia_pct: float | None


def _safe_int(x) -> int:
    try:
        return int(x)
    except Exception:
        return 0


def metric_from_row(row) -> AdherenceMetric:
    feitas = _safe_int(row.get("visitas_feitas", 0))
    planejadas = _safe_int(row.get("visitas_planejadas", 0))
    pct = row.get("aderencia_pct", None)
    try:
        pct_val = float(pct) if pct is not None else None
    except Exception:
        pct_val = None
    return AdherenceMetric(feitas, planejadas, pct_val)


def fmt_pct(p: float | None, *, with_icon: bool = False) -> str:
    if p is None:
        return "—"

    if not with_icon:
        return f"{p:.1f}%"

    # Indicador visual por faixa (usar apenas onde fizer sentido, ex.: Mês)
    # <70%  -> ❌
    # 70-<90 -> 🟡
    # >=90% -> ✅
    if p < 70:
        icon = "❌"
    elif p < 90:
        icon = "🟡"
    else:
        icon = "✅"

    return f"{p:.1f}% {icon}"


def normalize_phone_to_e164(raw: str) -> str:
    s = (raw or "").strip()
    s = s.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")

    if s.startswith("+"):
        return s

    # Só dígitos
    digits = "".join(ch for ch in s if ch.isdigit())

    # Se já veio com 55 na frente
    if digits.startswith("55"):
        return "+" + digits

    # DDD + número (11 dígitos) -> assume Brasil
    if len(digits) in (10, 11):
        return "+55" + digits

    # Fallback
    return "+" + digits if digits else ""


def order_areas(area_rows: list[dict]) -> list[dict]:
    order_index = {name.lower(): i for i, name in enumerate(AREAS_ORDEM_PADRAO)}

    def key_fn(r: dict):
        name = (r.get("area_merchan") or "").strip()
        idx = order_index.get(name.lower(), 10_000)
        return (idx, name.lower())

    return sorted(area_rows, key=key_fn)


def build_general_leader_message(
    ref_date: date,
    day_label: str,
    period2_label: str,
    overall_day: AdherenceMetric,
    overall_period2: AdherenceMetric,
    areas_day: list[dict],
    areas_month_by_name: dict[str, AdherenceMetric],
    include_grupo_rede: bool,
    grupo_rede_day_rows: list[dict] | None = None,
    grupo_rede_month_rows: list[dict] | None = None,
    grupo_rede_section_title: str = "🏪 Grupos/Redes Importantes",
    include_areas_section: bool = True,
    period2_title: str = "Mês",
) -> str:
    lines: list[str] = []
    lines.append("📊 Relatório Merchandising")
    lines.append("")
    lines.append(f"Aderência ao Roteiro Geral (Ontem {day_label} | {period2_title} {period2_label})")
    lines.append("")
    lines.append(
        f"Ontem: {fmt_pct(overall_day.aderencia_pct)}  |  {period2_title}: {fmt_pct(overall_period2.aderencia_pct, with_icon=True)}"
    )
    lines.append("")

    if include_areas_section:
        lines.append(f"📍 Aderência ao Roteiro por Área (Ontem {day_label} | {period2_title} {period2_label})")
        lines.append("")

        for r in order_areas(areas_day):
            area = (r.get("area_merchan") or "Não Identificada").strip()
            day_metric = metric_from_row(r)
            month_metric = areas_month_by_name.get(area, AdherenceMetric(0, 0, None))
            lines.append(f"- {area}:")
            lines.append(
                f"Ontem {fmt_pct(day_metric.aderencia_pct)}  |  {period2_title} {fmt_pct(month_metric.aderencia_pct, with_icon=True)}"
            )
            lines.append("")

    if include_grupo_rede and grupo_rede_day_rows is not None and grupo_rede_month_rows is not None:
        lines.append(f"{grupo_rede_section_title} ({period2_title} {period2_label})")
        lines.append("")
        
        # Criar dicionários para buscar por unidade
        day_by_unit = {(r.get("unidade") or "").strip(): r for r in grupo_rede_day_rows}
        month_by_unit = {(r.get("unidade") or "").strip(): r for r in grupo_rede_month_rows}
        
        # Unir todas as unidades
        all_units = set(day_by_unit.keys()) | set(month_by_unit.keys())

        if not all_units:
            lines.append("Sem dados no período.")
            lines.append("")
            return "\n".join(lines).strip() + "\n"
        
        for unidade in sorted(all_units):
            if not unidade:
                continue
            
            day_r = day_by_unit.get(unidade, {})
            month_r = month_by_unit.get(unidade, {})
            
            day_pct = None
            month_pct = None
            
            try:
                if day_r.get("aderencia_pct") is not None:
                    day_pct = float(day_r.get("aderencia_pct"))
            except Exception:
                pass
            
            try:
                if month_r.get("aderencia_pct") is not None:
                    month_pct = float(month_r.get("aderencia_pct"))
            except Exception:
                pass
            
            lines.append(f"- {unidade}:")
            lines.append(
                f"Ontem {fmt_pct(day_pct)}  |  {period2_title} {fmt_pct(month_pct, with_icon=True)}"
            )
            lines.append("")

    return "\n".join(lines).strip() + "\n"


def build_area_leader_message(
    area_name: str,
    leader_name: str,
    ref_date: date,
    month_label: str,
    area_day: AdherenceMetric,
    area_month: AdherenceMetric,
    collaborators_day_by_name: dict[str, AdherenceMetric],
    collaborators_month_by_name: dict[str, AdherenceMetric],
) -> str:
    lines: list[str] = []
    lines.append(f"📊 Relatório Merchan - {area_name}")
    lines.append("")
    lines.append(f"Aderência ao Roteiro {area_name}")
    lines.append("")
    lines.append(
        f"Ontem: {fmt_pct(area_day.aderencia_pct)}  |  Mês: {fmt_pct(area_month.aderencia_pct, with_icon=True)}"
    )
    lines.append("")
    lines.append("👥 Colaboradores (ordem alfabética)")
    lines.append("")

    def sort_key(name: str):
        return name.casefold()

    # Regra: para líderes de área, listar apenas colaboradores que tiveram
    # visitas_planejadas > 0 no dia de ontem.
    eligible_names = [
        name
        for name, day_metric in collaborators_day_by_name.items()
        if day_metric.visitas_planejadas > 0
    ]

    if not eligible_names:
        lines.append("Sem colaboradores com visitas planejadas ontem.")
        lines.append("")
        return "\n".join(lines).strip() + "\n"

    for name in sorted(eligible_names, key=sort_key):
        d = collaborators_day_by_name.get(name, AdherenceMetric(0, 0, None))
        m = collaborators_month_by_name.get(name, AdherenceMetric(0, 0, None))
        lines.append(f"- {name}:")
        lines.append(f"Ontem {fmt_pct(d.aderencia_pct)}  |  Mês {fmt_pct(m.aderencia_pct, with_icon=True)}")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def build_diretoria_message(
    ref_date: date,
    semana_label: str,
    mes_label: str,
    overall_semana: AdherenceMetric,
    overall_mes: AdherenceMetric,
    areas_semana: list[dict] | None = None,
    areas_mes_by_name: dict[str, AdherenceMetric] | None = None,
    include_areas_section: bool = True,
    grupos_semana_rows: list[dict] | None = None,
    grupos_mes_rows: list[dict] | None = None,
    grupos_section_title: str = "🏪 Grupos Econômicos Importantes",
) -> str:
    lines: list[str] = []
    lines.append("📊 Relatório Merchandising")
    lines.append("")
    lines.append(f"Aderência ao Roteiro Geral (Semana {semana_label} | Mês {mes_label})")
    lines.append("")
    lines.append(
        f"Semana Anterior: {fmt_pct(overall_semana.aderencia_pct, with_icon=False)}  |  Mês: {fmt_pct(overall_mes.aderencia_pct, with_icon=True)}"
    )
    lines.append("")

    if include_areas_section:
        lines.append("📍 Aderência ao Roteiro por Área")
        lines.append("")

        areas_mes_by_name = areas_mes_by_name or {}
        areas_semana = areas_semana or []

        for r in order_areas(areas_semana):
            area = (r.get("area_merchan") or "Não Identificada").strip()
            semana_metric = metric_from_row(r)
            mes_metric = areas_mes_by_name.get(area, AdherenceMetric(0, 0, None))
            lines.append(f"- {area}:")
            lines.append(
                f"Semana {fmt_pct(semana_metric.aderencia_pct, with_icon=False)}  |  Mês {fmt_pct(mes_metric.aderencia_pct, with_icon=True)}"
            )
            lines.append("")

    if grupos_semana_rows is not None and grupos_mes_rows is not None:
        lines.append(f"{grupos_section_title} (Semana {semana_label} | Mês {mes_label})")
        lines.append("")

        semana_by_unit = {(r.get('unidade') or '').strip(): r for r in grupos_semana_rows}
        mes_by_unit = {(r.get('unidade') or '').strip(): r for r in grupos_mes_rows}
        all_units = set(semana_by_unit.keys()) | set(mes_by_unit.keys())

        if not all_units:
            lines.append("Sem dados no período.")
            lines.append("")
            return "\n".join(lines).strip() + "\n"

        for unidade in sorted(all_units):
            if not unidade:
                continue

            semana_r = semana_by_unit.get(unidade, {})
            mes_r = mes_by_unit.get(unidade, {})

            semana_pct = None
            mes_pct = None

            try:
                if semana_r.get("aderencia_pct") is not None:
                    semana_pct = float(semana_r.get("aderencia_pct"))
            except Exception:
                pass

            try:
                if mes_r.get("aderencia_pct") is not None:
                    mes_pct = float(mes_r.get("aderencia_pct"))
            except Exception:
                pass

            lines.append(f"- {unidade}:")
            lines.append(f"Semana {fmt_pct(semana_pct, with_icon=False)}  |  Mês {fmt_pct(mes_pct, with_icon=True)}")
            lines.append("")

    return "\n".join(lines).strip() + "\n"
