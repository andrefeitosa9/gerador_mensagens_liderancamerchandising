"""Envio de mensagens pelo WhatsApp Web via pywhatkit.

Notas práticas:
- O pywhatkit abre o WhatsApp Web, digita e envia a mensagem.
- Para evitar que a aba seja fechada cedo demais (mensagem ainda "subindo"),
  aguardamos alguns segundos após o envio antes de fechar.
"""

import time

import pyautogui
import pywhatkit as kit


class WhatsAppSender:
    def __init__(self, intervalo_entre_mensagens=15, intervalo_mesmo_numero=8, espera_pos_envio=5):
        self.intervalo = intervalo_entre_mensagens
        self.intervalo_mesmo_numero = intervalo_mesmo_numero
        self.espera_pos_envio = espera_pos_envio

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

    def enviar_mensagem(self, telefone, mensagem, fechar_aba=True):
        try:
            print(f"⏳ Enviando mensagem para {telefone}...")

            # Mantém a aba aberta; fecharemos manualmente após uma espera segura.
            kit.sendwhatmsg_instantly(
                phone_no=telefone,
                message=mensagem,
                wait_time=20,
                tab_close=False,
                close_time=3,
            )

            # Aguarda a mensagem efetivamente ser enviada antes de fechar.
            if self.espera_pos_envio and self.espera_pos_envio > 0:
                print(f"  ⏱ Aguardando {self.espera_pos_envio}s para confirmar envio...")
                time.sleep(self.espera_pos_envio)

            # Garante que não ficou nenhum popup/overlay
            try:
                pyautogui.press("esc")
            except Exception:
                pass

            if fechar_aba:
                self.fechar_aba()

            print(f"✓ Mensagem enviada para {telefone}")
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
                    sucesso = self.enviar_mensagem(telefone, mensagem, fechar_aba=fechar_aba_msg)
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
            # Best-effort: fecha a janela do navegador ao final do lote para evitar acúmulo.
            # (Se não houver navegador em foco, não deve quebrar.)
            if not modo_teste:
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
