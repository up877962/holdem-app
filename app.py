from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from poker.game import PokerGame

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

games = {}
waiting_players = {}  # ✅ Track players waiting for the next game


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

        # 🚫 Prevent joining mid-round, queue for next game instead
        if game.current_round > 0:
            if game_id not in waiting_players:
                waiting_players[game_id] = []  # ✅ Create queue for new players

            waiting_players[game_id].append(player_name)  # ✅ Add player to queue
            emit('join_error', {"message": "Game in progress! You'll be added to the next round."}, room=request.sid)
            return

        # ✅ If preflop, add player immediately
        game.add_player(player_name)
        player = game.get_player(player_name)

        if player and not player.hand:
            player.hand = game.deck.deal(2)  # 🎴 Ensure they get cards

        emit('game_state', game.get_state(), broadcast=True)
        emit('player_hand', {"hand": player.hand}, room=request.sid)
        print(f"🃏 {player.name} joined preflop and received: {player.hand}")





@socketio.on('player_action')
def handle_action(data):
    print(f"⚡ Flask received action: {data}")

    game_id = data['game_id']
    if game_id in games:
        game = games[game_id]
        print("✅ Game found, processing action...")

        game.process_action(data['name'], data.get('action', ""), data.get('amount', 0))

        active_players = [p for p in game.players if p.status != "folded"]

        # 🏆 **Check if only one player remains (Win by fold)**
        if len(active_players) == 1:
            winner_data = {"winner": active_players[0].name, "pot": game.pot}
            socketio.emit("game_result", winner_data)  # ✅ Show winner pop-up
            print(f"🎉 Winner announced due to fold: {winner_data}")

            socketio.emit("start_new_game")  # ✅ Restart game after fold
            return  # ✅ Prevent further action processing

        # 🏆 **Check if round reached showdown (Normal game end)**
        if game.rounds[game.current_round] == "showdown":
            winner_data = {"winner": game.determine_winner(), "pot": game.pot}
            socketio.emit("game_result", winner_data)  # ✅ Show winner pop-up
            print(f"🎉 Winner announced at showdown: {winner_data}")

            socketio.emit("start_new_game")  # ✅ Restart game after showdown
            return  # ✅ Prevent further action processing

        # 🔄 **Ensure UI refreshes properly during normal play**
        socketio.emit("game_state", game.get_state())





@socketio.on('start_new_game')
def start_new_game():
    global games, waiting_players

    game_id = max(games.keys(), key=lambda x: int(x.split("-")[-1]))  # Keep latest game
    game = games[game_id]

    game.start_game()  # 🔄 Reset the game state

    # ✅ Add waiting players from queue
    if game_id in waiting_players:
        for player_name in waiting_players[game_id]:
            game.add_player(player_name)
            print(f"✅ Queued player {player_name} added to new game.")

        waiting_players[game_id] = []  # Clear queue after players are added

    socketio.emit("game_state", game.get_state())  # Broadcast fresh game state
    print("♻️ New round started with queued + existing players!")





@socketio.on('leave_game')
def handle_leave(data):
    game_id = data['game_id']
    player_name = data['name']

    if game_id in games:
        game = games[game_id]
        game.players = [p for p in game.players if p.name != player_name]

        if not game.players:
            del games[game_id]

    socketio.emit("game_state", game.get_state())


if __name__ == '__main__':
    socketio.run(app, debug=True)
