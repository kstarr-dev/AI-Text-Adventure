import anthropic
import os
import json
import textwrap
from datetime import datetime
from typing import List, Dict, Optional

class SimulationRunner:
    def __init__(self, api_key: str, save_dir: str = "saved_simulations"):
        """Initialize the simulation runner with Anthropic API key."""
        self.client = anthropic.Anthropic(api_key=api_key)
        self.conversation_history: List[Dict[str, str]] = []
        self.system_prompt = ""
        self.save_dir = save_dir
        self.current_save_file = None
        self.simulation_title = ""
        self.terminal_width = 80  # Default width, adjustable
        
        # Create save directory if it doesn't exist
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
    
    def wrap_text(self, text: str, width: int = None) -> str:
        """Wrap text to fit terminal width."""
        if width is None:
            width = self.terminal_width
        
        # Split by paragraphs (double newlines or single newlines)
        paragraphs = text.split('\n\n')
        wrapped_paragraphs = []
        
        for paragraph in paragraphs:
            # Handle single newlines within paragraphs
            lines = paragraph.split('\n')
            wrapped_lines = []
            
            for line in lines:
                if line.strip():
                    # Wrap each line
                    wrapped = textwrap.fill(line, width=width, 
                                           break_long_words=False,
                                           break_on_hyphens=False)
                    wrapped_lines.append(wrapped)
                else:
                    wrapped_lines.append('')
            
            wrapped_paragraphs.append('\n'.join(wrapped_lines))
        
        return '\n\n'.join(wrapped_paragraphs)
    
    def print_wrapped(self, text: str, width: int = None):
        """Print text with wrapping."""
        print(self.wrap_text(text, width))
    
    def list_saved_simulations(self) -> List[str]:
        """List all saved simulation files."""
        if not os.path.exists(self.save_dir):
            return []
        
        saves = [f for f in os.listdir(self.save_dir) if f.endswith('.json')]
        return sorted(saves, reverse=True)  # Most recent first
    
    def save_simulation(self):
        """Save the current simulation state to a file."""
        if not self.current_save_file:
            # Create a new save file name based on timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = "".join(c for c in self.simulation_title if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_title = safe_title.replace(' ', '_')[:30]  # Limit length
            self.current_save_file = f"{timestamp}_{safe_title}.json"
        
        save_data = {
            "simulation_title": self.simulation_title,
            "system_prompt": self.system_prompt,
            "conversation_history": self.conversation_history,
            "last_saved": datetime.now().isoformat()
        }
        
        save_path = os.path.join(self.save_dir, self.current_save_file)
        
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Simulation saved to: {self.current_save_file}")
            return True
        except Exception as e:
            print(f"\n❌ Error saving simulation: {e}")
            return False
    
    def load_simulation(self, save_file: str) -> bool:
        """Load a saved simulation from a file."""
        save_path = os.path.join(self.save_dir, save_file)
        
        try:
            with open(save_path, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
            
            self.simulation_title = save_data.get("simulation_title", "Unknown")
            self.system_prompt = save_data.get("system_prompt", "")
            self.conversation_history = save_data.get("conversation_history", [])
            self.current_save_file = save_file
            
            print(f"\n✅ Loaded simulation: {self.simulation_title}")
            print(f"Last saved: {save_data.get('last_saved', 'Unknown')}")
            
            # Display the last few messages to remind the user
            print("\n" + "="*self.terminal_width)
            print("STORY SO FAR (last 2 exchanges):")
            print("="*self.terminal_width)
            
            # Show last 4 messages (2 user actions + 2 assistant responses)
            recent_messages = self.conversation_history[-4:] if len(self.conversation_history) > 4 else self.conversation_history
            
            for msg in recent_messages:
                role = "YOU" if msg["role"] == "user" else "CLAUDE"
                content = msg["content"][:500] + "..." if len(msg["content"]) > 500 else msg["content"]
                print(f"\n[{role}]:")
                self.print_wrapped(content)
            
            print("="*self.terminal_width + "\n")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error loading simulation: {e}")
            return False
    
    def generate_simulations(self, num_simulations: int = 5) -> str:
        """Generate a list of simulation ideas using Claude."""
        prompt = f"""Generate {num_simulations} creative and engaging simulation scenarios. 
        Each should be unique and interactive. Format your response as a numbered list with:
        - A brief title (max 10 words)
        - A one-sentence description
        
        Example format:
        1. Fantasy City Mayor - Manage a magical city with dragons, wizards, and political intrigue.
        2. Zombie Apocalypse Survivor - Navigate a post-apocalyptic world and make survival decisions.
        
        Make them diverse and exciting!"""
        
        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            
            simulations_text = message.content[0].text
            print("\n" + "="*self.terminal_width)
            print("AVAILABLE SIMULATIONS")
            print("="*self.terminal_width)
            self.print_wrapped(simulations_text)
            print("="*self.terminal_width + "\n")
            
            return simulations_text
            
        except Exception as e:
            print(f"Error generating simulations: {e}")
            return None
    
    def start_simulation(self, choice: str, simulations_text: str):
        """Start the chosen simulation."""
        self.conversation_history = []
        
        # Extract simulation title for saving
        lines = simulations_text.split('\n')
        for line in lines:
            if line.strip().startswith(f"{choice}."):
                self.simulation_title = line.strip()
                break
        
        # Set up system prompt for the simulation
        self.system_prompt = f"""You are running an interactive simulation (the user chose option #{choice}). 
        Your role is to:
        - Create an immersive, engaging experience
        - Respond to user actions with detailed, descriptive narration
        - Keep responses to 3-5 paragraphs maximum
        - Always end with a question or present choices for the user
        - Adapt the story based on user decisions
        - Make the experience dynamic and unpredictable"""
        
        setup_prompt = f"""The user has chosen simulation #{choice}. 
        Begin this simulation with an engaging opening scene that sets the context 
        and asks the user what they want to do first. Be descriptive and immersive."""
        
        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                system=self.system_prompt,
                messages=[{"role": "user", "content": setup_prompt}]
            )
            
            opening = message.content[0].text
            
            # Initialize conversation history
            self.conversation_history.append({
                "role": "user",
                "content": setup_prompt
            })
            self.conversation_history.append({
                "role": "assistant",
                "content": opening
            })
            
            print("\n" + "="*self.terminal_width)
            self.print_wrapped(opening)
            print("="*self.terminal_width + "\n")
            
            # Auto-save the initial state
            self.save_simulation()
            
        except Exception as e:
            print(f"Error starting simulation: {e}")
    
    def process_user_action(self, user_input: str) -> str:
        """Process user input and get the next part of the simulation."""
        self.conversation_history.append({
            "role": "user",
            "content": user_input
        })
        
        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                system=self.system_prompt,
                messages=self.conversation_history
            )
            
            ai_response = message.content[0].text
            
            self.conversation_history.append({
                "role": "assistant",
                "content": ai_response
            })
            
            # Auto-save after each exchange
            self.save_simulation()
            
            return ai_response
            
        except Exception as e:
            return f"Error processing action: {e}"


