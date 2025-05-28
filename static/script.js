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

// 🃏 Game State Updates
socket.on("game_state", function(data) {
    // 🎭 Update turn and bet status
    document.getElementById("game-status").innerHTML = `💰 Pot: ${data.pot ?? 0}`;
    document.getElementById("turn-indicator").innerHTML = `🎭 Current Turn: ${data.current_player ?? "Waiting..."}`;
    document.getElementById("highest-bet").innerHTML = `💵 Highest Bet: ${data.highest_bet ?? 0}`;

    // 🃏 Update community cards
    let communityCardsContainer = document.getElementById("community-cards");
    communityCardsContainer.innerHTML = "<h3>Community Cards</h3>";
    if (data.community_cards?.length > 0) {
        data.community_cards.forEach(card => {
            let cardDiv = document.createElement("div");
            cardDiv.className = "card";
            cardDiv.innerHTML = `${card.rank} of ${card.suit}`;
            communityCardsContainer.appendChild(cardDiv);
        });
    }

    // 🃏 Update player hand
    let playerHandContainer = document.getElementById("player-hand");
    playerHandContainer.innerHTML = "<h3>Your Hand</h3>";
    let currentPlayerData = data.players?.find(p => p.name === playerName);
    if (currentPlayerData?.hand?.length > 0) {
        currentPlayerData.hand.forEach(card => {
            let cardDiv = document.createElement("div");
            cardDiv.className = "card";
            cardDiv.innerHTML = `${card.rank} of ${card.suit}`;
            playerHandContainer.appendChild(cardDiv);
        });
    }

    // 🔄 Restore player balances
    let playersContainer = document.getElementById("players-container");
    playersContainer.innerHTML = "<h3>Players & Balances</h3>";
    data.players.forEach(player => {
        let playerDiv = document.createElement("div");
        playerDiv.className = "player-info";
        playerDiv.innerHTML = `<strong>${player.name}</strong> - 🪙 Chips: ${player.chips} - ${player.status}`;
        playersContainer.appendChild(playerDiv);
    });
});


socket.on("game_deleted", function(data) {
    if (currentGameId === data.game_id) {
        document.getElementById("game-container").style.display = "none";
        document.getElementById("game-selection").style.display = "block";
        currentGameId = null;
        alert("Game has been removed as no players remained.");
    }

    // ✅ Remove game from the list without needing a manual refresh
    let gameListContainer = document.getElementById("game-list");
    let gameItems = gameListContainer.getElementsByTagName("li");

    for (let i = 0; i < gameItems.length; i++) {
        if (gameItems[i].innerText.includes(data.game_id)) {
            gameListContainer.removeChild(gameItems[i]);
            break;
        }
    }
});



// 🏆 Winner Announcement & Auto-Restart Game
socket.on("game_result", function(data) {
    socket.emit("start_new_game");

    let alertBox = document.createElement("div");
    alertBox.innerHTML = `🏆 Winner: ${data.winner} | 💰 Pot: ${data.pot}`;
    alertBox.className = "alert-box";
    document.body.appendChild(alertBox);

    setTimeout(() => { alertBox.style.opacity = 1; }, 100);
    setTimeout(() => {
        alertBox.style.opacity = 0;
        setTimeout(() => alertBox.remove(), 500);
    }, 5000);
});

// 🔄 Betting Functions
function placeBet() {
    let betAmount = document.getElementById("betAmount").value;
    if (!betAmount || isNaN(betAmount) || betAmount <= 0) {
        return showError("Invalid bet amount.");
    }

    socket.emit("player_action", {
        game_id: currentGameId,
        name: playerName,
        action: "raise",
        amount: parseInt(betAmount)
    });

    socket.emit("get_game_state");
}

function call() {
    socket.emit("player_action", { game_id: currentGameId, name: playerName, action: "call" });
    socket.emit("get_game_state");
}

function fold() {
    socket.emit("player_action", { game_id: currentGameId, name: playerName, action: "fold" });
    socket.emit("get_game_state");
}

// 🔄 Leave Game
function leaveGame() {
    socket.emit("leave_game", { game_id: currentGameId, name: playerName });
    document.getElementById("game-container").style.display = "none";
    document.getElementById("game-selection").style.display = "block";
}

socket.on("join_error", function(data) {
    alert(data.message); // 🚫 Notify the player that joining mid-game isn't allowed
});

