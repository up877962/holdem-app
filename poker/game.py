from poker.deck import Deck
from poker.hand_evaluator import evaluate_hand
from poker.player import Player


class PokerGame:
    def __init__(self):
        self.players = []
        self.pot = 0
        self.community_cards = []
        self.deck = Deck()
        self.rounds = ["preflop", "flop", "turn", "river", "showdown"]
        self.current_round = 0
        self.current_turn_index = 0  # 🔥 Track turn order

    def add_player(self, name):
        if len(self.players) < 6:
            self.players.append(Player(name))

    def get_player(self, name):
        for player in self.players:
            if player.name == name:
                return player
        return None

    def get_current_player(self):
        return self.players[self.current_turn_index] if self.players else None

    def next_turn(self):
        """Moves turn forward to the next active player."""
        active_players = [p for p in self.players if p.status != "folded"]
        if active_players:
            self.current_turn_index = (self.current_turn_index + 1) % len(active_players)
            print(f"👤 It's now {self.get_current_player().name}'s turn!")

    def start_game(self):
        """Start a new game, ensuring players persist while resetting their hands."""
        if not self.players:  # 🚨 If no players exist, do NOT reset the game!
            print("❌ Error: No players found! Can't start a new game without them.")
            return

        self.deck = Deck()  # 🔥 Reset deck
        self.community_cards = []  # 🔥 Clear old community cards
        self.pot = 0
        self.current_round = 0
        self.current_turn_index = 0

        # 🔄 Reset players WITHOUT removing them
        for player in self.players:
            player.reset_for_new_game()
            player.hand = self.deck.deal(2)  # 🔥 Assign new hole cards
            print(f"🃏 {player.name} received: {player.hand}")

        print("♻️ New round started! Players have been retained.")

    def process_action(self, name, action, amount=0):
        """Ensure actions follow turn order correctly."""
        current_player = self.get_current_player()

        if not current_player or name != current_player.name:
            print(f"❌ Not {name}'s turn! It's {current_player.name}'s turn.")
            return

        print(f"🃏 Processing {name}'s action: {action}")

        highest_bet = max((p.bet_amount for p in self.players if p.status != "folded"), default=0)

        if action == "fold":
            current_player.fold()
        elif action == "raise":
            current_player.bet(amount)
            self.pot += amount
        elif action == "call":
            call_amount = highest_bet - current_player.bet_amount
            if call_amount > 0:
                current_player.bet(call_amount)
                self.pot += call_amount

        current_player.has_acted = True

        active_players = [p for p in self.players if p.status != "folded"]
        if all(p.has_acted for p in active_players) and all(p.bet_amount == highest_bet for p in active_players):
            print("🔄 All players have acted, advancing round!")
            self.next_round()

        self.next_turn()

    def next_round(self):
        """Advance the game to the next round, ensuring correct indexing."""
        if self.current_round + 1 >= len(self.rounds):  # 🏁 Ensure showdown is reached at the right time
            print("🏆 Game has reached showdown!")
            self.current_round = len(self.rounds) - 1  # 🔥 Explicitly set to "showdown"
            return {"winner": self.determine_winner(), "pot": self.pot}

        self.current_round += 1  # ✅ Properly increment rounds before updating UI

        print(f"🔄 Moving to next round: {self.rounds[self.current_round]}")

        if self.rounds[self.current_round] == "flop":
            self.community_cards.extend(self.deck.deal(3))
            print(f"🃏 Flop cards revealed: {self.community_cards}")
        elif self.rounds[self.current_round] in ["turn", "river"]:
            self.community_cards.append(self.deck.deal(1)[0])
            print(f"🃏 {self.rounds[self.current_round]} card added: {self.community_cards[-1]}")

    def determine_winner(self):
        """Evaluate the best poker hand and declare a winner."""
        best_hand = None
        winner = None

        for player in self.players:
            if player.status != "folded":
                hand_strength = evaluate_hand(player.hand + self.community_cards)
                if not best_hand or hand_strength > best_hand:
                    best_hand = hand_strength
                    winner = player.name

        print(f"🏆 Winner determined: {winner}")
        return winner

    def get_state(self):
        if not self.players:  # 🚨 Prevent empty player lists from breaking the game
            print("❌ Error: No players found when updating game state!")
            return {"error": "No players found!"}

        highest_bet = max((p.bet_amount for p in self.players if p.status != "folded"), default=0)

        return {
            "players": [
                {
                    "name": p.name,
                    "chips": p.chips,
                    "status": p.status,
                    "bet_amount": p.bet_amount,
                    "call_amount": max(0, highest_bet - p.bet_amount),
                    "hand": [{"rank": c["rank"], "suit": c["suit"]} for c in p.hand] if isinstance(p.hand,
                                                                                                   list) and p.hand else []
                    # 🔥 Ensure hands are sent in game state
                }
                for p in self.players if p.name and isinstance(p.hand, list)
                # 🚨 Prevent including invalid/null players
            ],
            "pot": self.pot,
            "community_cards": [{"rank": c["rank"], "suit": c["suit"]} for c in
                                self.community_cards] if self.community_cards else [],
            "current_round": self.rounds[self.current_round],
            "current_player": self.get_current_player().name if self.get_current_player() else None,
            "highest_bet": highest_bet
        }




