from collections import defaultdict


def normalize_name(name):
    """'Rahul  Patil.' and 'rahul patil' become the same text."""
    cleaned = name.lower().replace(".", "")
    return " ".join(cleaned.split())


def find_duplicate_groups(players):
    """Return groups of players that share a phone number or a name.

    A group is skipped when everyone in it was marked 'reviewed'.
    Each group is {"kind": "phone" or "name", "reason": text, "players": [...]}.
    """
    by_phone = defaultdict(list)
    by_name = defaultdict(list)
    for p in players:
        by_phone[p["phone"]].append(p)
        by_name[normalize_name(p["name"])].append(p)

    groups = []
    for phone, members in by_phone.items():
        if len(members) > 1 and any(not m["flag_dismissed"] for m in members):
            groups.append({"kind": "phone", "reason": f"Same phone: {phone}", "players": members})
    for name, members in by_name.items():
        if len(members) > 1 and any(not m["flag_dismissed"] for m in members):
            groups.append({"kind": "name", "reason": f"Same name: {name}", "players": members})
    groups.sort(key=lambda g: min(m["number"] for m in g["players"]))
    return groups