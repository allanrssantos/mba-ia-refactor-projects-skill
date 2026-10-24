"""Validação de entrada: funções puras que levantam ValidationError com as mensagens do projeto."""
import re
from datetime import datetime

from utils.constants import (
    DATE_FORMAT,
    DEFAULT_PRIORITY,
    DEFAULT_ROLE,
    DEFAULT_STATUS,
    MAX_PRIORITY,
    MAX_TITLE_LENGTH,
    MIN_PASSWORD_LENGTH,
    MIN_PRIORITY,
    MIN_TITLE_LENGTH,
    VALID_ROLES,
    VALID_STATUSES,
)
from utils.errors import ValidationError

EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$')
INVALID_BODY = 'Dados inválidos'
CREATE_DATE_MESSAGE = 'Formato de data inválido. Use YYYY-MM-DD'
UPDATE_DATE_MESSAGE = 'Formato de data inválido'


def require_body(data):
    """Corpo JSON presente e não vazio (comportamento original de `if not data`)."""
    if not isinstance(data, dict) or not data:
        raise ValidationError(INVALID_BODY)
    return data


def require_object(data):
    """Corpo JSON do tipo objeto (vazio permitido)."""
    if not isinstance(data, dict):
        raise ValidationError(INVALID_BODY)
    return data


# --- Task -------------------------------------------------------------------

def validate_title(title):
    if not isinstance(title, str):
        raise ValidationError('Título inválido')
    if len(title) < MIN_TITLE_LENGTH:
        raise ValidationError('Título muito curto')
    if len(title) > MAX_TITLE_LENGTH:
        raise ValidationError('Título muito longo')
    return title


def validate_status(status):
    if status not in VALID_STATUSES:
        raise ValidationError('Status inválido')
    return status


def validate_priority(priority):
    if not isinstance(priority, (int, float)) or priority < MIN_PRIORITY or priority > MAX_PRIORITY:
        raise ValidationError('Prioridade deve ser entre 1 e 5')
    return priority


def parse_due_date(value, message):
    try:
        return datetime.strptime(value, DATE_FORMAT)
    except (TypeError, ValueError):
        raise ValidationError(message)


def normalize_tags(tags):
    if isinstance(tags, list):
        try:
            return ','.join(tags)
        except TypeError:
            raise ValidationError('Tags inválidas')
    return tags


def validate_task_create(data):
    data = require_body(data)
    title = data.get('title')
    if not title:
        raise ValidationError('Título é obrigatório')
    validate_title(title)
    status = data.get('status', DEFAULT_STATUS)
    priority = data.get('priority', DEFAULT_PRIORITY)
    validate_status(status)
    validate_priority(priority)
    tags = data.get('tags')
    return {
        'title': title,
        'description': data.get('description', ''),
        'status': status,
        'priority': priority,
        'user_id': data.get('user_id'),
        'category_id': data.get('category_id'),
        'due_date': data.get('due_date'),
        'tags': normalize_tags(tags) if tags else None,
    }


def validate_task_update(data):
    """Valida só os campos enviados; `user_id`, `category_id` e `due_date` ficam brutos para o serviço resolver."""
    data = require_body(data)
    fields = {}
    if 'title' in data:
        fields['title'] = validate_title(data['title'])
    if 'description' in data:
        fields['description'] = data['description']
    if 'status' in data:
        fields['status'] = validate_status(data['status'])
    if 'priority' in data:
        fields['priority'] = validate_priority(data['priority'])
    for key in ('user_id', 'category_id', 'due_date'):
        if key in data:
            fields[key] = data[key]
    if 'tags' in data:
        fields['tags'] = normalize_tags(data['tags'])
    return fields


def _parse_int_filter(value, message):
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValidationError(message)


def validate_task_filters(args):
    filters = {}
    query = args.get('q', '')
    status = args.get('status', '')
    priority = args.get('priority', '')
    user_id = args.get('user_id', '')
    if query:
        filters['query'] = query
    if status:
        filters['status'] = status
    if priority:
        filters['priority'] = _parse_int_filter(priority, 'Prioridade inválida')
    if user_id:
        filters['user_id'] = _parse_int_filter(user_id, 'Usuário inválido')
    return filters


# --- User -------------------------------------------------------------------

def validate_email(email):
    if not isinstance(email, str) or not EMAIL_PATTERN.match(email):
        raise ValidationError('Email inválido')
    return email


def validate_password(password, message):
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(message)
    return password


def validate_role(role):
    if role not in VALID_ROLES:
        raise ValidationError('Role inválido')
    return role


def validate_user_create(data):
    """Checagens de campo na ordem original; unicidade de e-mail e role são verificados pelo serviço."""
    data = require_body(data)
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', DEFAULT_ROLE)
    if not name:
        raise ValidationError('Nome é obrigatório')
    if not email:
        raise ValidationError('Email é obrigatório')
    if not password:
        raise ValidationError('Senha é obrigatória')
    validate_email(email)
    validate_password(password, 'Senha deve ter no mínimo 4 caracteres')
    return {'name': name, 'email': email, 'password': password, 'role': role}


def validate_login(data):
    data = require_body(data)
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        raise ValidationError('Email e senha são obrigatórios')
    return {'email': email, 'password': password}


# --- Category ---------------------------------------------------------------

def validate_category_create(data):
    data = require_body(data)
    name = data.get('name')
    if not name:
        raise ValidationError('Nome é obrigatório')
    return {
        'name': name,
        'description': data.get('description', ''),
        'color': data.get('color'),
    }


def validate_category_update(data):
    data = require_object(data)
    return {key: data[key] for key in ('name', 'description', 'color') if key in data}
