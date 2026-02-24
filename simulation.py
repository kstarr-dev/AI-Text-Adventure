"""SimulationRunner class for managing interactive Claude-powered adventures."""
import os
import json
import textwrap
from datetime import datetime
from typing import List, Dict

import anthropic

MODEL = "claude-sonnet-4-20250514"

SYSTEM_PROMPT_TEMPLATE = (
    "You are running an interactive simulation "
    "(the user chose option #{choice}). "
    "Your role is to:\n"
    "- Create an immersive, engaging experience\n"
    "- Respond to user actions with detailed, descriptive narration\n"
    "- Keep responses to 3-5 paragraphs maximum\n"
    "- Always end with a question or present choices for the user\n"
    "- Adapt the story based on user decisions\n"
    "- Make the experience dynamic and unpredictable"
)

GENERATION_PROMPT = (
    "Generate {count} creative and engaging simulation scenarios. "
    "Each should be unique and interactive. Format your response as a "
    "numbered list with:\n"
    "- A brief title (max 10 words)\n"
    "- A one-sentence description\n\n"
    "Example format:\n"
    "1. Fantasy City Mayor - Manage a magical city with dragons, "
    "wizards, and political intrigue.\n"
    "2. Zombie Apocalypse Survivor - Navigate a post-apocalyptic world "
    "and make survival decisions.\n\n"
    "Make them diverse and exciting!"
)

SETUP_PROMPT_TEMPLATE = (
    "The user has chosen simulation #{choice}. "
    "Begin this simulation with an engaging opening scene that sets "
    "the context and asks the user what they want to do first. "
    "Be descriptive and immersive."
)


