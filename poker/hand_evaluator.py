from collections import Counter

def is_straight(ranks):
    """Check if ranks form a sequential straight."""
    rank_values = sorted([rank_to_value(r) for r in ranks])
    return rank_values == list(range(rank_values[0], rank_values[0] + 5))

def is_flush(suits):
    """Check if all suits are the same."""
    return len(set(suits)) == 1

def rank_to_value(rank):
    """Convert card rank to numeric value for easier evaluation."""
    rank_map = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6,
                '7': 7, '8': 8, '9': 9, '10': 10,
                'J': 11, 'Q': 12, 'K': 13, 'A': 14}
    return rank_map.get(rank, 0)

def evaluate_hand(cards):
    """Evaluate hand strength using full Texas Hold'em rules."""
    ranks = [card['rank'] for card in cards]
    suits = [card['suit'] for card in cards]

    rank_counts = Counter(ranks)
    most_common = rank_counts.most_common()

    flush = is_flush(suits)
    straight = is_straight(ranks)

    if flush and straight:
        return "Straight Flush"
    elif most_common[0][1] == 4:
        return "Four of a Kind"
    elif most_common[0][1] == 3 and most_common[1][1] == 2:
        return "Full House"
    elif flush:
        return "Flush"
    elif straight:
        return "Straight"
    elif most_common[0][1] == 3:
        return "Three of a Kind"
    elif most_common[0][1] == 2 and most_common[1][1] == 2:
        return "Two Pair"
    elif most_common[0][1] == 2:
        return "One Pair"
    else:
        return "High Card"

