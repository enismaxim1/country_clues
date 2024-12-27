from flask import Flask, Response, request, jsonify
from flask_cors import CORS, cross_origin
from flask_limiter import Limiter
from game_logic import (
    GameState, create_new_game, save_game_state, 
    load_game_state, delete_game_state
)
import random
from ai import ask_question_to_ai
import logging
from datetime import datetime

app = Flask(__name__)
CORS(app, 
     resources={r"/api/*": {  # Apply to all /api/ routes
         "origins": ["http://localhost:3000"],  # Changed from "*" to specific origin
         "methods": ["GET", "POST", "DELETE", "OPTIONS"],
         "allow_headers": ["Content-Type", "Authorization"],
         "expose_headers": ["Content-Type", "Authorization"],
         "supports_credentials": True,
         "max_age": 3600  # Cache preflight requests for 1 hour
     }},
     supports_credentials=True)


# Set up logging immediately after imports
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add a test print and log
print("Flask app starting...")
logger.debug("Flask app initializing...")

@app.before_request
def log_request_info():
    print("=== BEFORE REQUEST ===")  # Debug marker
    print("Received request:", request.method, request.url)
    logger.debug('Headers: %s', dict(request.headers))
    logger.debug('Method: %s', request.method)
    logger.debug('URL: %s', request.url)
    logger.debug('IP: %s', get_client_ip())

WORD_LIST = [
    "bolt", "horse", "stick", "bracket", "cloud", "river", "stone", "wind",
    "flame", "tree", "star", "moon", "sun", "wave", "mountain", "bird",
    "leaf", "rain", "snow", "fish", "door", "book", "lamp", "chair",
    "table", "clock", "ship", "road", "bridge", "garden", "flower", "drum",
    "shell", "pearl", "lake", "forest", "beach", "cave", "cliff", "pond",
    "gate", "tower", "castle", "shield", "sword", "crown", "chest", "map",
    "compass", "torch", "crystal", "valley", "spring", "storm", "desert", "peak",
    "arrow", "wheel", "bell", "candle", "mirror", "basket", "rope", "key", "rune"
]



def get_client_ip():
    # Try to get IP from X-Forwarded-For header first (for proxy situations)
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0]
    # Fall back to remote_addr if no forwarded header
    return request.remote_addr

limiter = Limiter(
    app=app,
    key_func=get_client_ip,
    default_limits=["200 per day", "50 per hour"]
)


@app.after_request
def after_request(response):
    print("Response Headers:", dict(response.headers))  # Add print statement
    return response

@app.after_request
def log_response_info(response):
    logger.debug('Response Headers: %s', dict(response.headers))
    logger.debug('Response Status: %s', response.status)
    return response


@app.route('/api/game/create', methods=['POST'])
@limiter.limit("20 per minute; 200 per hour; 400 per day")
@cross_origin()
def create_game():
    game_id = '-'.join(random.sample(WORD_LIST, 3)).lower()
    game_state = create_new_game()
    save_game_state(game_id, game_state)
    return jsonify({'game_id': game_id})

@app.route('/api/game/<game_id>/state', methods=['GET'])
@limiter.limit("1000 per minute; 20000 per hour; 50000 per day")
@cross_origin()
def get_game_state(game_id):
    print("=== STATE ENDPOINT HIT ===")  # Debug marker
    logger.debug(f"Accessing state endpoint for game {game_id}")
    try:
        game_state = load_game_state(game_id)
        return jsonify({
            'countries': game_state.get_visible_countries(),
            'revealed_tiles': game_state.get_revealed_tiles(),
            'current_turn': game_state.current_turn,
            'question_history': game_state.get_question_history()
        })
    except ValueError:
        logger.error(f"Game not found: {game_id}")
        return jsonify({'error': 'Game not found'}), 404

@app.route('/api/game/<game_id>/reveal', methods=['POST'])
@limiter.limit("20 per minute; 200 per hour; 400 per day")
@cross_origin()
def reveal_country(game_id):
    try:
        game_state = load_game_state(game_id)
    except ValueError:
        return jsonify({'error': 'Game not found'}), 404
    
    data = request.get_json()
    country = data.get('country')
    
    if not country:
        return jsonify({'error': 'Country not specified'}), 400
    
    try:
        color = game_state.reveal_country(country)
        save_game_state(game_id, game_state)  # Save the updated state
        print("question history: ", game_state.get_question_history())
        return jsonify({
            'country': country,
            'color': color,
            'revealed_tiles': game_state.get_revealed_tiles(),
            'question_history': game_state.get_question_history()
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/game/<game_id>/question', methods=['POST'])
@limiter.limit("20 per minute; 100 per hour; 200 per day")
@cross_origin()
def ask_question(game_id):
    try:
        game_state = load_game_state(game_id)
    except ValueError:
        return jsonify({'error': 'Game not found'}), 404
    
    data = request.get_json()
    question = data.get('question')
    user_color = data.get('user_color')
    
    if not question:
        return jsonify({'error': 'Question not specified'}), 400
    
    answer = ask_question_to_ai(question, game_state.get_unrevealed_countries(), user_color)
    
    # Add question to history before getting AI response
    game_state.add_question(question, user_color, answer)
    # Save the updated game state with the new question
    save_game_state(game_id, game_state)
    
    return jsonify({
        'answer': answer,
        'question': question,
        'question_history': game_state.get_question_history()
    })

@app.route('/api/game/<game_id>/end-turn', methods=['POST'])
@limiter.limit("20 per minute; 200 per hour; 400 per day")
@cross_origin()
def end_turn(game_id):
    try:
        game_state = load_game_state(game_id)
    except ValueError:
        return jsonify({'error': 'Game not found'}), 404
    
    new_turn = game_state.end_turn()
    save_game_state(game_id, game_state)
    
    return jsonify({
        'current_turn': new_turn
    })

@app.route('/api/game/<game_id>', methods=['DELETE'])
@limiter.limit("20 per minute; 200 per hour; 400 per day")
@cross_origin()
def end_game(game_id):
    try:
        delete_game_state(game_id)
        return jsonify({'message': 'Game successfully ended'})
    except ValueError:
        return jsonify({'error': 'Game not found'}), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080) 