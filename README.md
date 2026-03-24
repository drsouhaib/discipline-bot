# Discipline Bot

A Telegram bot for daily accountability, task tracking, and discipline reinforcement.

## Features

- Parse user's daily plan and track tasks
- Morning lock to ensure early start
- Periodic reminders for pending tasks
- Discipline score (0-100) with tiers
- Sleep tracking and weekly sleep score
- Focus timer, silent mode, alter ego, future you messages
- Weekly reports and failure pattern detection

## Setup

1. Clone the repository.
2. Create a `.env` file from `.env.example` and add your bot token.
3. Run `docker-compose up` to start the bot and PostgreSQL.

## Commands

- `/start` - start or reset bot
- `/done <task>` - mark task done
- `/missed <task>` - mark task missed
- `/status` - show today's progress
- `/focus [minutes]` - start focus timer
- `/stopfocus` - stop timer
- `/silent` - disable reminders
- `/loud` - enable reminders
- `/weekly` - weekly report
- `/score` - today's score
- `/export` - export all data
- `/delete` - delete all data

## License

Proprietary.