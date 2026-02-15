# LISA AI Voice Agent

## Overview

LISA AI Voice Agent is a modular Python application for building conversational voice agents designed to help users improve their language skills. It integrates speech-to-text (STT), text-to-speech (TTS), large language models (LLMs), and messaging platforms (Telegram, WhatsApp) to enable natural, context-aware voice interactions in any language. The project is designed for extensibility, supporting local and remote LLMs, and can be used for personal assistants, customer support bots, or research.

---

## Installing

#### Prerequisites
- Python 3.11+
- pip
- For now:
    - Local LLM installation (e.g., Ollama)
    - FFmpeg (for audio processing)

#### Clone the repository
- SSH
```bash
git clone git@github.com:VandersonTorres/ai-voice-agent.git
```
- HTTPS
```bash
git clone https://github.com/VandersonTorres/ai-voice-agent.git
```

- CD into the root:
```bash
cd ai-voice-agent
```

#### FFmpeg Installation
```bash
sudo apt install -y ffmpeg
```

#### Local LLM Installation
- [Ollama](https://ollama.com/) provides local LLMs. Install Ollama:
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

- Download Llama model 3 8B
```bash
ollama pull llama3:8b
```

- Start Ollama and pull a model (e.g., llama2):
```bash
ollama run llama3:8b
```

#### Install dependencies
```bash
pip install -r requirements.txt
```

#### Setup environment
- Copy `.env.sample` to `.env` and update your environment variables as needed.
```bash
cp .env.sample .env
```

- **TELEGRAM_BOT_TOKEN** is mandatory if you want to integrate with Telegram.

#### Telegram integration (Optional)

- Find @BotFather: In the search bar, type BotFather and select the official, verified account (it will have a blue checkmark next to the name).

- Start the Conversation: Tap on the Start button to initiate a chat with @BotFather.

- Create a New Bot: Send the command /newbot in the chat.

- Follow further instructions provided by Botfather so you can get your TELEGRAM_BOT_TOKEN

---

## Usage

#### Run the main application on Telegram mode
```bash
python -m app.main --use-telegram
```

#### Or run the app fully locally (without Telegram or WhatsApp integration)

You can choose whether to provide an audio as input, or just provide an input text:

- Provide an audio file in the `data/temp_audio` directory (e.g., `data/temp_audio/input.wav`).
```bash
python -m test.test_pipeline --input-filename <your_filename.ext>
```


- Provide a simple text input.
```bash
python -m test.test_pipeline --input-text "Hello, could you introduce yourself?"
```

## Modules Description

#### app/
- `main.py`: Entry point for the application.
- `config.py`: Configuration settings (API keys, endpoints, etc).
- `logging.py`: Logging setup.

#### audio/
- `formats.py`: Audio format utilities.

#### llm/
- `llm_api_client.py`: Handles LLM API requests (local/remote).
- `conversation_memory.py`: Stores conversation history.
- `conversation_state.py`: Tracks conversation state.
- `conversation_state_summarizer.py`: Summarizes conversation context.
- `conversation_topic_detector.py`: Detects conversation topics.
- `prompts.py`: Prompt templates for LLMs.

#### pipelines/
- `voice_pipeline.py`: Orchestrates voice input/output, STT, TTS, LLM.
- `text_pipeline.py`: Handles text-based interactions.

#### stt/
- `whisper_engine.py`: Speech-to-text engine using OpenAI Whisper.

#### tts/
- `edge_tts_engine.py`: Text-to-speech engine (Microsoft Edge TTS).
- `voices.py`: Voice selection utilities.

#### telegram/
- `runner.py`: Telegram bot runner.
- `handlers.py`: Telegram message handlers.

#### whatsapp/
- `runner.py`: WhatsApp bot runner.
- `handlers.py`: WhatsApp message handlers.
- `middlewares.py`: Middleware for WhatsApp events.

#### utils/
- Utility functions shared across modules.

## Summarization

The LISA AI Voice Agent project provides a flexible framework for building conversational agents with voice and text interfaces. It supports integration with local and remote LLMs, modular pipelines for STT/TTS, and messaging platforms. The codebase is organized for easy extension and customization, making it suitable for a wide range of conversational AI applications.


### PS:
The responses might delay up to 360 seconds, since it is a local prototype.
