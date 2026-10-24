from flask import jsonify, request

from services import task_service
from utils import validators


def list_tasks():
    return jsonify(task_service.list_tasks()), 200


def get_task(task_id):
    task = task_service.get_task_or_404(task_id)
    return jsonify(task.to_dict_with_overdue()), 200


def create_task():
    payload = validators.validate_task_create(request.get_json())
    task = task_service.create_task(payload)
    return jsonify(task.to_dict()), 201


def update_task(task_id):
    task = task_service.get_task_or_404(task_id)
    fields = validators.validate_task_update(request.get_json())
    task = task_service.update_task(task, fields)
    return jsonify(task.to_dict()), 200


def delete_task(task_id):
    task = task_service.get_task_or_404(task_id)
    task_service.delete_task(task)
    return jsonify({'message': 'Task deletada com sucesso'}), 200


def search_tasks():
    filters = validators.validate_task_filters(request.args)
    return jsonify(task_service.search_tasks(filters)), 200


def task_stats():
    return jsonify(task_service.task_stats()), 200
