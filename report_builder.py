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

    return f"{icon} {p:.1f}%"


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
    month_label: str,
    overall_day: AdherenceMetric,
    overall_month: AdherenceMetric,
    areas_day: list[dict],
    areas_month_by_name: dict[str, AdherenceMetric],
    include_grupo_rede: bool,
    grupo_rede_rows: list[dict] | None = None,
) -> str:
    lines: list[str] = []
    lines.append(f"📊 Relatório Merchandising (ref.: {ref_date.strftime('%d/%m/%Y')})")
    lines.append("")
    lines.append("Aderência ao Roteiro Geral")
    lines.append(
        f"Ontem: {fmt_pct(overall_day.aderencia_pct)}"
        f"  |  Mês: {fmt_pct(overall_month.aderencia_pct, with_icon=True)}"
    )
    lines.append("")
    lines.append("📍 Aderência ao Roteiro por Área")

    for r in order_areas(areas_day):
        area = (r.get("area_merchan") or "Não Identificada").strip()
        day_metric = metric_from_row(r)
        month_metric = areas_month_by_name.get(area, AdherenceMetric(0, 0, None))
        lines.append(
            f"- {area}: Ontem {fmt_pct(day_metric.aderencia_pct)}"
            f"  |  Mês {fmt_pct(month_metric.aderencia_pct, with_icon=True)}"
        )

    if include_grupo_rede:
        lines.append("")
        lines.append(f"🏪 Grupos/Redes Importantes ({month_label})")
        for r in (grupo_rede_rows or []):
            unidade = (r.get("unidade") or "").strip()
            feitas = _safe_int(r.get("visitas_feitas", 0))
            planejadas = _safe_int(r.get("visitas_planejadas", 0))
            pct = None
            try:
                pct = float(r.get("aderencia_pct"))
            except Exception:
                pct = None
            lines.append(
                f"- {unidade}: {fmt_pct(pct, with_icon=True)}"
                f"  |  Planejadas {planejadas}"
                f"  |  Feitas {feitas}"
            )

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
    lines.append(f"📊 Relatório Merchan - {area_name} (ref.: {ref_date.strftime('%d/%m/%Y')})")
    lines.append("")
    lines.append(f"Aderência ao Roteiro {area_name}")
    lines.append(
        f"Ontem: {fmt_pct(area_day.aderencia_pct)}"
        f"  |  Mês: {fmt_pct(area_month.aderencia_pct, with_icon=True)}"
    )
    lines.append("")
    lines.append("👥 Colaboradores (ordem por aderência do mês)")

    def sort_key(name: str):
        return name.casefold()

    all_names = set(collaborators_month_by_name.keys()) | set(collaborators_day_by_name.keys())

    lines[-1] = "👥 Colaboradores (ordem alfabética)"

    for name in sorted(all_names, key=sort_key):
        m = collaborators_month_by_name.get(name, AdherenceMetric(0, 0, None))
        d = collaborators_day_by_name.get(name, AdherenceMetric(0, 0, None))
        lines.append(
            f"- {name}: Ontem {fmt_pct(d.aderencia_pct)}"
            f"  |  Mês {fmt_pct(m.aderencia_pct, with_icon=True)}"
        )

    return "\n".join(lines).strip() + "\n"
