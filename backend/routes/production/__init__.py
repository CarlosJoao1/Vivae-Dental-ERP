# backend/routes/production/__init__.py
"""
Production Routes Package
NAV/BC-style production management endpoints
"""
from .masterdata import bp as masterdata_bp
from .bom import bp as bom_bp
from .routing import bp as routing_bp
from .work_centers import bp as work_centers_bp
from .production_orders import bp as production_orders_bp

__all__ = ['masterdata_bp', 'bom_bp', 'routing_bp', 'work_centers_bp', 'production_orders_bp']
