#!/usr/bin/env python3
"""Initialize database before starting the application"""
from app import create_database_if_not_exists, init_db

if __name__ == '__main__':
    create_database_if_not_exists()
    init_db()
    print("Database initialized successfully")

