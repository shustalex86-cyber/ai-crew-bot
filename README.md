# AI Crew Bot

Telegram multi-agent bot powered by Anthropic Claude. Routes messages to specialized agents based on task type.

## Agents

- **Оркестратор** — analyzes the request and briefs the right specialist
- **Программист** — writes code and answers technical questions
- **Копирайтер** — creates texts, posts, slogans, articles
- **Дизайнер** — gives UI/UX and design recommendations

All agents respond in Russian and remember the last 10 messages per user.

## Setup

1. Clone the repo
2. Copy `.env.example` to `.env` and fill in your tokens
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run:
   ```bash
   cd telegram-bot && python bot.py
   ```

## Commands

- `/start` — welcome message
- `/help` — usage examples
- `/clear` — reset conversation history

## Deployment (Railway / Heroku)

The included `Procfile` runs the bot as a worker process:
```
worker: cd telegram-bot && python bot.py
```
