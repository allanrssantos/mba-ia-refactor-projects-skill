from flask import jsonify, request

from services import user_service
from utils import validators


def list_users():
    return jsonify(user_service.list_users()), 200


def get_user(user_id):
    user = user_service.get_user_or_404(user_id)
    return jsonify(user_service.user_detail(user)), 200


def create_user():
    fields = validators.validate_user_create(request.get_json())
    user = user_service.create_user(fields)
    return jsonify(user.to_dict()), 201


def update_user(user_id):
    user = user_service.get_user_or_404(user_id)
    user = user_service.update_user(user, request.get_json())
    return jsonify(user.to_dict()), 200


def delete_user(user_id):
    user = user_service.get_user_or_404(user_id)
    user_service.delete_user(user)
    return jsonify({'message': 'Usuário deletado com sucesso'}), 200


def get_user_tasks(user_id):
    user = user_service.get_user_or_404(user_id)
    return jsonify(user_service.user_tasks(user)), 200


def login():
    credentials = validators.validate_login(request.get_json())
    user = user_service.authenticate(credentials['email'], credentials['password'])
    return jsonify({
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': 'fake-jwt-token-' + str(user.id),
    }), 200
