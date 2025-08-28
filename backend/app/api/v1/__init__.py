from flask import Blueprint

bp = Blueprint('api_v1', __name__)

from . import nodes, tasks, results, alerts, auth, users, system_variables, reports, tenants


@bp.route('/health')
def health_check():
    """Health check endpoint"""
    return {'code': 0, 'data': 'OK', 'message': 'Service is running'}