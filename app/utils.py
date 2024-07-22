from hashlib import sha256


def url_to_id(url: str) -> str:
    return sha256(url.encode("UTF-8")).hexdigest()
