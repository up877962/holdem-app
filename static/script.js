var socket = io.connect("http://localhost:5000");
var currentGameId = null;
var playerName = null;

socket.emit("get_games");

// Update the list of available games dynamically
socket.on("update_games", function(gameList) {
    console.log("🔄 Received updated game list:", gameList);
    var gameListContainer = document.getElementById("game-list");
    gameListContainer.innerHTML = "";

    gameList.forEach(game => {
        let gameItem = document.createElement("li");
        gameItem.innerHTML = `${game} <button onclick="joinGame('${game}')">Join</button>`;
        gameListContainer.appendChild(gameItem);
    });
});

function createGame() {
    console.log("🆕 Creating a new game...");
    socket.emit("create_game");
}

function joinGame(gameId) {
    playerName = prompt("Enter your name:");
    if (!playerName) return;

    currentGameId = gameId;

    document.getElementById("game-selection").style.display = "none";
    document.getElementById("game-container").style.display = "block";
    document.getElementById("game-title").innerHTML = `Game ID: ${gameId}`;

    console.log(`🔗 Joining game ${gameId} as ${playerName}`);
    socket.emit("join_game", { game_id: gameId, name: playerName });
}

// Update full game state for all players (community cards, players, chip counts)
socket.on("game_state", function(data) {
    console.log("🔄 Updated game state:", data);
    document.getElementById("game-status").innerHTML = `💰 Pot: ${data.pot} | 🔄 Current Round: ${data.current_round}`;

    // Update community cards
    let communityCardsContainer = document.getElementById("community-cards");
    communityCardsContainer.innerHTML = "<h3>Community Cards</h3>";

    if (!data.community_cards || data.community_cards.length === 0) {
        console.warn("❌ No community cards received!");
    } else {
        data.community_cards.forEach(card => {
            let cardDiv = document.createElement("div");
            cardDiv.className = "card";
            cardDiv.innerHTML = `${card.rank} of ${card.suit}`;
            communityCardsContainer.appendChild(cardDiv);
        });
    }

    // Update player list with chip counts (but no private hands)
    let playersContainer = document.getElementById("players");
    playersContainer.innerHTML = "<h3>Players</h3>";

    data.players.forEach(player => {
        let playerDiv = document.createElement("div");
        playerDiv.className = "player";
        playerDiv.innerHTML = `<h4>${player.name} (${player.chips} chips)</h4>`;
        playersContainer.appendChild(playerDiv);
    });
});

// Handle private hands (only sent to the current player)
socket.on("player_hand", function(data) {
    console.log("🎴 Received player's private hand:", data.hand);

    let playerHandContainer = document.getElementById("player-hand");
    playerHandContainer.innerHTML = "<h3>Your Hand</h3>";

    if (!data.hand || data.hand.length === 0) {
        console.error("❌ Hand data is missing!");
    } else {
        data.hand.forEach(card => {
            let cardDiv = document.createElement("div");
            cardDiv.className = "card";
            cardDiv.innerHTML = `${card.rank} of ${card.suit}`;
            playerHandContainer.appendChild(cardDiv);
        });
    }
});

// Handle betting actions (Rounds progress based on bets)
function placeBet(amount) {
    if (!currentGameId || !playerName) return;
    console.log(`💰 ${playerName} raises ${amount} chips`);
    socket.emit("player_action", { game_id: currentGameId, name: playerName, action: "raise", amount: amount });
}

function call() {
    if (!currentGameId || !playerName) return;
    console.log(`🔵 ${playerName} calls`);
    socket.emit("player_action", { game_id: currentGameId, name: playerName, action: "call" });
}

function fold() {
    if (!currentGameId || !playerName) return;
    console.log(`🚶‍♂️ ${playerName} folds`);
    socket.emit("player_action", { game_id: currentGameId, name: playerName, action: "fold" });
}

// Reveal the winner
function revealWinner() {
    if (!currentGameId) return;
    console.log("🏆 Revealing winner...");
    socket.emit("reveal", { game_id: currentGameId });
}

socket.on("game_result", function(data) {
    alert(`🏆 Winner: ${data.winner}\n💰 Total Pot: ${data.pot}`);
});
