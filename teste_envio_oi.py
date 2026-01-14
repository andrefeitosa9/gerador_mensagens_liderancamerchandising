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

from config import TEST_PHONE_E164
from whatsapp_sender import WhatsAppSender


def main() -> int:
    telefone = TEST_PHONE_E164
    mensagem = "oi"

    print("=" * 60)
    print("TESTE WHATSAPP - ENVIO DE 'OI'")
    print(f"Telefone destino: {telefone}")
    print("=" * 60)

    sender = WhatsAppSender(intervalo_entre_mensagens=2, intervalo_mesmo_numero=2, espera_pos_envio=5)
    ok = sender.enviar_mensagem(telefone, mensagem, fechar_aba=True)

    # Best-effort: tenta fechar o navegador ao final para não acumular janelas.
    try:
        sender.fechar_navegador()
    except Exception:
        pass

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
