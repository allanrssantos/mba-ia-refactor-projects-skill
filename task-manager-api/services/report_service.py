"""Relatórios agregados que cruzam tasks, usuários e categorias."""
from datetime import timedelta

from models.category import Category
from models.task import Task
from models.user import User
from utils.constants import PRIORITY_LABELS, RECENT_ACTIVITY_DAYS, VALID_STATUSES
from utils.numbers import calculate_percentage
from utils.time import utcnow


def summary_report():
    now = utcnow()
    by_status = Task.count_by_status()
    by_priority = Task.count_by_priority()

    overdue_tasks = Task.list_overdue(now)
    overdue_list = [
        {
            'id': task.id,
            'title': task.title,
            'due_date': str(task.due_date),
            'days_overdue': task.days_overdue(now),
        }
        for task in overdue_tasks
    ]

    since = now - timedelta(days=RECENT_ACTIVITY_DAYS)
    stats_by_user = Task.stats_by_user()
    user_stats = []
    for user in User.list_all():
        total, completed = stats_by_user.get(user.id, (0, 0))
        user_stats.append({
            'user_id': user.id,
            'user_name': user.name,
            'total_tasks': total,
            'completed_tasks': completed,
            'completion_rate': calculate_percentage(completed, total),
        })

    return {
        'generated_at': str(now),
        'overview': {
            'total_tasks': Task.count_all(),
            'total_users': User.count_all(),
            'total_categories': Category.count_all(),
        },
        'tasks_by_status': {status: by_status.get(status, 0) for status in VALID_STATUSES},
        'tasks_by_priority': {label: by_priority.get(level, 0) for level, label in PRIORITY_LABELS},
        'overdue': {
            'count': len(overdue_list),
            'tasks': overdue_list,
        },
        'recent_activity': {
            'tasks_created_last_7_days': Task.count_created_since(since),
            'tasks_completed_last_7_days': Task.count_completed_since(since),
        },
        'user_productivity': user_stats,
    }


def user_report(user):
    now = utcnow()
    tasks = Task.list_for_user(user.id)
    total = len(tasks)
    counts = {status: 0 for status in VALID_STATUSES}
    overdue = 0
    high_priority = 0
    for task in tasks:
        if task.status in counts:
            counts[task.status] += 1
        if task.is_high_priority():
            high_priority += 1
        if task.is_overdue(now):
            overdue += 1

    return {
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
        },
        'statistics': {
            'total_tasks': total,
            'done': counts['done'],
            'pending': counts['pending'],
            'in_progress': counts['in_progress'],
            'cancelled': counts['cancelled'],
            'overdue': overdue,
            'high_priority': high_priority,
            'completion_rate': calculate_percentage(counts['done'], total),
        },
    }
