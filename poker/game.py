from poker.deck import Deck
from poker.hand_evaluator import evaluate_hand
from poker.player import Player

class PokerGame:
    def __init__(self):
        self.players = []
        self.pot = 0
        self.community_cards = []
        self.current_turn = 0
        self.deck = Deck()
        self.rounds = ["preflop", "flop", "turn", "river", "showdown"]
        self.current_round = 0

    def add_player(self, name):
        if len(self.players) < 6:
            self.players.append(Player(name))

    def get_player(self, name):
        for player in self.players:
            if player.name == name:
                return player
        return None

    def start_game(self):
        """Start game with preflop hole cards."""
        self.deck = Deck()
        self.community_cards = []
        self.pot = 0
        self.current_round = 0

        for player in self.players:
            player.reset_for_new_game()
            player.hand = self.deck.deal(2)
            print(f"🃏 {player.name} received: {player.hand}")  # Debugging line

    def next_round(self):
        if self.current_round < len(self.rounds) - 1:
            self.current_round += 1
            if self.rounds[self.current_round] == "flop":
                self.community_cards.extend(self.deck.deal(3))
            elif self.rounds[self.current_round] in ["turn", "river"]:
                self.community_cards.append(self.deck.deal(1)[0])

    def process_action(self, name, action, amount=0):
        """Players make betting decisions (Raise, Call, Fold) correctly."""
        player = self.get_player(name)
        if not player:
            return

        if action == "fold":
            player.fold()
        elif action == "raise":
            player.bet(amount)
            self.pot += amount
        elif action == "call":
            highest_bet = max(p.bet_amount for p in self.players if p.status != "folded")
            call_amount = highest_bet - player.bet_amount

            if call_amount > 0:
                player.bet(call_amount)
                self.pot += call_amount

        player.has_acted = True

        # Advance round only if all non-folded players have acted
        active_players = [p for p in self.players if p.status != "folded"]
        if all(p.has_acted for p in active_players):
            self.next_round()

        for p in self.players:
            p.has_acted = False

    def get_state(self):
        return {
            "players": [{"name": p.name, "chips": p.chips, "status": p.status} for p in self.players],
            "pot": self.pot,
            "community_cards": [{"rank": c["rank"], "suit": c["suit"]} for c in self.community_cards],
            "current_turn": self.current_turn,
            "current_round": self.rounds[self.current_round],
        }

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

        return winner

