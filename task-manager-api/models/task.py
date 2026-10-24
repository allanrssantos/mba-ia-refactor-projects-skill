from sqlalchemy.orm import selectinload

from database import db
from utils.constants import (
    CLOSED_STATUSES,
    DEFAULT_PRIORITY,
    DEFAULT_STATUS,
    HIGH_PRIORITY_THRESHOLD,
    STATUS_DONE,
)
from utils.time import utcnow


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=DEFAULT_STATUS)
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', back_populates='tasks')
    category = db.relationship('Category', back_populates='tasks')

    # --- regras intrínsecas ---------------------------------------------------

    def is_overdue(self, now=None):
        now = now or utcnow()
        return bool(self.due_date and self.due_date < now and self.status not in CLOSED_STATUSES)

    def is_done(self):
        return self.status == STATUS_DONE

    def is_high_priority(self):
        return self.priority <= HIGH_PRIORITY_THRESHOLD

    def days_overdue(self, now=None):
        now = now or utcnow()
        return (now - self.due_date).days

    def tag_list(self):
        return self.tags.split(',') if self.tags else []

    # --- serialização ---------------------------------------------------------

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'user_id': self.user_id,
            'category_id': self.category_id,
            'created_at': str(self.created_at),
            'updated_at': str(self.updated_at),
            'due_date': str(self.due_date) if self.due_date else None,
            'tags': self.tag_list(),
        }

    def to_dict_with_overdue(self, now=None):
        data = self.to_dict()
        data['overdue'] = self.is_overdue(now)
        return data

    def to_dict_with_relations(self, now=None):
        data = self.to_dict_with_overdue(now)
        data['user_name'] = self.user.name if self.user else None
        data['category_name'] = self.category.name if self.category else None
        return data

    def to_summary_dict(self, now=None):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'created_at': str(self.created_at),
            'due_date': str(self.due_date) if self.due_date else None,
            'overdue': self.is_overdue(now),
        }

    # --- acesso a dados -------------------------------------------------------

    @classmethod
    def get_by_id(cls, task_id):
        return db.session.get(cls, task_id)

    @classmethod
    def list_all(cls):
        return db.session.execute(db.select(cls).order_by(cls.id)).scalars().all()

    @classmethod
    def list_with_relations(cls):
        stmt = db.select(cls).options(selectinload(cls.user), selectinload(cls.category)).order_by(cls.id)
        return db.session.execute(stmt).scalars().all()

    @classmethod
    def list_for_user(cls, user_id):
        return db.session.execute(db.select(cls).filter_by(user_id=user_id).order_by(cls.id)).scalars().all()

    @classmethod
    def search(cls, query=None, status=None, priority=None, user_id=None):
        stmt = db.select(cls)
        if query:
            stmt = stmt.filter(db.or_(cls.title.like(f'%{query}%'), cls.description.like(f'%{query}%')))
        if status:
            stmt = stmt.filter(cls.status == status)
        if priority is not None:
            stmt = stmt.filter(cls.priority == priority)
        if user_id is not None:
            stmt = stmt.filter(cls.user_id == user_id)
        return db.session.execute(stmt.order_by(cls.id)).scalars().all()

    @classmethod
    def list_overdue(cls, now=None):
        now = now or utcnow()
        stmt = (
            db.select(cls)
            .filter(cls.due_date.isnot(None), cls.due_date < now, cls.status.notin_(CLOSED_STATUSES))
            .order_by(cls.id)
        )
        return db.session.execute(stmt).scalars().all()

    @classmethod
    def count_all(cls):
        return db.session.scalar(db.select(db.func.count(cls.id))) or 0

    @classmethod
    def count_overdue(cls, now=None):
        now = now or utcnow()
        stmt = db.select(db.func.count(cls.id)).filter(
            cls.due_date.isnot(None), cls.due_date < now, cls.status.notin_(CLOSED_STATUSES)
        )
        return db.session.scalar(stmt) or 0

    @classmethod
    def count_by_status(cls):
        rows = db.session.execute(db.select(cls.status, db.func.count(cls.id)).group_by(cls.status)).all()
        return dict(rows)

    @classmethod
    def count_by_priority(cls):
        rows = db.session.execute(db.select(cls.priority, db.func.count(cls.id)).group_by(cls.priority)).all()
        return dict(rows)

    @classmethod
    def count_by_category(cls):
        rows = db.session.execute(db.select(cls.category_id, db.func.count(cls.id)).group_by(cls.category_id)).all()
        return dict(rows)

    @classmethod
    def count_created_since(cls, since):
        return db.session.scalar(db.select(db.func.count(cls.id)).filter(cls.created_at >= since)) or 0

    @classmethod
    def count_completed_since(cls, since):
        stmt = db.select(db.func.count(cls.id)).filter(cls.status == STATUS_DONE, cls.updated_at >= since)
        return db.session.scalar(stmt) or 0

    @classmethod
    def stats_by_user(cls):
        """{user_id: (total, concluídas)} em uma única consulta agregada."""
        done_case = db.case((cls.status == STATUS_DONE, 1), else_=0)
        stmt = db.select(cls.user_id, db.func.count(cls.id), db.func.sum(done_case)).group_by(cls.user_id)
        return {user_id: (total, int(done or 0)) for user_id, total, done in db.session.execute(stmt).all()}
