class Player:
    def __init__(self, name, chips=100):
        self.name = name
        self.chips = chips
        self.hand = []
        self.status = "active"  # Can be "active", "folded", or "out"

    def bet(self, amount):
        """Place a bet"""
        if amount <= self.chips:
            self.chips -= amount
            return amount
        else:
            return 0  # Not enough chips

    def fold(self):
        """Player folds"""
        self.status = "folded"

    def reset_for_new_game(self):
        """Reset player status for a new round"""
        self.status = "active"
        self.hand = []
