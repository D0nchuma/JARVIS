"""Punto de entrada del asistente.

Mantené una ventana de consola abierta corriendo este script. Mantené
presionado el hotkey (por defecto Ctrl+Espacio) para hablarle; al soltarlo
(o tras el timeout) se transcribe lo que dijiste y se lo manda a Claude.
"""
import keyboard as kb

import config
import voice
from brain import Brain
from overlay import overlay


def main():
    overlay.start()
    brain = Brain()
    voice.speak(f"{config.ASSISTANT_NAME} listo. Mantené {config.PUSH_TO_TALK_HOTKEY} para hablarme.")
    print(f"Presioná y mantené '{config.PUSH_TO_TALK_HOTKEY}' para hablar. Ctrl+C para salir.")

    while True:
        try:
            kb.wait(config.PUSH_TO_TALK_HOTKEY)
            overlay.show("🎙️  Escuchando...")
            text = voice.listen()
            if not text:
                overlay.hide()
                continue

            if text.strip().lower() in {"salir", "chau", "adiós", "apagate"}:
                overlay.hide()
                voice.speak("Listo, nos vemos.")
                break

            overlay.update("🤔  Pensando...")
            reply = brain.chat(text)
            if reply:
                preview = reply if len(reply) <= 90 else reply[:87] + "..."
                overlay.update(f"💬  {preview}")
                voice.speak(reply)
            else:
                overlay.hide()

        except KeyboardInterrupt:
            overlay.hide()
            voice.speak("Listo, nos vemos.")
            break


if __name__ == "__main__":
    main()
