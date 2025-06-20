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
        # Blinds and dealer
        self.dealer_index = 0
        self.small_blind_amount = 10
        self.big_blind_amount = 20
        self.small_blind_index = 0
        self.big_blind_index = 0
        self.minimum_bet = self.big_blind_amount
        self.waiting_for_players = False  # Flag to indicate waiting state

    def add_player(self, name):
        if len(self.players) < 6:
            self.players.append(Player(name))
            print(f"✅ Player added: {name}. Current players: {[p.name for p in self.players]}")

    def get_player(self, name):
        for player in self.players:
            if player.name == name:
                return player
        return None

    def get_current_player(self):
        if not self.players or not (0 <= self.current_turn_index < len(self.players)):
            return None
        return self.players[self.current_turn_index]

    def next_turn(self):
        """Advances the turn order, skipping folded, all-in, or broke players."""
        active_players = [p for p in self.players if p.status != "folded"]

        if not active_players:
            print("🚫 No active players left—game should end!")
            return  # Prevent errors if everyone folds

        for _ in range(len(self.players)):
            self.current_turn_index = (self.current_turn_index + 1) % len(self.players)
            next_player = self.players[self.current_turn_index]
            if next_player.status not in ("folded", "all-in") and next_player.chips > 0:
                return
        print("⚠️ No eligible players left to act.")

    def start_game(self):
        """Start a new game, ensuring minimum player count and assign blinds."""
        # Exclude players with 0 chips
        self.players = [p for p in self.players if p.chips > 0]
        if len(self.players) < 2:
            print("❌ Not enough players to start the game! Waiting for more players.")
            # Optionally, set a waiting flag or notify frontend here
            self.waiting_for_players = True
            return
        self.waiting_for_players = False

        self.deck = Deck()  # ✅ Reset the deck to shuffle new cards
        self.community_cards = []
        self.pot = 0
        self.current_round = 0
        # Rotate dealer
        self.dealer_index = (self.dealer_index + 1) % len(self.players)
        self.small_blind_index = (self.dealer_index + 1) % len(self.players)
        self.big_blind_index = (self.dealer_index + 2) % len(self.players)
        self.current_turn_index = (self.dealer_index + 3) % len(self.players) if len(self.players) > 2 else self.big_blind_index
        self.minimum_bet = self.big_blind_amount

        for i, player in enumerate(self.players):
            player.reset_for_new_game()
            player.hand = self.deck.deal(2)  # 🎴 Ensure each player gets new hole cards
            print(f"🃏 {player.name} received: {player.hand}")

        # Post blinds
        sb_player = self.players[self.small_blind_index]
        bb_player = self.players[self.big_blind_index]
        sb_bet = sb_player.bet(self.small_blind_amount)
        bb_bet = bb_player.bet(self.big_blind_amount)
        self.pot += sb_bet + bb_bet
        print(f"💰 {sb_player.name} posts small blind ({sb_bet}), {bb_player.name} posts big blind ({bb_bet})")
        sb_player.has_acted = True
        bb_player.has_acted = True

        print("♻️ New round started with at least two players!")

    def process_action(self, name, action, amount=0):
        current_player = self.get_current_player()
        if not current_player or name != current_player.name:
            actual_turn = current_player.name if current_player else "(no player)"
            print(f"❌ Not {name}'s turn! It's {actual_turn}'s turn.")
            return

        if current_player.chips == 0 or current_player.status == "all-in":
            print(f"⛔ {name} cannot act (all-in or broke). Skipping.")
            self.next_turn()
            return

        print(f"🃏 Processing {name}'s action: {action}")

        highest_bet = max((p.bet_amount for p in self.players if p.status != "folded"), default=0)

        if action == "fold":
            current_player.fold()
        elif action == "raise":
            bet_amount = current_player.bet(min(amount, current_player.chips))
            self.pot += bet_amount
        elif action == "call":
            call_amount = min(highest_bet - current_player.bet_amount, current_player.chips)
            if call_amount > 0:
                bet_amount = current_player.bet(call_amount)
                self.pot += bet_amount
            # Mark as acted even if call_amount is 0 (checking)
        else:
            print(f"❌ Invalid action: {action}")
            return

        current_player.has_acted = True

        active_players = [p for p in self.players if p.status != "folded"]
        all_in_or_folded_or_broke = all(p.status in ("all-in", "folded") or p.chips == 0 for p in active_players)
        highest_bet = max((p.bet_amount for p in active_players), default=0)

        if len(active_players) == 1:
            winner = active_players[0]
            winner.award_winnings(self.pot)
            winner_data = {"winner": winner.name, "pot": self.pot}
            print(f"🎉 Winner announced due to fold: {winner_data}")
            self.start_game()  # Automatically start a new game
            return winner_data

        if all_in_or_folded_or_broke:
            print("🏁 All players are all-in, folded, or broke. Dealing out the board and proceeding to showdown!")
            while self.current_round < len(self.rounds) - 2:
                self.next_round()
            winner_name = self.determine_winner()
            result = {"winner": winner_name, "pot": self.pot}
            self.start_game()
            return result

        # Only advance round if all active players have acted and matched the highest bet
        if all(p.has_acted for p in active_players) and all(p.bet_amount == highest_bet for p in active_players):
            # If any player is all-in and no one can raise, go straight to showdown
            if any(p.status == "all-in" for p in active_players):
                print("🏁 All-in situation: dealing out the board and proceeding to showdown!")
                while self.current_round < len(self.rounds) - 2:
                    self.next_round()
                winner_name = self.determine_winner()
                result = {"winner": winner_name, "pot": self.pot}
                self.start_game()
                return result
            print("🔄 All players have acted, advancing round!")
            for p in self.players:
                p.has_acted = False  # Reset for next round
            self.next_round()
            return

        self.next_turn()

    def next_round(self):
        """Advance the game to the next round, ensuring correct indexing and turn order."""
        if self.current_round + 1 >= len(self.rounds):
            print("🏆 Game has reached showdown!")
            self.current_round = len(self.rounds) - 1
            return {"winner": self.determine_winner(), "pot": self.pot}

        self.current_round += 1
        print(f"🔄 Moving to next round: {self.rounds[self.current_round]}")

        if self.rounds[self.current_round] == "flop":
            self.community_cards.extend(self.deck.deal(3))
            print(f"🃏 Flop cards revealed: {self.community_cards}")
        elif self.rounds[self.current_round] in ["turn", "river"]:
            self.community_cards.append(self.deck.deal(1)[0])
            print(f"🃏 {self.rounds[self.current_round]} card added: {self.community_cards[-1]}")

        # Reset has_acted for all players
        for p in self.players:
            p.has_acted = False
        # Set turn to the next eligible player
        for idx, p in enumerate(self.players):
            if p.status not in ("folded", "all-in") and p.chips > 0:
                self.current_turn_index = idx
                break

    def determine_winner(self):
        """Evaluate the best poker hand and declare a winner, handling side pots only if needed."""
        eligible_players = [p for p in self.players if p.status != "folded"]
        if not eligible_players:
            return None

        # Check if all eligible players have the same bet amount (no side pot needed)
        bet_amounts = set(p.bet_amount for p in eligible_players)
        if len(bet_amounts) == 1:
            # Normal case: award the whole pot to the best hand
            best_hand = None
            best_players = []
            for player in eligible_players:
                hand_strength = evaluate_hand(player.hand + self.community_cards)
                if best_hand is None or hand_strength > best_hand:
                    best_hand = hand_strength
                    best_players = [player]
                elif hand_strength == best_hand:
                    best_players.append(player)
            share = self.pot // len(best_players)
            for winner in best_players:
                winner.award_winnings(share)
            remainder = self.pot % len(best_players)
            if remainder:
                best_players[0].award_winnings(remainder)
            names = ', '.join([p.name for p in best_players])
            print(f"🏆 Winner(s): {names}")
            return names

        # Otherwise, use side pot logic
        contributions = [(p, p.bet_amount) for p in self.players]
        pots = []
        while True:
            nonzero = [amt for _, amt in contributions if amt > 0]
            if not nonzero:
                break
            min_bet = min(nonzero)
            pot_players = [p for p, amt in contributions if amt > 0]
            pot_amount = min_bet * len(pot_players)
            pots.append((pot_players, pot_amount))
            contributions = [
                (p, amt - min_bet if amt > 0 else 0)
                for p, amt in contributions
            ]

        winners = []
        for pot_players, pot_amount in pots:
            best_hand = None
            best_players = []
            for player in pot_players:
                hand_strength = evaluate_hand(player.hand + self.community_cards)
                if best_hand is None or hand_strength > best_hand:
                    best_hand = hand_strength
                    best_players = [player]
                elif hand_strength == best_hand:
                    best_players.append(player)
            share = pot_amount // len(best_players)
            for winner in best_players:
                winner.award_winnings(share)
            winners.append((best_players, share))
            remainder = pot_amount % len(best_players)
            if remainder:
                best_players[0].award_winnings(remainder)
        main_pot_winners = winners[0][0] if winners else []
        if main_pot_winners:
            names = ', '.join([p.name for p in main_pot_winners])
            print(f"🏆 Winner(s): {names}")
            return names
        return None

    def get_state(self):
        highest_bet = max((p.bet_amount for p in self.players if p.status != "folded"), default=0)

        return {
            "players": [
                {
                    "name": p.name,
                    "chips": p.chips,
                    "status": p.status,
                    "bet_amount": p.bet_amount,
                    "call_amount": max(0, highest_bet - p.bet_amount),
                    "hand": [{"rank": c["rank"], "suit": c["suit"]} for c in p.hand] if isinstance(p.hand, list) and p.hand else []
                }
                for p in self.players if p.name and isinstance(p.hand, list)
            ],
            "pot": self.pot,
            "community_cards": [{"rank": c["rank"], "suit": c["suit"]} for c in self.community_cards] if self.community_cards else [],
            "current_round": self.rounds[self.current_round],
            "current_player": self.get_current_player().name if self.get_current_player() else None,
            "highest_bet": highest_bet,
            "dealer_index": self.dealer_index,
            "small_blind_index": self.small_blind_index,
            "big_blind_index": self.big_blind_index,
            "small_blind_amount": self.small_blind_amount,
            "big_blind_amount": self.big_blind_amount,
            "minimum_bet": self.minimum_bet,
        }
