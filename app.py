from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from poker.game import PokerGame

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

games = {}
waiting_players = {}  # ✅ Track players waiting for the next game
player_sessions = {}  # ✅ Map player names to their session IDs


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

        if game.current_round > 0:
            if game_id not in waiting_players:
                waiting_players[game_id] = []
            waiting_players[game_id].append(player_name)
            emit('join_error', {"message": "Game in progress! You'll be added to the next round."}, room=request.sid)
            return

        game.add_player(player_name)
        player_sessions[player_name] = request.sid  # ✅ Store player's session ID
        player = game.get_player(player_name)

        # ✅ Ensure player gets hole cards
        if player and not player.hand:
            player.hand = game.deck.deal(2)  # 🎴 Give two hole cards

        print(f"🃏 {player_name} joined and received: {player.hand}")

        # ✅ Now emit game state and player's hand properly
        emit('game_state', game.get_state())
        emit('player_hand', {"hand": player.hand}, room=request.sid)






@socketio.on('player_action')
def handle_action(data):
    print(f"⚡ Flask received action: {data}")

    game_id = data['game_id']
    if game_id in games:
        game = games[game_id]
        print("✅ Game found, processing action...")

        result = game.process_action(data['name'], data.get('action', ""), data.get('amount', 0))

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

        # 🏆 **Check for all-in or special win result**
        if result and isinstance(result, dict) and "winner" in result:
            socketio.emit("game_result", result)
            print(f"🎉 Winner announced (all-in/special): {result}")
            socketio.emit("start_new_game")
            return

        # 🔄 **Ensure UI refreshes properly during normal play**
        socketio.emit("game_state", game.get_state())





@socketio.on('start_new_game')
def start_new_game():
    global games, waiting_players

    if not games:  # ✅ Prevent calling max() on empty dict
        print("❌ No active games, skipping new game start.")
        return

    game_id = max(games.keys(), key=lambda x: int(x.split("-")[-1]))  # Keep latest game
    game = games[game_id]

    game.start_game()  # 🔄 Reset the game state

    # ✅ Add waiting players from queue
    if game_id in waiting_players:
        for player_name in waiting_players[game_id]:
            game.add_player(player_name)
            print(f"✅ Queued player {player_name} added to new game.")

        waiting_players[game_id] = []  # ✅ Clear queue after players are added

    socketio.emit("game_state", game.get_state())  # ✅ Broadcast fresh game state
    print("♻️ New round started with queued + existing players!")






@socketio.on('leave_game')
def handle_leave(data):
    game_id = data['game_id']
    player_name = data['name']

    if game_id in games:
        game = games[game_id]
        game.players = [p for p in game.players if p.name != player_name]

        # ✅ If no players remain, delete the game and notify clients
        if not game.players:
            del games[game_id]
            print(f"♻️ Game {game_id} removed since no players remain.")
            socketio.emit("game_deleted", {"game_id": game_id})  # ✅ Notify UI to remove game
        else:
            socketio.emit("game_state", game.get_state())  # ✅ Only emit if game still exists
    else:
        print(f"⚠️ Attempted to leave non-existent game {game_id}.")



@socketio.on('disconnect')
def handle_disconnect():
    player_sid = request.sid
    disconnected_player = None
    game_id = None

    # ✅ Find the player by their session ID
    for name, sid in player_sessions.items():
        if sid == player_sid:
            disconnected_player = name
            break

    if not disconnected_player:
        print(f"❌ Unknown session disconnected: {player_sid}")
        return

    # ✅ Remove from active sessions
    del player_sessions[disconnected_player]

    # ✅ Find their game and remove them
    for gid, game in games.items():
        if any(p.name == disconnected_player for p in game.players):
            game_id = gid
            break

    if game_id:
        game = games[game_id]
        game.players = [p for p in game.players if p.name != disconnected_player]
        print(f"❌ {disconnected_player} disconnected and removed from {game_id}")

        # ✅ If the disconnected player was up next, advance turn
        if game.get_current_player() and game.get_current_player().name == disconnected_player:
            game.next_turn()

        # ✅ If only one player remains, declare winner
        active_players = [p for p in game.players if p.status != "folded"]
        if len(active_players) == 1:
            winner = active_players[0]
            winner.award_winnings(game.pot)
            socketio.emit("game_result", {"winner": winner.name, "pot": game.pot})
            del games[game_id]

        socketio.emit("game_state", game.get_state())




if __name__ == '__main__':
    socketio.run(app, debug=True)
