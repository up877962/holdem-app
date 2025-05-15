from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from poker.game import PokerGame

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

games = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    emit('update_games', list(games.keys()))

@socketio.on('create_game')
def handle_create_game():
    game_id = f"game-{len(games) + 1}"
    games[game_id] = PokerGame()
    emit('update_games', list(games.keys()), broadcast=True)

@socketio.on('join_game')
def handle_join_game(data):
    game_id = data['game_id']
    player_name = data['name']

    if game_id in games:
        game = games[game_id]
        game.add_player(player_name)

        if len(game.players) >= 2:
            game.start_game()

        emit('game_state', game.get_state(), broadcast=True)

        player = game.get_player(player_name)
        if player:
            # 🔥 Fix: Ensure the hand is properly set before sending it
            if not player.hand:
                player.hand = game.deck.deal(2)

            print(f"🎴 Sending hand to {player.name}: {player.hand}")  # Debugging confirmation
            emit('player_hand', {"hand": player.hand}, room=request.sid)




@socketio.on('player_action')
def handle_action(data):
    game_id = data['game_id']
    if game_id in games:
        game = games[game_id]
        game.process_action(data['name'], data.get('action', ""), data.get('amount', 0))

        # Broadcast updated game state to all players
        emit('game_state', game.get_state(), broadcast=True)



@socketio.on('reveal')
def handle_reveal(data):
    game_id = data['game_id']
    if game_id in games:
        game = games[game_id]
        winner = game.determine_winner()
        emit('game_result', {"winner": winner, "pot": game.pot}, broadcast=True)
        emit('game_state', game.get_state(), broadcast=True)

@socketio.on('leave_game')
def handle_leave(data):
    game_id = data['game_id']
    player_name = data['name']

    if game_id in games:
        game = games[game_id]
        game.players = [p for p in game.players if p.name != player_name]

        if not game.players:
            del games[game_id]

    emit('update_games', list(games.keys()), broadcast=True)


if __name__ == '__main__':
    socketio.run(app, debug=True)
