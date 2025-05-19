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
        if player and not player.hand:
            player.hand = game.deck.deal(2)

        print(f"🎴 Sending hand to {player.name}: {player.hand}")
        emit('player_hand', {"hand": player.hand}, room=request.sid)


@socketio.on('player_action')
def handle_action(data):
    print(f"⚡ Flask received action: {data}")

    game_id = data['game_id']
    if game_id in games:
        game = games[game_id]
        print("✅ Game found, processing action...")

        game.process_action(data['name'], data.get('action', ""), data.get('amount', 0))

        # 🏆 **Announce winner & trigger game reset immediately**
        if game.rounds[game.current_round] == "showdown":
            winner_data = {"winner": game.determine_winner(), "pot": game.pot}
            socketio.emit("game_result", winner_data)  # Send to all clients
            print(f"🎉 Winner announced: {winner_data}")

            # 🔄 **Immediately update the game state so UI syncs correctly**
            socketio.emit("game_state", game.get_state())

            # 🔄 **Start new game after 5 seconds**
            socketio.emit("start_new_game")
            return  # ✅ Prevent further actions from disrupting the state

        socketio.emit("game_state", game.get_state())  # ✅ Ensure UI updates properly


@socketio.on('start_new_game')
def start_new_game():
    global games
    game_id = max(games.keys(), key=lambda x: int(x.split("-")[-1]))  # Keep latest game
    game = games[game_id]  # 🔥 Keep existing game instead of overwriting

    game.start_game()  # 🔄 Reset the game state while keeping players

    socketio.emit("game_state", game.get_state())  # Broadcast fresh game state
    print("♻️ New round started with existing players!")



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
