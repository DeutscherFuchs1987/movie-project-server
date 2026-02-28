import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Твоя строка подключения (временно вставь сюда для теста)
DATABASE_URL = "postgresql://movie_project_db_oyjk_user:1T4CAHsiyFOMxhUF0XFUFa5VHECN81dN@dpg-d6hf7hrh46gs73e6a2d0-a.oregon-postgres.render.com/movie_project_db_oyjk"

def get_db_connection():
    """Создает подключение к базе данных"""
    return psycopg2.connect(DATABASE_URL)

def init_db():
    """Создает таблицу при первом запуске"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            data JSONB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    cur.close()
    conn.close()
    print("✅ База данных готова")

# Инициализируем при старте
init_db()

@app.route('/')
def home():
    return jsonify({
        'status': 'ok',
        'message': 'Сервер работает с PostgreSQL!',
        'database': '✅ PostgreSQL подключен'
    })

@app.route('/projects', methods=['GET'])
def get_projects():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT data FROM projects ORDER BY created_at DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([row['data'] for row in rows])

@app.route('/watched', methods=['GET'])
def get_watched():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT data FROM projects WHERE data->>'watched' = 'true'")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([row['data'] for row in rows])

@app.route('/projects', methods=['POST'])
def add_project():
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Проверяем существование
    cur.execute("SELECT id FROM projects WHERE id = %s", (data['id'],))
    if cur.fetchone():
        cur.close()
        conn.close()
        return jsonify({'error': 'Проект уже есть'}), 409
    
    cur.execute(
        "INSERT INTO projects (id, data) VALUES (%s, %s)",
        (data['id'], json.dumps(data))
    )
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'status': 'ok'}), 201

@app.route('/projects/<project_id>', methods=['PUT'])
def update_project(project_id):
    updates = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT data FROM projects WHERE id = %s", (project_id,))
    row = cur.fetchone()
    if not row:
        return jsonify({'error': 'Не найден'}), 404
    
    current = row[0]
    current.update(updates)
    
    cur.execute(
        "UPDATE projects SET data = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
        (json.dumps(current), project_id)
    )
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/projects/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM projects WHERE id = %s", (project_id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    print("🚀 Сервер PostgreSQL запущен")
    app.run(debug=True, host='0.0.0.0', port=5000)