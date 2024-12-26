import random
from typing import Dict, List, Set
import json
import os
from datetime import datetime

COUNTRY_LIST = [
    "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan",
    "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi",
    "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo", "Costa Rica", "Croatia", "Cuba", "Cyprus", "Czech Republic",
    "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominica", "Dominican Republic",
    "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia",
    "Fiji", "Finland", "France",
    "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana",
    "Haiti", "Honduras", "Hungary",
    "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Ivory Coast",
    "Jamaica", "Japan", "Jordan",
    "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan",
    "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg",
    "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar",
    "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia", "Norway",
    "Oman",
    "Pakistan", "Palau", "Palestine", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal",
    "Qatar",
    "Romania", "Russia", "Rwanda",
    "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria",
    "Taiwan", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu",
    "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States", "Uruguay", "Uzbekistan",
    "Vanuatu", "Vatican City", "Venezuela", "Vietnam",
    "Yemen",
    "Zambia", "Zimbabwe"
]

class GameState:
    def __init__(self, countries: Dict[str, str]):
        self.countries = countries  # Dictionary mapping country names to colors
        self.revealed_tiles: Set[str] = set()  # Set of revealed country names
        self.current_turn = "blue"  # Start with blue's turn
        # Add new field for question history
        self.question_history: List[Dict[str, str]] = []
    
    def reveal_country(self, country: str) -> str:
        """Reveal the color of a country."""
        if country not in self.countries:
            raise ValueError(f"Country {country} not found")
        
        self.revealed_tiles.add(country)
        return self.countries[country]
    
    def get_visible_countries(self) -> List[str]:
        """Get list of all countries in the game."""
        return list(self.countries.keys())
    
    def get_unrevealed_countries(self) -> List[str]:
        """Get a dictionary of all countries in the game that have not been revealed."""
        return {country: color for country, color in self.countries.items() if country not in self.revealed_tiles}
    
    def get_revealed_tiles(self) -> Dict[str, str]:
        """Get dictionary of revealed countries and their colors."""
        return {country: self.countries[country] 
                for country in self.revealed_tiles}
    
    def end_turn(self) -> str:
        """Switch turns between red and blue."""
        self.current_turn = "red" if self.current_turn == "blue" else "blue"
        return self.current_turn
    
    def add_question(self, question: str, team: str, answer: str) -> None:
        """Add a question to the history."""
        self.question_history.append({
            'question': question,
            'team': team,
            'answer': answer,
            'timestamp': datetime.now().isoformat()
        })
    
    def get_question_history(self) -> List[Dict[str, str]]:
        """Get the history of questions."""
        return self.question_history
    
    def to_dict(self) -> dict:
        """Convert the game state to a dictionary for serialization."""
        return {
            'countries': self.countries,
            'revealed_tiles': list(self.revealed_tiles),
            'current_turn': self.current_turn,
            'question_history': self.question_history  # Add question history to serialization
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'GameState':
        """Create a GameState instance from a dictionary."""
        game_state = cls(data['countries'])
        game_state.revealed_tiles = set(data['revealed_tiles'])
        game_state.current_turn = data.get('current_turn', 'blue')
        game_state.question_history = data.get('question_history', [])  # Load question history
        return game_state

def create_new_game() -> GameState:
    """Create a new game with randomly assigned colors to countries."""
    # Randomly select 20 countries from the list
    selected_countries = random.sample(COUNTRY_LIST, 20)
    
    # Assign colors randomly
    colors = (
        ["blue"] * 7 +
        ["red"] * 7 +
        ["gray"] * 6
    )

    random.shuffle(colors)
    
    # Create country-color mapping
    countries = dict(zip(selected_countries, colors))
    
    return GameState(countries)

def save_game_state(game_id: str, game_state: GameState, storage_dir: str = "game_states") -> None:
    """Save game state to a file."""
    os.makedirs(storage_dir, exist_ok=True)
    file_path = os.path.join(storage_dir, f"{game_id}.json")
    
    with open(file_path, 'w') as f:
        json.dump(game_state.to_dict(), f)

def load_game_state(game_id: str, storage_dir: str = "game_states") -> GameState:
    """Load game state from a file."""
    file_path = os.path.join(storage_dir, f"{game_id}.json")
    
    if not os.path.exists(file_path):
        raise ValueError(f"Game {game_id} not found")
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    return GameState.from_dict(data)

def delete_game_state(game_id: str, storage_dir: str = "game_states") -> None:
    """Delete a game state file."""
    file_path = os.path.join(storage_dir, f"{game_id}.json")
    if os.path.exists(file_path):
        os.remove(file_path) 
