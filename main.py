"""Gerador de mensagens diárias (WhatsApp) - Aderência ao Roteiro (Merchandising).

Regras:
- Envia mensagens apenas de segunda a sábado.
- No disparo de segunda, "ontem" refere-se ao sábado.
- Líder geral (área = Merchan) recebe geral + por área; na segunda também recebe grupos/redes.
- Líderes de área recebem resumo da área + colaboradores ordenados pela aderência do mês.

Observação: no modo de teste, todos os envios vão para o telefone fixo configurado.
"""

from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta

from config import MODO_TESTE, TEST_PHONE_E164, USE_TEST_PHONE
from database import Database
from merchan_queries import (
	area_total_by_area_sql,
	area_totals_sql,
	area_collaborators_sql,
	grupo_rede_month_sql,
	leader_area_total_sql,
	leaders_with_area_and_phone_sql,
	overall_adherence_sql,
)
from report_builder import (
	AdherenceMetric,
	build_area_leader_message,
	build_general_leader_message,
	metric_from_row,
	normalize_phone_to_e164,
)
from whatsapp_sender import WhatsAppSender


def should_send_today(today: date) -> bool:
	# weekday: 0=segunda ... 6=domingo
	return today.weekday() != 6


def reference_date(today: date) -> date:
	# segunda -> sábado
	if today.weekday() == 0:
		return today - timedelta(days=2)
	return today - timedelta(days=1)


def month_start(d: date) -> date:
	return date(d.year, d.month, 1)


def scalar_metric(df) -> AdherenceMetric:
	if df is None or df.empty:
		return AdherenceMetric(0, 0, None)
	return metric_from_row(df.iloc[0].to_dict())


