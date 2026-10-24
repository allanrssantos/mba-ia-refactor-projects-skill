import logging

_FORMATO = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def configurar_logging(nivel="INFO"):
    logging.basicConfig(level=getattr(logging, str(nivel).upper(), logging.INFO), format=_FORMATO)


def obter_logger(nome):
    return logging.getLogger(nome)
