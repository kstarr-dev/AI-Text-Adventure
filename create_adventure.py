"""Interactive simulation generator powered by Claude."""
import os
import json
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

from simulation import SimulationRunner

TERMINAL_WIDTH = 80


def _read_save_metadata(save_path):
    """Read title and last_saved timestamp from a save file."""
    with open(save_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    title = data.get("simulation_title", "Unknown")
    last_saved = data.get("last_saved", "Unknown")
    if last_saved != "Unknown":
        dt = datetime.fromisoformat(last_saved)
        last_saved = dt.strftime("%Y-%m-%d %H:%M")
    return title, last_saved


def _print_save_entry(idx, runner, save_file):
    """Print a single save file entry with title and date."""
    try:
        save_path = os.path.join(runner.save_dir, save_file)
        title, last_saved = _read_save_metadata(save_path)
        print(f"{idx}. {title}")
        print(f"   Last played: {last_saved}\n")
    except Exception:
        print(f"{idx}. {save_file}")


def display_saved_simulations(runner) -> Optional[str]:
    """Display saved simulations and let user choose one to load."""
    saved_sims = runner.list_saved_simulations()
    if not saved_sims:
        print("\nNo saved simulations found.")
        return None
    print("\n" + "=" * runner.terminal_width)
    print("SAVED SIMULATIONS")
    print("=" * runner.terminal_width)
    for idx, save_file in enumerate(saved_sims, 1):
        _print_save_entry(idx, runner, save_file)
    print("=" * runner.terminal_width)
    choice = input("\nEnter the number to load (or press Enter to skip): ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(saved_sims):
        return saved_sims[int(choice) - 1]
    return None


def _get_api_key():
    """Get the API key from environment or user input."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("\nNo API key found in environment variables.")
        api_key = input("Please enter your Anthropic API key: ").strip()
    return api_key


def _prompt_simulation_choice():
    """Prompt the user to pick a simulation number or quit."""
    while True:
        choice = input(
            "\nEnter the number of the simulation you want to play "
            "(or 'q' to quit): "
        ).strip()
        if choice.lower() == 'q':
            return None
        if choice.isdigit():
            return choice
        print("Please enter a valid number.")


def _try_load_saved(runner):
    """Attempt to load a saved simulation. Returns True if loaded."""
    save_file = display_saved_simulations(runner)
    if not save_file:
        return False
    if runner.load_simulation(save_file):
        print("\n✅ Simulation loaded! Continuing from where you left off...")
        return True
    print("\n❌ Failed to load simulation. Starting new simulation instead.")
    return False


def _start_new_simulation(runner):
    """Generate options and start a new simulation. Returns False to exit."""
    print("\nGenerating simulation options...\n")
    simulations = runner.generate_simulations()
    if not simulations:
        print("Failed to generate simulations. Exiting.")
        return False
    choice = _prompt_simulation_choice()
    if not choice:
        print("Thanks for playing! Goodbye.")
        return False
    print(f"\nStarting simulation #{choice}...\n")
    runner.start_simulation(choice, simulations)
    return True


def _handle_action(runner, user_action):
    """Process a single user action and display the response."""
    print("\nProcessing...\n")
    response = runner.process_user_action(user_action)
    print("=" * runner.terminal_width)
    runner.print_wrapped(response)
    print("=" * runner.terminal_width)


def _run_game_loop(runner):
    """Run the main game input loop."""
    print("\nCommands: 'quit'/'exit' to end | 'save' to manually save")
    print("(Note: The game auto-saves after each action)\n")
    while True:
        user_action = input("\nYour action: ").strip()
        if user_action.lower() in ('quit', 'exit', 'q'):
            print("\n💾 Saving before exit...")
            runner.save_simulation()
            print("\nEnding simulation. Thanks for playing!")
            break
        if user_action.lower() == 'save':
            runner.save_simulation()
            continue
        if not user_action:
            print("Please enter an action.")
            continue
        _handle_action(runner, user_action)


def main():
    """Main entry point for the simulation program."""
    print("=" * TERMINAL_WIDTH)
    print("INTERACTIVE SIMULATION GENERATOR")
    print("Powered by Claude (Anthropic)")
    print("=" * TERMINAL_WIDTH)
    api_key = _get_api_key()
    if not api_key:
        print("Error: API key is required to run this program.")
        return
    runner = SimulationRunner(api_key)
    runner.terminal_width = TERMINAL_WIDTH
    print("\nChecking for saved simulations...")
    loaded = _try_load_saved(runner)
    if not loaded and not _start_new_simulation(runner):
        return
    _run_game_loop(runner)


if __name__ == "__main__":
    main()
