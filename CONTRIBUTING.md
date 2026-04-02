# Contributing to Srisailam Pilgrim Bot 🛕

Thank you for helping make this bot better for pilgrims!

## How to adapt this for your temple

### Step 1 — Fork the repository
```bash
git clone https://github.com/qualigenai/srisailam-pilgrim-bot
cd srisailam-pilgrim-bot
```

### Step 2 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 3 — Configure your temple
Copy `.env.example` to `.env` and fill in your API keys:
```bash
cp .env.example .env
```

### Step 4 — Add your temple content
- Delete existing files in `knowledge_base/raw/`
- Create new `.txt` files with your temple's Q&As
- Follow this format:
```
Q: What time does temple open?
A: Temple opens at 6:00 AM...

Q: How to reach the temple?
A: The temple is located at...
```

### Step 5 — Build knowledge base
```bash
python ingest.py
```

### Step 6 — Run the bot
```bash
python main.py
```

## How to contribute to Srisailam bot

### Adding more Q&As
- Open `knowledge_base/raw/srisailam_faq.txt`
- Add new Q&A pairs in the same format
- Run `python ingest.py`
- Test your addition

### Reporting issues
- Open an issue on GitHub
- Describe the problem clearly
- Include the question that failed

### Suggesting improvements
- Open a GitHub issue with label `enhancement`
- Describe your suggestion

## Temple bots built with this framework
If you build a bot for your temple using this code,
please add it here by opening a PR!

| Temple | Location | Language | GitHub |
|--------|----------|----------|--------|
| Srisailam | Andhra Pradesh | Telugu/Hindi/English | [link](https://github.com/qualigenai/srisailam-pilgrim-bot) |

## Code of Conduct
This project is built with devotion for pilgrims.
Please be respectful and keep discussions constructive.

## License
MIT — Free to use, modify and share. 🙏