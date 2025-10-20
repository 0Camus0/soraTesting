"""
Sora 2 Web Application Module
==============================

Flask-based web interface for Sora 2 API.

Main Components:
    app: Flask application instance
    create_video_async: Asynchronous video creation handler
    remix_video_async: Asynchronous video remixing handler
"""

from .web_app import app

__all__ = ['app']
