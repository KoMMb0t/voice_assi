# Voice Assistant - KI Sprachsteuerung

This project is a cross-device AI voice control system designed for both human and AI interaction. It features wake-word detection, speech-to-text, text-to-speech, and command execution. The initial prototype is built for a Windows 11 Mini PC, with plans to expand to Linux (Jetson Nano, Raspberry Pi), Android devices, and home automation integration.

---

Dieses Projekt ist eine geräteübergreifende KI-Sprachsteuerung, die sowohl für die menschliche als auch für die KI-Interaktion entwickelt wurde. Es verfügt über Wake-Word-Erkennung, Speech-to-Text, Text-to-Speech und Befehlsausführung. Der erste Prototyp wird für einen Windows 11 Mini PC entwickelt, mit Plänen zur Erweiterung auf Linux (Jetson Nano, Raspberry Pi), Android-Geräte und die Integration in die Hausautomation.

## Features

* **Wake-Word Detection:** Uses OpenWakeWord for reliable and low-resource wake-word detection. Currently uses "hey_jarvis" as a placeholder.
* **Speech-to-Text (STT):** Offline speech recognition using Vosk (German model).
* **Text-to-Speech (TTS):** Clear and natural-sounding speech synthesis using Edge TTS.
* **Voice Activity Detection (VAD):** Automatically detects when the user starts and stops speaking.
* **Command Execution:** Executes basic commands like opening applications (Calculator, YouTube) and providing the time and date.
* **Cross-Device Compatibility:** Designed to be expanded to multiple platforms, including Windows, Linux, and Android.
* **Decentralized Architecture:** Each device will act as an independent agent, avoiding a single point of failure.

## Features (Deutsch)

* **Wake-Word-Erkennung:** Verwendet OpenWakeWord für eine zuverlässige und ressourcenschonende Wake-Word-Erkennung. Derzeit wird "hey_jarvis" als Platzhalter verwendet.
* **Speech-to-Text (STT):** Offline-Spracherkennung mit Vosk (deutsches Modell).
* **Text-to-Speech (TTS):** Klare und natürlich klingende Sprachsynthese mit Edge TTS.
* **Voice Activity Detection (VAD):** Erkennt automatisch, wann der Benutzer zu sprechen beginnt und aufhört.
* **Befehlsausführung:** Führt grundlegende Befehle aus, wie das Öffnen von Anwendungen (Rechner, YouTube) und die Angabe von Uhrzeit und Datum.
* **Geräteübergreifende Kompatibilität:** Entwickelt, um auf mehrere Plattformen erweitert zu werden, einschließlich Windows, Linux und Android.
* **Dezentrale Architektur:** Jedes Gerät fungiert als unabhängiger Agent, um einen Single Point of Failure zu vermeiden.

## Tech Stack

* **Language:** Python 3.11
* **Wake Word:** OpenWakeWord
* **Speech-to-Text:** Vosk
* **Text-to-Speech:** Edge TTS
* **Voice Activity Detection:** webrtcvad
* **Audio Input:** sounddevice, numpy

## Getting Started

### Prerequisites

* Python 3.11
* Git

### Installation

1. Clone the repository:

   ```sh
   git clone https://github.com/KoMMb0t/voice_assi.git
   cd voice_assi
   ```

2. Create a virtual environment:

   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

## Usage

Run the main voice assistant script:

Contributing
Contributions are welcome! Please feel free to submit a pull request.
License
This project is licensed under the MIT License. See the LICENSE file for details.
