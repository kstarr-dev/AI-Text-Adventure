# AI-Text-Adventure

A CLI text-based adventure game powered by Claude (Anthropic). The program generates a list of interactive simulation scenarios, then narrates an evolving story based on your decisions. Game state is automatically saved so you can quit and resume later.

## Prerequisites

- Python 3.8+
- An [Anthropic API key](https://console.anthropic.com/)

## Quick Start

1. Clone the repo and copy the environment template:

   ```bash
   cp .env.example .env
   ```

2. Add your API key to `.env`:

   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ```

3. Run the game:

   ```bash
   ./run.sh
   ```

   `run.sh` creates a virtual environment, installs dependencies, and launches the adventure. It is idempotent and safe to run repeatedly.

## Project Structure

```
create_adventure.py   # Entry point and CLI interface
simulation.py         # SimulationRunner class (API calls, save/load, text formatting)
run.sh                # Bootstrap script (venv + deps + launch)
.env.example          # API key template (tracked in git)
.env                  # Your actual API key (git-ignored)
```

## In-Game Commands

| Command | Action |
|---------|--------|
| *(any text)* | Perform an action in the simulation |
| `save` | Manually save progress |
| `quit` / `exit` / `q` | Save and exit |

The game auto-saves after every action.
