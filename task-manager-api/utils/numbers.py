def calculate_percentage(part, total):
    if not total:
        return 0
    return round((part / total) * 100, 2)
