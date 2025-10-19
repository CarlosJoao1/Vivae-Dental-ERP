# backend/routes/production/__init__.py
"""
Production Routes Package
NAV/BC-style production management endpoints
"""
from .masterdata import bp as masterdata_bp

__all__ = ['masterdata_bp']
