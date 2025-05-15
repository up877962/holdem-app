from collections import Counter


def evaluate_hand(cards):
    """Evaluate hand strength (simplified)."""
    ranks = [card['rank'] for card in cards]
    suits = [card['suit'] for card in cards]

    rank_counts = Counter(ranks)
    most_common = rank_counts.most_common()

    if len(set(suits)) == 1:
        return "Flush"
    elif most_common[0][1] == 4:
        return "Four of a Kind"
    elif most_common[0][1] == 3 and most_common[1][1] == 2:
        return "Full House"
    elif most_common[0][1] == 3:
        return "Three of a Kind"
    elif most_common[0][1] == 2 and most_common[1][1] == 2:
        return "Two Pair"
    elif most_common[0][1] == 2:
        return "One Pair"
    else:
        return "High Card"