class SimulationRunner:
    """Manages simulation state, API calls, and save/load operations."""

    def __init__(self, api_key: str, save_dir: str = "saved_simulations"):
        """Initialize the simulation runner with Anthropic API key."""
        self.client = anthropic.Anthropic(api_key=api_key)
        self.conversation_history: List[Dict[str, str]] = []
        self.system_prompt = ""
        self.save_dir = save_dir
        self.current_save_file = None
        self.simulation_title = ""
        self.terminal_width = 80
        os.makedirs(save_dir, exist_ok=True)

    def _send_message(self, messages, system=None, max_tokens=2048):
        """Send a message to the Claude API and return the response text."""
        kwargs = {"model": MODEL, "max_tokens": max_tokens, "messages": messages}
        if system:
            kwargs["system"] = system
        message = self.client.messages.create(**kwargs)
        return message.content[0].text

    def _wrap_paragraph(self, paragraph, width):
        """Wrap a single paragraph preserving internal newlines."""
        wrapped = []
        for line in paragraph.split('\n'):
            if not line.strip():
                wrapped.append('')
                continue
            wrapped.append(textwrap.fill(
                line, width=width,
                break_long_words=False,
                break_on_hyphens=False,
            ))
        return '\n'.join(wrapped)

    def wrap_text(self, text, width=None):
        """Wrap text to fit terminal width."""
        width = width or self.terminal_width
        paragraphs = text.split('\n\n')
        return '\n\n'.join(self._wrap_paragraph(p, width) for p in paragraphs)

    def print_wrapped(self, text, width=None):
        """Print text with wrapping."""
        print(self.wrap_text(text, width))

    def print_bordered(self, text, header=None):
        """Print text within a bordered section with optional header."""
        print("\n" + "=" * self.terminal_width)
        if header:
            print(header)
            print("=" * self.terminal_width)
        self.print_wrapped(text)
        print("=" * self.terminal_width + "\n")

    def list_saved_simulations(self) -> List[str]:
        """List all saved simulation files, most recent first."""
        if not os.path.exists(self.save_dir):
            return []
        saves = [f for f in os.listdir(self.save_dir) if f.endswith('.json')]
        return sorted(saves, reverse=True)

    def _generate_save_filename(self):
        """Generate a timestamped save filename from the simulation title."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(
            c for c in self.simulation_title
            if c.isalnum() or c in (' ', '-', '_')
        ).strip().replace(' ', '_')[:30]
        return f"{timestamp}_{safe_title}.json"

    def _build_save_data(self):
        """Build the save data dictionary."""
        return {
            "simulation_title": self.simulation_title,
            "system_prompt": self.system_prompt,
            "conversation_history": self.conversation_history,
            "last_saved": datetime.now().isoformat(),
        }

    def save_simulation(self):
        """Save the current simulation state to a JSON file."""
        if not self.current_save_file:
            self.current_save_file = self._generate_save_filename()
        save_path = os.path.join(self.save_dir, self.current_save_file)
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(self._build_save_data(), f, indent=2, ensure_ascii=False)
            print(f"\n💾 Simulation saved to: {self.current_save_file}")
            return True
        except Exception as e:
            print(f"\n❌ Error saving simulation: {e}")
            return False

    def _restore_state(self, save_data, save_file):
        """Restore simulation state from loaded data."""
        self.simulation_title = save_data.get("simulation_title", "Unknown")
        self.system_prompt = save_data.get("system_prompt", "")
        self.conversation_history = save_data.get("conversation_history", [])
        self.current_save_file = save_file

    def _display_recent_history(self):
        """Display the last few exchanges to remind the user."""
        print("\n" + "=" * self.terminal_width)
        print("STORY SO FAR (last 2 exchanges):")
        print("=" * self.terminal_width)
        for msg in self.conversation_history[-4:]:
            role = "YOU" if msg["role"] == "user" else "CLAUDE"
            content = msg["content"][:500]
            if len(msg["content"]) > 500:
                content += "..."
            print(f"\n[{role}]:")
            self.print_wrapped(content)
        print("=" * self.terminal_width + "\n")

    def load_simulation(self, save_file):
        """Load a saved simulation from a JSON file."""
        save_path = os.path.join(self.save_dir, save_file)
        try:
            with open(save_path, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
            self._restore_state(save_data, save_file)
            print(f"\n✅ Loaded simulation: {self.simulation_title}")
            print(f"Last saved: {save_data.get('last_saved', 'Unknown')}")
            self._display_recent_history()
            return True
        except Exception as e:
            print(f"\n❌ Error loading simulation: {e}")
            return False

    def generate_simulations(self, num_simulations=5):
        """Generate a list of simulation ideas using Claude."""
        prompt = GENERATION_PROMPT.format(count=num_simulations)
        try:
            text = self._send_message(
                [{"role": "user", "content": prompt}], max_tokens=1024,
            )
            self.print_bordered(text, header="AVAILABLE SIMULATIONS")
            return text
        except Exception as e:
            print(f"Error generating simulations: {e}")
            return None

    def _extract_title(self, simulations_text, choice):
        """Extract the simulation title for a given choice number."""
        for line in simulations_text.split('\n'):
            if line.strip().startswith(f"{choice}."):
                return line.strip()
        return f"Simulation #{choice}"

    def _initialize_simulation(self, choice, simulations_text):
        """Set up simulation state for a new game."""
        self.conversation_history = []
        self.simulation_title = self._extract_title(simulations_text, choice)
        self.system_prompt = SYSTEM_PROMPT_TEMPLATE.format(choice=choice)

    def start_simulation(self, choice, simulations_text):
        """Start the chosen simulation with an opening scene."""
        self._initialize_simulation(choice, simulations_text)
        setup_prompt = SETUP_PROMPT_TEMPLATE.format(choice=choice)
        try:
            opening = self._send_message(
                [{"role": "user", "content": setup_prompt}],
                system=self.system_prompt,
            )
            self.conversation_history.append({"role": "user", "content": setup_prompt})
            self.conversation_history.append({"role": "assistant", "content": opening})
            self.print_bordered(opening)
            self.save_simulation()
        except Exception as e:
            print(f"Error starting simulation: {e}")

    def process_user_action(self, user_input):
        """Process user input and return the next part of the simulation."""
        self.conversation_history.append({"role": "user", "content": user_input})
        try:
            response = self._send_message(
                self.conversation_history, system=self.system_prompt,
            )
            self.conversation_history.append({"role": "assistant", "content": response})
            self.save_simulation()
            return response
        except Exception as e:
            return f"Error processing action: {e}"
