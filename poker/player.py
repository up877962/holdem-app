class Player:
    def __init__(self, name):
        self.name = name
        self.chips = 1000
        self.hand = []
        self.status = "active"
        self.has_acted = False
        self.bet_amount = 0  # Track the current bet amount

    def reset_for_new_game(self):
        """Reset player state for a new hand."""
        self.status = "active"
        self.hand = []
        self.has_acted = False
        self.bet_amount = 0  # Reset bet amount

    def fold(self):
        """Marks the player as folded for this round."""
        self.status = "folded"
        self.has_acted = True

    def bet(self, amount):
        """Places a bet, preventing bets larger than available chips."""
        if amount > self.chips:
            print(f"❌ {self.name} can't bet {amount}, insufficient chips!")
            return 0  # Prevent betting more than available chips
        self.chips -= amount
        self.bet_amount += amount  # Track total bet for matching calls
        self.has_acted = True
        return amount

    def award_winnings(self, amount):
        """Credit winnings to the player's balance, handling split pots."""
        self.chips += amount
        print(f"💰 {self.name} received {amount} chips! New balance: {self.chips}")

    def __repr__(self):
        """Provides a cleaner string representation for debugging."""
        return f"Player({self.name}, Chips: {self.chips}, Status: {self.status}, Bet: {self.bet_amount})"