def display_saved_simulations(runner: SimulationRunner) -> Optional[str]:
    """Display saved simulations and let user choose one."""
    saved_sims = runner.list_saved_simulations()
    
    if not saved_sims:
        print("\nNo saved simulations found.")
        return None
    
    print("\n" + "="*runner.terminal_width)
    print("SAVED SIMULATIONS")
    print("="*runner.terminal_width)
    
    for idx, save_file in enumerate(saved_sims, 1):
        # Try to read the title from the save file
        try:
            save_path = os.path.join(runner.save_dir, save_file)
            with open(save_path, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
            title = save_data.get("simulation_title", "Unknown")
            last_saved = save_data.get("last_saved", "Unknown")
            
            # Parse and format the datetime
            if last_saved != "Unknown":
                dt = datetime.fromisoformat(last_saved)
                last_saved = dt.strftime("%Y-%m-%d %H:%M")
            
            print(f"{idx}. {title}")
            print(f"   Last played: {last_saved}")
            print()
        except:
            print(f"{idx}. {save_file}")
    
    print("="*runner.terminal_width)
    
    choice = input("\nEnter the number to load (or press Enter to skip): ").strip()
    
    if choice.isdigit() and 1 <= int(choice) <= len(saved_sims):
        return saved_sims[int(choice) - 1]
    
    return None


def main():
    """Main function to run the simulation program."""
    terminal_width = 80  # You can adjust this value (60, 80, 100, 120, etc.)
    
    print("="*terminal_width)
    print("INTERACTIVE SIMULATION GENERATOR")
    print("Powered by Claude (Anthropic)")
    print("="*terminal_width)
    
    # Get API key from environment variable or user input
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        print("\nNo API key found in environment variables.")
        api_key = input("Please enter your Anthropic API key: ").strip()
    
    if not api_key:
        print("Error: API key is required to run this program.")
        return
    
    # Initialize the simulation runner
    runner = SimulationRunner(api_key)
    runner.terminal_width = terminal_width  # Set the width
    
    # Check for saved simulations
    print("\nChecking for saved simulations...")
    save_file = display_saved_simulations(runner)
    
    if save_file:
        # Load existing simulation
        if runner.load_simulation(save_file):
            print("\n✅ Simulation loaded! Continuing from where you left off...")
        else:
            print("\n❌ Failed to load simulation. Starting new simulation instead.")
            save_file = None
    
    if not save_file:
        # Generate new simulation options
        print("\nGenerating simulation options...\n")
        simulations = runner.generate_simulations()
        
        if not simulations:
            print("Failed to generate simulations. Exiting.")
            return
        
        # Get user's choice
        while True:
            choice = input("\nEnter the number of the simulation you want to play (or 'q' to quit): ").strip()
            
            if choice.lower() == 'q':
                print("Thanks for playing! Goodbye.")
                return
            
            if choice.isdigit():
                break
            else:
                print("Please enter a valid number.")
        
        # Start the chosen simulation
        print(f"\nStarting simulation #{choice}...\n")
        runner.start_simulation(choice, simulations)
    
    # Main simulation loop
    print("\nCommands: 'quit'/'exit' to end | 'save' to manually save")
    print("(Note: The game auto-saves after each action)\n")
    
    while True:
        user_action = input("\nYour action: ").strip()
        
        if user_action.lower() in ['quit', 'exit', 'q']:
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
        
        print("\nProcessing...\n")
        response = runner.process_user_action(user_action)
        
        print("="*terminal_width)
        runner.print_wrapped(response)
        print("="*terminal_width)


if __name__ == "__main__":
    main()