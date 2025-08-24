import sqlite3
from datetime import datetime

def init_db():
    """Инициализация базы данных"""
    conn = sqlite3.connect('trading_bot.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        current_day INTEGER DEFAULT 1,
        completed_lessons TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()

def get_user(user_id):
    """Получить пользователя"""
    conn = sqlite3.connect('trading_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return {
            'user_id': user[0],
            'username': user[1],
            'current_day': user[2],
            'completed_lessons': user[3].split(',') if user[3] else [],
            'created_at': user[4]
        }
    return None

def create_user(user_id, username):
    """Создать пользователя"""
    conn = sqlite3.connect('trading_bot.db')
    cursor = conn.cursor()
    cursor.execute(
        'INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)',
        (user_id, username)
    )
    conn.commit()
    conn.close()

def update_user_day(user_id, day):
    """Обновить текущий день пользователя"""
    conn = sqlite3.connect('trading_bot.db')
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE users SET current_day = ? WHERE user_id = ?',
        (day, user_id)
    )
    conn.commit()
    conn.close()

def add_completed_lesson(user_id, day):
    """Добавить пройденный урок"""
    conn = sqlite3.connect('trading_bot.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT completed_lessons FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    
    completed = result[0].split(',') if result and result[0] else []
    if str(day) not in completed:
        completed.append(str(day))
        new_completed = ','.join(completed)
        cursor.execute(
            'UPDATE users SET completed_lessons = ? WHERE user_id = ?',
            (new_completed, user_id)
        )
    
    conn.commit()
    conn.close()

def get_all_users():
    """Получить всех пользователей"""
    conn = sqlite3.connect('trading_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, current_day FROM users')
    users = cursor.fetchall()
    conn.close()
    return users

def get_user_progress(user_id):
    """Получить прогресс пользователя"""
    user = get_user(user_id)
    if user:
        return {
            'current_day': user['current_day'],
            'completed': len(user['completed_lessons']),
            'total': 30
        }
    return None
