class Player:
    def __init__(self, name):
        self.name = name
        self.chips = 1000
        self.hand = []
        self.status = "active"
        self.has_acted = False  # NEW: Track if player has acted

    def fold(self):
        self.status = "folded"
        self.has_acted = True  # Mark as acted

    def bet(self, amount):
        self.chips -= amount
        self.has_acted = True  # Mark as acted
        return amount


    def reset_for_new_game(self):
        """Reset player status for a new round"""
        self.status = "active"
        self.hand = []
