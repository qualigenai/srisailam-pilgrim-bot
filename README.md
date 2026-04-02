# 🛕 Srisailam Pilgrim Bot

An open-source AI WhatsApp chatbot for Srisailam temple pilgrims — 
one of the twelve Jyotirlingas of Lord Shiva.

Built with love by a local boy from Srisailam. 
Dedicated to Lord Mallikarjuna Swamy & Bhramarambika Devi. 🙏

## Features
- Answers questions about temple timings, directions, sevas, rituals
- Supports Telugu, Hindi and English
- Routes booking queries to official channels
- Built on open-source stack — zero cost to run

## Tech Stack
- FastAPI + Python 3.12
- LangChain + ChromaDB (RAG pipeline)
- Groq API (Llama 3.1 — free tier)
- Twilio WhatsApp Sandbox
- sentence-transformers (multilingual embeddings)
- deep-translator (Telugu/Hindi support)

## Quick Start
```bash
git clone https://github.com/qualigenai/srisailam-pilgrim-bot
cd srisailam-pilgrim-bot
pip install -r requirements.txt
cp .env.example .env
# Fill in your API keys in .env
python ingest.py
python main.py
```

## Adding Your Temple
This bot is designed to work for any temple. 
Just replace the content in `knowledge_base/raw/` 
with your temple's information and run `python ingest.py`.

## Disclaimer
This is an unofficial community bot built by a Srisailam devotee.
Not affiliated with Srisailam Devasthanam.
For official bookings: srisailadevasthanam.org

## License
MIT License — Free to use, modify and distribute.
```

**File — `LICENSE`** (right-click project root → New → File):
```
MIT License

Copyright (c) 2024 qualigenai

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.