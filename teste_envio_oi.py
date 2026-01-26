"""Teste rápido de envio via WhatsApp.

Envia apenas um "oi" para o número configurado em `config.TEST_PHONE_E164`.

Uso:
- python teste_envio_oi.py

Requisitos práticos:
- WhatsApp Web deve estar logado no navegador padrão.
- O computador precisa estar com foco no navegador (pywhatkit/pyautogui).
"""

from __future__ import annotations

import sys

from config import (
    TEST_PHONE_E164,
    WA_ESPERA_POS_ENVIO,
    WA_INTERVALO_ENTRE_MENSAGENS,
    WA_INTERVALO_MESMO_NUMERO,
    WA_WAIT_TIME_PADRAO,
    WA_WAIT_TIME_PRIMEIRA,
    WA_WARMUP_SEGUNDOS,
)
from whatsapp_sender import WhatsAppSender


def main() -> int:
    telefone = TEST_PHONE_E164
    mensagens = ["oi", "oi (2)"]

    print("=" * 60)
    print("TESTE WHATSAPP - ENVIO DE 2 MENSAGENS")
    print(f"Telefone destino: {telefone}")
    print("=" * 60)

    sender = WhatsAppSender(
        intervalo_entre_mensagens=WA_INTERVALO_ENTRE_MENSAGENS,
        intervalo_mesmo_numero=WA_INTERVALO_MESMO_NUMERO,
        espera_pos_envio=WA_ESPERA_POS_ENVIO,
        wait_time_primeira=WA_WAIT_TIME_PRIMEIRA,
        wait_time_padrao=WA_WAIT_TIME_PADRAO,
        warmup_segundos=WA_WARMUP_SEGUNDOS,
    )
    lote = [
        {
            "destinatario": "TESTE",
            "telefone": telefone,
            "mensagens": mensagens,
            "tipo": "teste",
        }
    ]
    resumo = sender.enviar_mensagens_lote(lote, modo_teste=False)
    ok = resumo.get("falhas", 1) == 0

    # Não fecha automaticamente o navegador para evitar fechar antes do envio.

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
