from flask import Blueprint

v2_bp = Blueprint('v2', __name__, url_prefix='/api/v2')

# 导入所有v2 API模块
from . import tasks
from . import alerts
from . import api_alerts
from . import nodes
from . import results
from . import tenants
from . import reports