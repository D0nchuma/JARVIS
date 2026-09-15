"""Entrada de voz (speech-to-text) y salida de voz (text-to-speech).

STT: usa Google Web Speech API vía SpeechRecognition (necesita internet,
gratis y sin API key). Si más adelante querés algo 100% offline, se puede
reemplazar por faster-whisper sin tocar el resto del programa: solo hay
que cambiar la función `listen()`.

TTS: usa pyttsx3, que en Windows usa las voces SAPI5 ya instaladas
(no necesita internet ni API key).
"""
import speech_recognition as sr
import pyttsx3

_recognizer = sr.Recognizer()
_tts_engine = pyttsx3.init()
_tts_engine.setProperty("rate", 185)


def listen(timeout: int = 8, phrase_time_limit: int = 15) -> str | None:
    """Graba desde el micrófono y devuelve el texto transcripto (o None)."""
    with sr.Microphone() as source:
        _recognizer.adjust_for_ambient_noise(source, duration=0.5)
        print("🎙️  Escuchando...")
        try:
            audio = _recognizer.listen(
                source, timeout=timeout, phrase_time_limit=phrase_time_limit
            )
        except sr.WaitTimeoutError:
            return None

    try:
        text = _recognizer.recognize_google(audio, language="es-AR")
        print(f"🗣️  Vos: {text}")
        return text
    except sr.UnknownValueError:
        return None
    except sr.RequestError as e:
        print(f"⚠️  Error de reconocimiento de voz: {e}")
        return None


def speak(text: str) -> None:
    """Convierte texto a voz y lo reproduce."""
    print(f"🤖 Asistente: {text}")
    _tts_engine.say(text)
    _tts_engine.runAndWait()


def list_available_voices() -> None:
    """Utilidad para ver qué voces SAPI5 tenés instaladas en Windows."""
    for voice in _tts_engine.getProperty("voices"):
        print(voice.id, "-", voice.name)
