"""Hash e verificação de senha com a biblioteca já disponível (werkzeug, transitiva do Flask)."""
import hmac

from werkzeug.security import check_password_hash, generate_password_hash

_PREFIXOS_MODERNOS = ("scrypt:", "pbkdf2:")


def gerar_hash_senha(senha):
    return generate_password_hash(senha)


def verificar_senha(armazenada, informada):
    """Devolve (confere, precisa_rehash). Aceita o formato legado (texto puro) para migração transparente."""
    if not isinstance(armazenada, str) or not armazenada:
        return False, False
    if armazenada.startswith(_PREFIXOS_MODERNOS):
        return check_password_hash(armazenada, informada), False
    if hmac.compare_digest(armazenada.encode("utf-8"), informada.encode("utf-8")):
        return True, True
    return False, False
