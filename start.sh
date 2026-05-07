#!/bin/bash
echo "Starting RouteAI Server..."
echo "Admin: http://localhost:8000/admin (admin / admin123)"
echo "App:   http://localhost:8000"
python manage.py runserver
