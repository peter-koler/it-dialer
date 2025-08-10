from flask import request, jsonify
from . import bp


@bp.route('/alerts', methods=['GET'])
def get_alerts():
    """Get all alerts"""
    # This is a placeholder implementation
    return jsonify({
        'code': 0,
        'data': [],
        'message': 'ok'
    })