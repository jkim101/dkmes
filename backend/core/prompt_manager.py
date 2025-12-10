import json
import os
from typing import Dict, Optional

class PromptManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PromptManager, cls).__new__(cls)
            cls._instance.prompts = {}
            cls._instance.prompts_file = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 
                "data", 
                "prompts.json"
            )
            cls._instance.load_prompts()
        return cls._instance

    def load_prompts(self):
        """Load prompts from the JSON file."""
        if os.path.exists(self.prompts_file):
            try:
                with open(self.prompts_file, 'r', encoding='utf-8') as f:
                    self.prompts = json.load(f)
                print(f"Loaded {len(self.prompts)} prompts from {self.prompts_file}")
            except Exception as e:
                print(f"Error loading prompts: {e}")
                self.prompts = {}
        else:
            print(f"Prompts file not found at {self.prompts_file}")
            self.prompts = {}

    def save_prompts(self):
        """Save current prompts to the JSON file."""
        try:
            with open(self.prompts_file, 'w', encoding='utf-8') as f:
                json.dump(self.prompts, f, indent=4, ensure_ascii=False)
            print("Prompts saved successfully.")
        except Exception as e:
            print(f"Error saving prompts: {e}")

    def get_template(self, name: str) -> str:
        """Get a prompt template by name."""
        return self.prompts.get(name, "")

    def update_template(self, name: str, content: str):
        """Update a specific prompt template and save to disk."""
        self.prompts[name] = content
        self.save_prompts()

    def list_prompts(self) -> Dict[str, str]:
        """Return all prompts."""
        return self.prompts