def main() -> int:
	parser = argparse.ArgumentParser()
	parser.add_argument(
		"--enviar",
		action="store_true",
		help="Envia pelo WhatsApp Web (por padrão apenas simula/imprime)",
	)
	args = parser.parse_args()

	hoje = datetime.now().date()
	if not should_send_today(hoje):
		print("Hoje é domingo: não envia relatório.")
		return 0

	ref = reference_date(hoje)
	dt_start = ref
	dt_end = ref + timedelta(days=1)
	ms = month_start(ref)
	me = hoje  # mês até ontem (exclui o dia de execução)

	month_label = f"Mês {ms.strftime('%m/%Y')}"
	include_grupo_rede = hoje.weekday() == 0  # segunda

	db = Database()
	try:
		leaders_df = db.query_df(leaders_with_area_and_phone_sql())
		if leaders_df.empty:
			print("⚠ Nenhum líder encontrado em dimAreaMerchan.")
			return 1

		# Identifica líderes
		leaders_df["area_merchan"] = leaders_df["area_merchan"].fillna("")
		leaders_df["colaborador_superior"] = leaders_df["colaborador_superior"].fillna("")
		leaders_df["telefone"] = leaders_df["telefone"].fillna("")

		general_mask = leaders_df["area_merchan"].str.strip().str.lower() == "merchan"
		general_leaders = leaders_df[general_mask]
		area_leaders = leaders_df[~general_mask]

		# Métricas gerais
		overall_day = scalar_metric(db.query_df(overall_adherence_sql(dt_start, dt_end)))
		overall_month = scalar_metric(db.query_df(overall_adherence_sql(ms, me)))

		# Por área (para líder geral)
		areas_day_df = db.query_df(area_totals_sql(dt_start, dt_end))
		areas_month_df = db.query_df(area_totals_sql(ms, me))
		areas_month_by_name: dict[str, AdherenceMetric] = {}
		for _, row in areas_month_df.iterrows():
			name = (row.get("area_merchan") or "Não Identificada").strip()
			areas_month_by_name[name] = metric_from_row(row.to_dict())

		grupo_rede_rows = None
		if include_grupo_rede:
			grupo_rede_rows = db.query_df(grupo_rede_month_sql(ms, me)).to_dict("records")

		mensagens_envio: list[dict] = []

		# Líder geral
		for _, row in general_leaders.iterrows():
			leader_name = (row.get("colaborador_superior") or "").strip() or "Líder Geral"
			raw_phone = (row.get("telefone") or "").strip()
			phone = TEST_PHONE_E164 if USE_TEST_PHONE else normalize_phone_to_e164(raw_phone)
			msg = build_general_leader_message(
				ref_date=ref,
				month_label=month_label,
				overall_day=overall_day,
				overall_month=overall_month,
				areas_day=areas_day_df.to_dict("records"),
				areas_month_by_name=areas_month_by_name,
				include_grupo_rede=include_grupo_rede,
				grupo_rede_rows=grupo_rede_rows,
			)
			mensagens_envio.append(
				{
					"destinatario": leader_name,
					"telefone": phone,
					"mensagens": [msg],
					"tipo": "lider_geral",
				}
			)

		# Líderes de área
		# Pode haver duplicidade se a tabela tiver mais de 1 linha por líder; dedup por colaborador_superior
		seen_area_leaders: set[str] = set()
		for _, row in area_leaders.iterrows():
			leader_name = (row.get("colaborador_superior") or "").strip()
			if not leader_name or leader_name in seen_area_leaders:
				continue
			seen_area_leaders.add(leader_name)

			area_name = (row.get("area_merchan") or "Não Identificada").strip() or "Não Identificada"
			raw_phone = (row.get("telefone") or "").strip()
			phone = TEST_PHONE_E164 if USE_TEST_PHONE else normalize_phone_to_e164(raw_phone)

			# Área (ontem e mês): deve refletir a área como um todo, mesmo que existam vários líderes
			area_day_df = db.query_df(area_total_by_area_sql(area_name, dt_start, dt_end))
			area_month_df = db.query_df(area_total_by_area_sql(area_name, ms, me))
			area_day_metric = scalar_metric(area_day_df)
			area_month_metric = scalar_metric(area_month_df)
			if not area_day_df.empty:
				maybe_area = (area_day_df.iloc[0].get("area_merchan") or "").strip()
				if maybe_area:
					area_name = maybe_area

			# Colaboradores (ontem e mês) - por ÁREA (não por líder)
			coll_day_df = db.query_df(area_collaborators_sql(area_name, dt_start, dt_end))
			coll_month_df = db.query_df(area_collaborators_sql(area_name, ms, me))

			coll_day_by_name: dict[str, AdherenceMetric] = {}
			for _, r2 in coll_day_df.iterrows():
				name = (r2.get("colaborador") or "").strip()
				if name:
					coll_day_by_name[name] = metric_from_row(r2.to_dict())

			coll_month_by_name: dict[str, AdherenceMetric] = {}
			for _, r2 in coll_month_df.iterrows():
				name = (r2.get("colaborador") or "").strip()
				if name:
					coll_month_by_name[name] = metric_from_row(r2.to_dict())

			# Se a área não tiver nenhum colaborador no período,
			# não envia mensagem "vazia" (apenas cabeçalho).
			all_names = set(coll_month_by_name.keys()) | set(coll_day_by_name.keys())
			if not all_names:
				print(
					f"⚠ Pulando envio para {leader_name} ({area_name}): área sem colaboradores no período."
				)
				continue

			msg = build_area_leader_message(
				area_name=area_name,
				leader_name=leader_name,
				ref_date=ref,
				month_label=month_label,
				area_day=area_day_metric,
				area_month=area_month_metric,
				collaborators_day_by_name=coll_day_by_name,
				collaborators_month_by_name=coll_month_by_name,
			)

			mensagens_envio.append(
				{
					"destinatario": leader_name,
					"telefone": phone,
					"mensagens": [msg],
					"tipo": "lider_area",
				}
			)

		modo_teste = MODO_TESTE and not args.enviar
		sender = WhatsAppSender(intervalo_entre_mensagens=7, intervalo_mesmo_numero=5, espera_pos_envio=5)
		sender.enviar_mensagens_lote(mensagens_envio, modo_teste=modo_teste)
		return 0
	finally:
		db.disconnect()


if __name__ == "__main__":
	raise SystemExit(main())
