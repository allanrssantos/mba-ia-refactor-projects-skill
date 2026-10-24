from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def commit():
    """Confirma a unidade de trabalho atual; em falha, desfaz e propaga para o error handler."""
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
