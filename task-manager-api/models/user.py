import hashlib
import hmac

from werkzeug.security import check_password_hash, generate_password_hash

from database import db
from utils.constants import DEFAULT_ROLE, ROLE_ADMIN
from utils.time import utcnow

_MODERN_HASH_PREFIXES = ('scrypt:', 'pbkdf2:')


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=DEFAULT_ROLE)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    tasks = db.relationship('Task', back_populates='user')

    PUBLIC_FIELDS = ('id', 'name', 'email', 'role', 'active')

    def to_dict(self):
        data = {field: getattr(self, field) for field in self.PUBLIC_FIELDS}
        data['created_at'] = str(self.created_at)
        return data

    # --- senha ----------------------------------------------------------------

    def set_password(self, raw):
        self.password = generate_password_hash(raw)

    def check_password(self, raw):
        """Verifica a senha; hashes MD5 legados são aceitos e regravados no formato novo.

        Retorna True/False; quando houve rehash, o chamador deve confirmar a sessão.
        """
        if self.password.startswith(_MODERN_HASH_PREFIXES):
            return check_password_hash(self.password, raw)
        legacy = hashlib.md5(raw.encode()).hexdigest()
        if hmac.compare_digest(self.password, legacy):
            self.set_password(raw)
            return True
        return False

    def is_admin(self):
        return self.role == ROLE_ADMIN

    # --- acesso a dados -------------------------------------------------------

    @classmethod
    def get_by_id(cls, user_id):
        return db.session.get(cls, user_id)

    @classmethod
    def find_by_email(cls, email):
        return db.session.execute(db.select(cls).filter_by(email=email)).scalars().first()

    @classmethod
    def list_all(cls):
        return db.session.execute(db.select(cls).order_by(cls.id)).scalars().all()

    @classmethod
    def count_all(cls):
        return db.session.scalar(db.select(db.func.count(cls.id))) or 0
