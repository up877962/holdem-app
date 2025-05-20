var socket = io.connect("http://localhost:5000");
var currentGameId = null;
var playerName = null;

// 🔄 Request available games on load
socket.emit("get_games");

// 🔄 Update game list dynamically
socket.on("update_games", function(gameList) {
    var gameListContainer = document.getElementById("game-list");
    gameListContainer.innerHTML = "";

    gameList.forEach(game => {
        let gameItem = document.createElement("li");
        gameItem.innerHTML = `${game} <button onclick="joinGame('${game}')">Join</button>`;
        gameListContainer.appendChild(gameItem);
    });
});

// 🔄 Create a new game
function createGame() {
    socket.emit("create_game");
}

// 🔄 Join an existing game
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

socket.on("game_state", function(data) {
    console.log("📡 Game State Updated:", data);

    document.getElementById("game-status").innerHTML = `💰 Pot: ${data.pot ?? 0}`;
    document.getElementById("turn-indicator").innerHTML = `🎭 Current Turn: ${data.current_player ?? "Waiting..."}`;
    document.getElementById("highest-bet").innerHTML = `💵 Highest Bet: ${data.highest_bet ?? 0}`;

    // 🔄 Display community cards
    let communityCardsContainer = document.getElementById("community-cards");
    communityCardsContainer.innerHTML = "<h3>Community Cards</h3>";
    if (data.community_cards && data.community_cards.length > 0) {
        data.community_cards.forEach(card => {
            let cardDiv = document.createElement("div");
            cardDiv.className = "card";
            cardDiv.innerHTML = `${card.rank} of ${card.suit}`;
            communityCardsContainer.appendChild(cardDiv);
        });
    } else {
        communityCardsContainer.innerHTML += "<p>No community cards yet.</p>";
    }

    // 🔄 Display players and their balances
    let playersContainer = document.getElementById("players-container");
    playersContainer.innerHTML = "<h3>Players</h3>";
    data.players.forEach(player => {
        let playerDiv = document.createElement("div");
        playerDiv.className = "player-info";
        playerDiv.innerHTML = `<strong>${player.name}</strong> - 🪙 Chips: ${player.chips} - ${player.status}`;
        playersContainer.appendChild(playerDiv);
    });

    // 🔄 Display player hand
    let playerHandContainer = document.getElementById("player-hand");
    playerHandContainer.innerHTML = "<h3>Your Hand</h3>";

    let currentPlayerData = data.players?.find(p => p.name === playerName);
    if (currentPlayerData && Array.isArray(currentPlayerData.hand) && currentPlayerData.hand.length > 0) {
        currentPlayerData.hand.forEach(card => {
            let cardDiv = document.createElement("div");
            cardDiv.className = "card";
            cardDiv.innerHTML = `${card.rank} of ${card.suit}`;
            playerHandContainer.appendChild(cardDiv);
        });
    } else {
        playerHandContainer.innerHTML += "<p>No cards yet.</p>";
        console.warn("❌ No hand data found for player:", playerName);
    }
});

// 🏆 Announce winner & auto-restart game
socket.on("game_result", function(data) {
    alert(`🏆 Winner: ${data.winner} | 💰 Pot: ${data.pot}`);

    setTimeout(() => {
        socket.emit("start_new_game");
    }, 5000);
});

// 🔄 Place a bet (Now updates UI instantly)
function placeBet() {
    if (!currentGameId || !playerName) {
        alert("❌ Error: No valid game or player detected.");
        return;
    }

    let betAmount = document.getElementById("betAmount").value;

    if (!betAmount || isNaN(betAmount) || betAmount <= 0) {
        alert("Please enter a valid bet amount!");
        return;
    }

    console.log(`🔵 Betting ${betAmount} chips`);
    socket.emit("player_action", {
        game_id: currentGameId,
        name: playerName,
        action: "raise",
        amount: parseInt(betAmount)
    });

    // 🔄 Instantly refresh game state for UI update
    socket.emit("get_game_state");
}

// 🔄 Call a bet (Now refreshes balance immediately)
function call() {
    console.log("🔵 Call button clicked! Sending action...");
    if (!currentGameId || !playerName) {
        console.error("❌ Call failed: Missing Game ID or Player Name!");
        return;
    }

    socket.emit("player_action", {
        game_id: currentGameId,
        name: playerName,
        action: "call"
    });

    // 🔄 Ensure UI updates instantly
    socket.emit("get_game_state");
}

// 🔄 Fold hand (Now updates balance correctly)
function fold() {
    if (!currentGameId || !playerName) return;
    console.log(`🚶‍♂️ ${playerName} folds`);
    socket.emit("player_action", { game_id: currentGameId, name: playerName, action: "fold" });

    // 🔄 Refresh game state to reflect balance after fold
    socket.emit("get_game_state");
}

// 🔄 Leave game
function leaveGame() {
    socket.emit("leave_game", { game_id: currentGameId, name: playerName });

    document.getElementById("game-container").style.display = "none";
    document.getElementById("game-selection").style.display = "block";
}
