from datetime import datetime, timezone


def utcnow():
    """UTC ingênuo: compatível com os valores já gravados e com a serialização via str()."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
