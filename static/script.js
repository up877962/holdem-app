var socket = io.connect("http://localhost:5000");
var currentGameId = null;
var playerName = null;

socket.emit("get_games");

socket.on("update_games", function(gameList) {
    var gameListContainer = document.getElementById("game-list");
    gameListContainer.innerHTML = "";

    gameList.forEach(game => {
        let gameItem = document.createElement("li");
        gameItem.innerHTML = `${game} <button onclick="joinGame('${game}')">Join</button>`;
        gameListContainer.appendChild(gameItem);
    });
});

function createGame() {
    socket.emit("create_game");
}

function joinGame(gameId) {
    playerName = prompt("Enter your name:");
    if (!playerName) return;

    currentGameId = gameId;

    document.getElementById("player-name").innerText = playerName;
    document.getElementById("game-selection").style.display = "none";
    document.getElementById("game-container").style.display = "block";
    document.getElementById("game-title").innerHTML = `Game ID: ${gameId}`;

    socket.emit("join_game", { game_id: gameId, name: playerName });
}

// Update game state for all players
socket.on("game_state", function(data) {
    document.getElementById("game-status").innerHTML = `💰 Pot: ${data.pot} | 🔄 Current Round: ${data.current_round}`;

    let communityCardsContainer = document.getElementById("community-cards");
    communityCardsContainer.innerHTML = "<h3>Community Cards</h3>";

    data.community_cards.forEach(card => {
        let cardDiv = document.createElement("div");
        cardDiv.className = "card";
        cardDiv.innerHTML = `${card.rank} of ${card.suit}`;
        communityCardsContainer.appendChild(cardDiv);
    });

    let playersContainer = document.getElementById("players");
    playersContainer.innerHTML = "<h3>Players</h3>";

    data.players.forEach(player => {
        let playerDiv = document.createElement("div");
        playerDiv.className = "player";
        playerDiv.innerHTML = `<h4>${player.name} (${player.chips} chips)</h4>`;
        playersContainer.appendChild(playerDiv);
    });
});

// Handle private hands (only for the current player)
socket.on("player_hand", function(data) {
    console.log("🎴 Received player's private hand:", data.hand);

    let playerHandContainer = document.getElementById("player-hand");
    playerHandContainer.innerHTML = "<h3>Your Hand</h3>";

    if (!data.hand || data.hand.length === 0) {
        console.error("❌ Player hand data is missing!");
    } else {
        data.hand.forEach(card => {
            let cardDiv = document.createElement("div");
            cardDiv.className = "card";
            cardDiv.innerHTML = `${card.rank} of ${card.suit}`;
            playerHandContainer.appendChild(cardDiv);
        });
    }
});



// Handle betting actions
function placeBet(amount) {
    if (!currentGameId || !playerName) return;
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


function revealWinner() {
    if (!currentGameId) return;
    console.log("🏆 Revealing winner...");
    socket.emit("reveal", { game_id: currentGameId });
}

// Leave game
function leaveGame() {
    socket.emit("leave_game", { game_id: currentGameId, name: playerName });

    document.getElementById("game-container").style.display = "none";
    document.getElementById("game-selection").style.display = "block";
}

// Reveal winner & restart game automatically
socket.on("game_result", function(data) {
    alert(`🏆 Winner: ${data.winner}\n💰 Total Pot: ${data.pot}`);
});
