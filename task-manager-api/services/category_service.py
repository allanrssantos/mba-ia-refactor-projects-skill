import logging

from database import commit, db
from models.category import Category
from models.task import Task
from utils.constants import DEFAULT_COLOR
from utils.errors import NotFoundError

logger = logging.getLogger(__name__)

CATEGORY_NOT_FOUND = 'Categoria não encontrada'


def get_category_or_404(category_id):
    category = Category.get_by_id(category_id)
    if not category:
        raise NotFoundError(CATEGORY_NOT_FOUND)
    return category


def list_categories():
    counts = Task.count_by_category()
    result = []
    for category in Category.list_all():
        data = category.to_dict()
        data['task_count'] = counts.get(category.id, 0)
        result.append(data)
    return result


def create_category(fields):
    category = Category(
        name=fields['name'],
        description=fields['description'],
        color=fields['color'] if fields['color'] is not None else DEFAULT_COLOR,
    )
    db.session.add(category)
    commit()
    logger.info('category created id=%s', category.id)
    return category


def update_category(category, fields):
    for key, value in fields.items():
        setattr(category, key, value)
    commit()
    logger.info('category updated id=%s', category.id)
    return category


def delete_category(category):
    db.session.delete(category)
    commit()
    logger.info('category deleted id=%s', category.id)
