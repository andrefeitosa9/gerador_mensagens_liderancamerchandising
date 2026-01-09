"""Gerador de mensagens diárias (WhatsApp) - Aderência ao Roteiro (Merchandising).

Regras:
- Envia mensagens apenas de segunda a sábado.
- No disparo de segunda, "ontem" refere-se ao sábado.
- Líder Merchan (área_merchan = Merchan): recebe TODO DIA
	- Resumo geral
	- Resumo por área
	- Bloco de Grupos/Redes importantes
- Diretoria (área_merchan = Diretoria): recebe SOMENTE NA SEGUNDA
	- Resumo geral
	- Bloco de Grupos importantes (sem redes)
- Líderes de área recebem resumo da área + colaboradores.

Observação: se USE_TEST_PHONE estiver ativo, todos os envios vão para TEST_PHONE_E164.
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
	grupos_importantes_sql,
	grupo_rede_month_sql,
	leader_area_total_sql,
	leaders_with_area_and_phone_sql,
	overall_adherence_sql,
)
from report_builder import (
	AdherenceMetric,
	build_area_leader_message,
	build_diretoria_message,
	build_general_leader_message,
	metric_from_row,
	normalize_phone_to_e164,
)



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


def week_start(d: date) -> date:
	# Monday as start-of-week
	return d - timedelta(days=d.weekday())


def scalar_metric(rows: list[dict] | None) -> AdherenceMetric:
	if not rows:
		return AdherenceMetric(0, 0, None)
	return metric_from_row(rows[0])


def main() -> int:
	parser = argparse.ArgumentParser()
	parser.add_argument(
		"--enviar",
		action="store_true",
		help="(Compatibilidade) Envio real ja e o padrao; use --teste para apenas visualizar",
	)
	parser.add_argument(
		"--teste",
		action="store_true",
		help="Força modo teste (não abre WhatsApp; apenas imprime as mensagens)",
	)
	parser.add_argument(
		"--data",
		type=str,
		default=None,
		help="Simula a data de execucao (YYYY-MM-DD). Ex: --data 2026-01-12 para simular segunda",
	)
	parser.add_argument(
		"--somente-diretoria",
		action="store_true",
		help="Gera/mostra apenas a mensagem da Diretoria (use junto com --teste/--data)",
	)
	args = parser.parse_args()

	hoje = date.fromisoformat(args.data) if args.data else datetime.now().date()
	if not should_send_today(hoje):
		print("Hoje é domingo: não envia relatório.")
		return 0

	ref = reference_date(hoje)
	dt_start = ref
	dt_end = ref + timedelta(days=1)
	ms = month_start(ref)
	me = hoje  # mês até ontem (exclui o dia de execução)

	month_label = f"{ms.strftime('%m')}"
	weekday = hoje.weekday()  # 0=segunda
	include_grupo_rede_merchan = True  # TODO DIA
	include_grupos_diretoria = weekday == 0  # SOMENTE SEGUNDA
	ws = week_start(ref)
	ws_prev = ws - timedelta(days=7)
	we_prev = ws_prev + timedelta(days=6)  # ate o sabado anterior (exclusive)
	prev_week_label = f"{ws_prev.strftime('%d/%m')} a {(ws_prev + timedelta(days=5)).strftime('%d/%m')}"

	db = Database()
	try:
		leaders_rows = db.query_rows(leaders_with_area_and_phone_sql())
		if not leaders_rows:
			print("⚠ Nenhum líder encontrado em dimAreaMerchan.")
			return 1

		def _norm_area(v: str) -> str:
			return (v or "").strip().casefold()

		merchan_leaders = [r for r in leaders_rows if _norm_area(r.get("area_merchan")) == "merchan"]
		diretoria_leaders = [r for r in leaders_rows if _norm_area(r.get("area_merchan")) == "diretoria"]
		area_leaders = [
			r
			for r in leaders_rows
			if _norm_area(r.get("area_merchan")) not in ("merchan", "diretoria")
		]

		# Métricas gerais
		overall_day = scalar_metric(db.query_rows(overall_adherence_sql(dt_start, dt_end)))
		overall_month = scalar_metric(db.query_rows(overall_adherence_sql(ms, me)))
		overall_prev_week = scalar_metric(db.query_rows(overall_adherence_sql(ws_prev, we_prev)))

		# Por área (para líder geral)
		areas_day_rows = db.query_rows(area_totals_sql(dt_start, dt_end))
		areas_month_rows = db.query_rows(area_totals_sql(ms, me))
		areas_month_by_name: dict[str, AdherenceMetric] = {}
		for row in areas_month_rows:
			name = (row.get("area_merchan") or "Não Identificada").strip()
			areas_month_by_name[name] = metric_from_row(row)

		areas_prev_week_rows = None
		areas_prev_week_by_name: dict[str, AdherenceMetric] | None = None
		if include_grupos_diretoria:
			areas_prev_week_rows = db.query_rows(area_totals_sql(ws_prev, we_prev))
			# Reusa o dict do mês para consulta por área
			areas_prev_week_by_name = areas_month_by_name

		# Bloco de unidades importantes
		grupo_rede_day_rows = None
		grupo_rede_month_rows = None
		if include_grupo_rede_merchan:
			grupo_rede_day_rows = db.query_rows(grupo_rede_month_sql(dt_start, dt_end))
			grupo_rede_month_rows = db.query_rows(grupo_rede_month_sql(ms, me))

		grupos_semana_rows = None
		grupos_mes_rows = None
		if include_grupos_diretoria:
			grupos_semana_rows = db.query_rows(grupos_importantes_sql(ws_prev, we_prev))
			grupos_mes_rows = db.query_rows(grupos_importantes_sql(ms, me))

		mensagens_envio: list[dict] = []
		ontem_label = (ref - timedelta(days=1)).strftime("%d/%m")

		# Líder Merchan (diário)
		if not args.somente_diretoria:
			for row in merchan_leaders:
				leader_name = (row.get("colaborador_superior") or "").strip() or "Líder Merchan"
				raw_phone = (row.get("telefone") or "").strip()
				phone = TEST_PHONE_E164 if USE_TEST_PHONE else normalize_phone_to_e164(raw_phone)
				msg = build_general_leader_message(
					ref_date=ref,
					day_label=ontem_label,
					period2_label=month_label,
					overall_day=overall_day,
					overall_period2=overall_month,
					areas_day=areas_day_rows,
					areas_month_by_name=areas_month_by_name,
					include_grupo_rede=include_grupo_rede_merchan,
					grupo_rede_day_rows=grupo_rede_day_rows,
					grupo_rede_month_rows=grupo_rede_month_rows,
					grupo_rede_section_title="🏪 Grupos/Redes Importantes",
					period2_title="Mês",
				)
				mensagens_envio.append(
					{
						"destinatario": leader_name,
						"telefone": phone,
						"mensagens": [msg],
						"tipo": "lider_merchan",
					}
				)

		# Diretoria (somente segunda)
		if include_grupos_diretoria:
			for row in diretoria_leaders:
				leader_name = (row.get("colaborador_superior") or "").strip() or "Diretoria"
				raw_phone = (row.get("telefone") or "").strip()
				phone = TEST_PHONE_E164 if USE_TEST_PHONE else normalize_phone_to_e164(raw_phone)
				msg = build_diretoria_message(
					ref_date=ref,
					semana_label=prev_week_label,
					mes_label=month_label,
					overall_semana=overall_prev_week,
					overall_mes=overall_month,
					areas_semana=areas_prev_week_rows,
					areas_mes_by_name=areas_prev_week_by_name,
					include_areas_section=True,
					grupos_semana_rows=grupos_semana_rows,
					grupos_mes_rows=grupos_mes_rows,
					grupos_section_title="🏪 Grupos Econômicos Importantes",
				)
				mensagens_envio.append(
					{
						"destinatario": leader_name,
						"telefone": phone,
						"mensagens": [msg],
						"tipo": "diretoria",
					}
				)

		# Líderes de área
		# Pode haver duplicidade se a tabela tiver mais de 1 linha por líder; dedup por colaborador_superior
		if not args.somente_diretoria:
			seen_area_leaders: set[str] = set()
			for row in area_leaders:
				leader_name = (row.get("colaborador_superior") or "").strip()
				if not leader_name or leader_name in seen_area_leaders:
					continue
				seen_area_leaders.add(leader_name)

				area_name = (row.get("area_merchan") or "Não Identificada").strip() or "Não Identificada"
				raw_phone = (row.get("telefone") or "").strip()
				phone = TEST_PHONE_E164 if USE_TEST_PHONE else normalize_phone_to_e164(raw_phone)

			# Área (ontem e mês): deve refletir a área como um todo, mesmo que existam vários líderes
				area_day_rows = db.query_rows(area_total_by_area_sql(area_name, dt_start, dt_end))
				area_month_rows = db.query_rows(area_total_by_area_sql(area_name, ms, me))
				area_day_metric = scalar_metric(area_day_rows)
				area_month_metric = scalar_metric(area_month_rows)
				if area_day_rows:
					maybe_area = (area_day_rows[0].get("area_merchan") or "").strip()
					if maybe_area:
						area_name = maybe_area

			# Colaboradores (ontem e mês) - por ÁREA (não por líder)
				coll_day_rows = db.query_rows(area_collaborators_sql(area_name, dt_start, dt_end))
				coll_month_rows = db.query_rows(area_collaborators_sql(area_name, ms, me))

				coll_day_by_name: dict[str, AdherenceMetric] = {}
				for r2 in coll_day_rows:
					name = (r2.get("colaborador") or "").strip()
					if name:
						coll_day_by_name[name] = metric_from_row(r2)

				coll_month_by_name: dict[str, AdherenceMetric] = {}
				for r2 in coll_month_rows:
					name = (r2.get("colaborador") or "").strip()
					if name:
						coll_month_by_name[name] = metric_from_row(r2)

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

		modo_teste = args.teste or MODO_TESTE
		if modo_teste:
			print("\n" + "=" * 60)
			print("MODO TESTE - PRÉVIA DAS MENSAGENS")
			print("=" * 60)
			print(f"Total de destinatários: {len(mensagens_envio)}")
			print("=" * 60)
			for i, item in enumerate(mensagens_envio, 1):
				destinatario = item["destinatario"]
				telefone = item["telefone"]
				mensagens = item["mensagens"]
				tipo = item.get("tipo", "")
				print(f"\n[{i}/{len(mensagens_envio)}] {tipo.upper()}: {destinatario}")
				print(f"Telefone: {telefone}")
				for j, msg in enumerate(mensagens, 1):
					print(f"\n--- Mensagem {j} ---")
					print(msg)
			return 0

		from whatsapp_sender import WhatsAppSender
		sender = WhatsAppSender(intervalo_entre_mensagens=7, intervalo_mesmo_numero=5, espera_pos_envio=5)
		sender.enviar_mensagens_lote(mensagens_envio, modo_teste=False)
		return 0
	finally:
		db.disconnect()


if __name__ == "__main__":
	raise SystemExit(main())
