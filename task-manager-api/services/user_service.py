"""Casos de uso de usuários: cadastro, atualização, remoção com dependentes e autenticação."""
import logging

from database import commit, db
from models.task import Task
from models.user import User
from utils.errors import AuthenticationError, ConflictError, ForbiddenError, NotFoundError
from utils.time import utcnow
from utils.validators import require_body, validate_email, validate_password, validate_role

logger = logging.getLogger(__name__)

USER_NOT_FOUND = 'Usuário não encontrado'
EMAIL_TAKEN = 'Email já cadastrado'
INVALID_CREDENTIALS = 'Credenciais inválidas'
INACTIVE_USER = 'Usuário inativo'


def get_user_or_404(user_id):
    user = User.get_by_id(user_id)
    if not user:
        raise NotFoundError(USER_NOT_FOUND)
    return user


def list_users():
    counts = Task.stats_by_user()
    result = []
    for user in User.list_all():
        data = user.to_dict()
        data['task_count'] = counts.get(user.id, (0, 0))[0]
        result.append(data)
    return result


def user_detail(user):
    data = user.to_dict()
    data['tasks'] = [task.to_dict() for task in Task.list_for_user(user.id)]
    return data


def user_tasks(user):
    now = utcnow()
    return [task.to_summary_dict(now) for task in Task.list_for_user(user.id)]


def create_user(fields):
    if User.find_by_email(fields['email']):
        raise ConflictError(EMAIL_TAKEN)
    validate_role(fields['role'])

    user = User(name=fields['name'], email=fields['email'], role=fields['role'])
    user.set_password(fields['password'])
    db.session.add(user)
    commit()
    logger.info('user created id=%s', user.id)
    return user


def update_user(user, data):
    """Checagens na mesma ordem do contrato original: e-mail (formato, unicidade), senha, role."""
    data = require_body(data)
    changes = {}
    if 'name' in data:
        changes['name'] = data['name']
    if 'email' in data:
        validate_email(data['email'])
        existing = User.find_by_email(data['email'])
        if existing and existing.id != user.id:
            raise ConflictError(EMAIL_TAKEN)
        changes['email'] = data['email']
    if 'password' in data:
        validate_password(data['password'], 'Senha muito curta')
    if 'role' in data:
        changes['role'] = validate_role(data['role'])
    if 'active' in data:
        changes['active'] = data['active']

    for key, value in changes.items():
        setattr(user, key, value)
    if 'password' in data:
        user.set_password(data['password'])
    commit()
    logger.info('user updated id=%s', user.id)
    return user


def delete_user(user):
    for task in Task.list_for_user(user.id):
        db.session.delete(task)
    db.session.delete(user)
    commit()
    logger.info('user deleted id=%s', user.id)


def authenticate(email, password):
    user = User.find_by_email(email)
    if not user or not user.check_password(password):
        raise AuthenticationError(INVALID_CREDENTIALS)
    if not user.active:
        raise ForbiddenError(INACTIVE_USER)
    commit()  # persiste o rehash transparente de senhas legadas, quando houver
    return user
