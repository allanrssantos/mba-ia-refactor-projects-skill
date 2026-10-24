"""Casos de uso de tasks: orquestra validação de referências, persistência e estatísticas."""
import logging

from database import commit, db
from models.category import Category
from models.task import Task
from models.user import User
from utils.constants import VALID_STATUSES
from utils.errors import NotFoundError
from utils.numbers import calculate_percentage
from utils.time import utcnow
from utils.validators import CREATE_DATE_MESSAGE, UPDATE_DATE_MESSAGE, parse_due_date

logger = logging.getLogger(__name__)

TASK_NOT_FOUND = 'Task não encontrada'
USER_NOT_FOUND = 'Usuário não encontrado'
CATEGORY_NOT_FOUND = 'Categoria não encontrada'


def get_task_or_404(task_id):
    task = Task.get_by_id(task_id)
    if not task:
        raise NotFoundError(TASK_NOT_FOUND)
    return task


def _ensure_user_exists(user_id):
    if user_id and not User.get_by_id(user_id):
        raise NotFoundError(USER_NOT_FOUND)


def _ensure_category_exists(category_id):
    if category_id and not Category.get_by_id(category_id):
        raise NotFoundError(CATEGORY_NOT_FOUND)


def list_tasks():
    now = utcnow()
    return [task.to_dict_with_relations(now) for task in Task.list_with_relations()]


def create_task(payload):
    _ensure_user_exists(payload['user_id'])
    _ensure_category_exists(payload['category_id'])
    due_date = parse_due_date(payload['due_date'], CREATE_DATE_MESSAGE) if payload['due_date'] else None

    task = Task(
        title=payload['title'],
        description=payload['description'],
        status=payload['status'],
        priority=payload['priority'],
        user_id=payload['user_id'],
        category_id=payload['category_id'],
        due_date=due_date,
        tags=payload['tags'],
    )
    db.session.add(task)
    commit()
    logger.info('task created id=%s', task.id)
    return task


def update_task(task, fields):
    if 'user_id' in fields:
        _ensure_user_exists(fields['user_id'])
    if 'category_id' in fields:
        _ensure_category_exists(fields['category_id'])
    if 'due_date' in fields:
        raw = fields['due_date']
        fields['due_date'] = parse_due_date(raw, UPDATE_DATE_MESSAGE) if raw else None

    for key, value in fields.items():
        setattr(task, key, value)
    task.updated_at = utcnow()
    commit()
    logger.info('task updated id=%s', task.id)
    return task


def delete_task(task):
    db.session.delete(task)
    commit()
    logger.info('task deleted id=%s', task.id)


def search_tasks(filters):
    return [task.to_dict() for task in Task.search(**filters)]


def task_stats():
    by_status = Task.count_by_status()
    total = Task.count_all()
    done = by_status.get('done', 0)
    stats = {'total': total}
    for status in VALID_STATUSES:
        stats[status] = by_status.get(status, 0)
    stats['overdue'] = Task.count_overdue(utcnow())
    stats['completion_rate'] = calculate_percentage(done, total)
    return stats
