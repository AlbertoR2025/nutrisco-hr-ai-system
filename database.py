import sqlite3
import os
import psycopg2
from contextlib import contextmanager
from datetime import datetime

# Detectar si estamos en producción (Neon) o desarrollo (SQLite)
def get_db_connection():
    neon_url = os.getenv("NEON_DATABASE_URL")
    
    if neon_url:
        # Usar PostgreSQL en Neon
        return psycopg2.connect(neon_url)
    else:
        # Usar SQLite local (para desarrollo)
        conn = sqlite3.connect('data/local_chat.db', check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

def init_db(conn=None):
    if conn is None:
        conn = get_db_connection()
    
    cursor = conn.cursor()
    
    # Tablas SQLite/PostgreSQL compatibles
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    return conn

def save_chat(user_id, role, content):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO chats (user_id, role, content) VALUES (?, ?, ?)",
        (user_id, role, content)
    )
    
    conn.commit()
    conn.close()

def get_chat_history(user_id, limit=20):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """
        SELECT role, content, created_at 
        FROM chats 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT ?
        """,
        (user_id, limit)
    )
    
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {"role": row[0], "content": row[1], "time": row[2]}
        for row in reversed(rows)  # Ordenar ascendente
    ]