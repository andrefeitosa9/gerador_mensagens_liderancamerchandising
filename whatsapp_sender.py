"""Envio de mensagens pelo WhatsApp Web via pywhatkit.

Notas práticas:
- O pywhatkit abre o WhatsApp Web, digita e envia a mensagem.
- Para evitar que a aba seja fechada cedo demais (mensagem ainda "subindo"),
  aguardamos alguns segundos após o envio antes de fechar.
"""

import time
import webbrowser

import pyautogui
import pywhatkit as kit


KICKOFF_PHONE_E164 = "+5585986068742"
KICKOFF_MESSAGE = "Disparo de mensagens Merchan iniciado"


class WhatsAppSender:
    def __init__(
        self,
        intervalo_entre_mensagens=15,
        intervalo_mesmo_numero=8,
        espera_pos_envio=10,
        wait_time_primeira=90,
        wait_time_padrao=45,
        warmup_segundos=25,
        auto_close_browser=False,
    ):
        self.intervalo = intervalo_entre_mensagens
        self.intervalo_mesmo_numero = intervalo_mesmo_numero
        self.espera_pos_envio = espera_pos_envio
        self.wait_time_primeira = wait_time_primeira
        self.wait_time_padrao = wait_time_padrao
        self.warmup_segundos = warmup_segundos
        self._ja_enviou_algo = False
        # Não fecha automaticamente o navegador a menos que solicitado
        self.auto_close_browser = auto_close_browser

    def warmup_whatsapp_web(self):
        """Abre o WhatsApp Web para reduzir a chance do 1º envio ficar em rascunhos."""
        try:
            print("🌐 Abrindo WhatsApp Web (warm-up)...")
            webbrowser.open("https://web.whatsapp.com")
            if self.warmup_segundos and self.warmup_segundos > 0:
                print(f"  ⏱ Aguardando {self.warmup_segundos}s para carregar...")
                time.sleep(self.warmup_segundos)
            try:
                pyautogui.press("esc")
            except Exception:
                pass
            return True
        except Exception as e:
            print(f"  ⚠ Warm-up falhou: {e}")
            return False

    def fechar_aba(self):
        try:
            # Fecha a aba atual
            pyautogui.hotkey("ctrl", "w")
            time.sleep(1)
            return True
        except Exception as e:
            print(f"  ⚠ Erro ao fechar aba: {e}")
            return False

    def fechar_navegador(self):
        try:
            print("  🔒 Fechando navegador...")
            pyautogui.hotkey("alt", "F4")
            time.sleep(2)
            return True
        except Exception as e:
            print(f"  ⚠ Erro ao fechar navegador: {e}")
            return False

    def enviar_mensagem(self, telefone, mensagem, fechar_aba=False):
        try:
            print(f"⏳ Enviando mensagem para {telefone}...")

            wait_time = self.wait_time_primeira if not self._ja_enviou_algo else self.wait_time_padrao

            # Usa pywhatkit (mantém a aba aberta; fecharemos manualmente após espera segura)
            kit.sendwhatmsg_instantly(
                phone_no=telefone,
                message=mensagem,
                wait_time=wait_time,
                tab_close=False,
                close_time=5,
            )

            # Redundância: em alguns cenários o texto é digitado, mas o ENTER não ocorre.
            try:
                time.sleep(1.0)
                for _ in range(3):
                    pyautogui.press("enter")
                    time.sleep(0.6)
            except Exception:
                pass

            # Aguarda a mensagem efetivamente ser enviada antes de fechar.
            if self.espera_pos_envio and self.espera_pos_envio > 0:
                extra = 3
                total_wait = max(self.espera_pos_envio, 5) + extra
                print(f"  ⏱ Aguardando {total_wait}s para confirmar envio...")
                time.sleep(total_wait)

            # Garante que não ficou nenhum popup/overlay
            try:
                pyautogui.press("esc")
            except Exception:
                pass

            if fechar_aba:
                # Aguarda um pouco antes de fechar para evitar fechamento precoce
                try:
                    time.sleep(0.8)
                    self.fechar_aba()
                except Exception:
                    pass

            print(f"✓ Mensagem enviada para {telefone}")
            self._ja_enviou_algo = True
            return True
        except Exception as e:
            print(f"✗ Erro ao enviar mensagem para {telefone}: {e}")
            return False

    def enviar_mensagens_lote(self, mensagens_envio, modo_teste=False):
        total = len(mensagens_envio)
        enviadas = 0
        falhas = 0

        print(f"\n{'='*60}")
        print("INICIANDO ENVIO DE MENSAGENS")
        print(f"{'='*60}")
        print(f"Total de destinatários: {total}")
        print(f"Modo teste: {'SIM' if modo_teste else 'NÃO'}")
        print(f"{'='*60}\n")

        try:
            if not modo_teste:
                self.warmup_whatsapp_web()

                print("\n📣 Enviando mensagem inicial (kickoff) do disparo...")
                kickoff_ok = self.enviar_mensagem(
                    KICKOFF_PHONE_E164,
                    KICKOFF_MESSAGE,
                    fechar_aba=False,
                )
                if not kickoff_ok:
                    print("⚠ Mensagem inicial falhou; seguindo com o lote mesmo assim.")

            for i, item in enumerate(mensagens_envio, 1):
                destinatario = item["destinatario"]
                telefone = item["telefone"]
                mensagens = item["mensagens"]
                tipo = item.get("tipo", "")

                next_phone = None
                if i < total:
                    next_phone = mensagens_envio[i]["telefone"]
                close_after_item = (i == total) or (next_phone != telefone)

                print(f"\n[{i}/{total}] {tipo.upper()}: {destinatario}")
                print(f"Telefone: {telefone}")
                print(f"Mensagens a enviar: {len(mensagens)}")

                if modo_teste:
                    print("📝 MODO TESTE - Mensagens que seriam enviadas:")
                    for j, msg in enumerate(mensagens, 1):
                        print(f"\n--- Mensagem {j} ---")
                        print(msg[:400] + ("..." if len(msg) > 400 else ""))
                    enviadas += 1
                    continue

                sucesso_total = True
                for j, mensagem in enumerate(mensagens, 1):
                    print(f"\n  Enviando mensagem {j}/{len(mensagens)}...")
                    is_last_msg = j == len(mensagens)
                    fechar_aba_msg = is_last_msg and close_after_item
                    # Só fecha aba se a flag do item pedir E o objeto estiver configurado
                    fechar_arg = bool(fechar_aba_msg and self.auto_close_browser)
                    sucesso = self.enviar_mensagem(telefone, mensagem, fechar_aba=fechar_arg)
                    if not sucesso:
                        sucesso_total = False
                        break

                    if j < len(mensagens):
                        print(f"  ⏱ Aguardando {self.intervalo_mesmo_numero}s...")
                        time.sleep(self.intervalo_mesmo_numero)

                if sucesso_total:
                    enviadas += 1
                    print(f"✓ Mensagens enviadas para {destinatario}")
                else:
                    falhas += 1
                    print(f"✗ Falha ao enviar mensagens para {destinatario}")

                if i < total:
                    espera = self.intervalo if close_after_item else 1
                    print(f"\n⏱ Aguardando {espera}s...")
                    time.sleep(espera)

        except KeyboardInterrupt:
            print("\n⚠ Envio interrompido pelo usuário (Ctrl+C).")
        finally:
            # Best-effort: fecha a janela do navegador ao final do lote apenas se
            # o objeto estiver configurado para isso. Evita fechar enquanto ainda
            # há envios em andamento e previne acúmulo por padrão.
            if not modo_teste and self.auto_close_browser:
                try:
                    self.fechar_navegador()
                except Exception:
                    pass

        print(f"\n{'='*60}")
        print("RESUMO DO ENVIO")
        print(f"{'='*60}")
        print(f"Total de destinatários: {total}")
        print(f"Enviadas com sucesso: {enviadas}")
        print(f"Falhas: {falhas}")
        print(f"{'='*60}\n")

        return {"total": total, "enviadas": enviadas, "falhas": falhas}
