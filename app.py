import os
import json
import sqlite3
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

# ========== ПОДКЛЮЧЕНИЕ К SQLITE ==========
# Получаем абсолютный путь к папке проекта
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.sqlite3')

def get_db_connection():
    """Создает подключение к SQLite базе"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Позволяет обращаться по именам колонок
    return conn

def init_db():
    """Создает таблицу при первом запуске"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ SQLite база данных готова по пути: {DB_PATH}")

# Инициализируем БД при запуске
init_db()

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

def dict_from_row(row):
    """Преобразует sqlite3.Row в словарь"""
    return dict(zip(row.keys(), row))

# ========== API ЭНДПОИНТЫ ==========

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'status': 'ok',
        'message': 'Сервер работает на PythonAnywhere + SQLite!',
        'database': '✅ SQLite подключен',
        'db_path': DB_PATH
    })

@app.route('/projects', methods=['GET'])
def get_projects():
    """Получить все проекты"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT data FROM projects ORDER BY created_at DESC")
        rows = cur.fetchall()
        
        cur.close()
        conn.close()
        
        # Преобразуем JSON строки обратно в объекты
        projects = [json.loads(row['data']) for row in rows]
        return jsonify(projects)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/watched', methods=['GET'])
def get_watched_projects():
    """Получить только просмотренные проекты"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # В SQLite используем LIKE для поиска в JSON
        cur.execute("""
            SELECT data FROM projects 
            WHERE data LIKE '%"watched": true%'
            ORDER BY created_at DESC
        """)
        rows = cur.fetchall()
        
        cur.close()
        conn.close()
        
        projects = [json.loads(row['data']) for row in rows]
        return jsonify(projects)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/projects', methods=['POST'])
def add_project():
    """Добавить новый проект"""
    try:
        new_project = request.json
        
        if not new_project.get('id'):
            return jsonify({'error': 'Отсутствует ID проекта'}), 400
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Проверяем существование
        cur.execute("SELECT id FROM projects WHERE id = ?", (new_project['id'],))
        if cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({'error': 'Проект уже существует'}), 409
        
        # Добавляем новый проект
        cur.execute(
            "INSERT INTO projects (id, data) VALUES (?, ?)",
            (new_project['id'], json.dumps(new_project, ensure_ascii=False))
        )
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'status': 'ok',
            'message': 'Проект добавлен',
            'project': new_project
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/projects/<project_id>', methods=['PUT'])
def update_project(project_id):
    """Обновить существующий проект"""
    try:
        updates = request.json
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Получаем текущие данные
        cur.execute("SELECT data FROM projects WHERE id = ?", (project_id,))
        row = cur.fetchone()
        
        if not row:
            cur.close()
            conn.close()
            return jsonify({'error': 'Проект не найден'}), 404
        
        # Обновляем данные
        current_data = json.loads(row['data'])
        current_data.update(updates)
        
        cur.execute(
            "UPDATE projects SET data = ? WHERE id = ?",
            (json.dumps(current_data, ensure_ascii=False), project_id)
        )
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'status': 'ok',
            'message': 'Проект обновлён',
            'project': current_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/projects/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Удалить проект"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        conn.commit()
        
        cur.close()
        conn.close()
        
        return jsonify({'status': 'ok', 'message': 'Проект удалён'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Сервер SQLite запущен")
    print(f"📁 База данных: {DB_PATH}")
    app.run(debug=True, host='0.0.0.0', port=5000)