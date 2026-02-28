from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Разрешаем запросы с GitHub Pages

JSON_FILE = 'projects.json'

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

def load_data():
    """Загружает данные из JSON-файла"""
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_data(data):
    """Сохраняет данные в JSON-файл"""
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ========== МАРШРУТЫ API ==========

@app.route('/', methods=['GET'])
def home():
    """Главная страница для проверки работы сервера"""
    return jsonify({
        'status': 'ok',
        'message': 'Сервер проектов работает!',
        'endpoints': {
            'GET /projects': 'Получить все проекты',
            'POST /projects': 'Добавить новый проект',
            'GET /projects/<id>': 'Получить проект по ID',
            'PUT /projects/<id>': 'Обновить проект',
            'DELETE /projects/<id>': 'Удалить проект',
            'GET /watched': 'Получить только просмотренные проекты'
        }
    })

@app.route('/projects', methods=['GET'])
def get_projects():
    """Получить все проекты"""
    return jsonify(load_data())

@app.route('/watched', methods=['GET'])
def get_watched_projects():
    """Получить только просмотренные проекты (для страницы оценок)"""
    data = load_data()
    watched = [p for p in data if p.get('watched') == True]
    return jsonify(watched)

@app.route('/projects/<project_id>', methods=['GET'])
def get_project(project_id):
    """Получить конкретный проект по ID"""
    data = load_data()
    project = next((p for p in data if p['id'] == project_id), None)
    if project:
        return jsonify(project)
    return jsonify({'error': 'Проект не найден'}), 404

@app.route('/projects', methods=['POST'])
def add_project():
    """Добавить новый проект"""
    try:
        new_project = request.json
        
        # Проверяем обязательные поля
        if not new_project.get('id'):
            return jsonify({'error': 'Отсутствует ID проекта'}), 400
        
        # Добавляем поля по умолчанию, если их нет
        if 'watched' not in new_project:
            new_project['watched'] = False
        if 'inProgress' not in new_project:
            new_project['inProgress'] = False
        if 'ratings' not in new_project:
            new_project['ratings'] = {
                'senya': None,
                'vanya': None,
                'pasha': None,
                'volodya': None
            }
        if 'notes' not in new_project:
            new_project['notes'] = ''
        if 'watchedDate' not in new_project:
            new_project['watchedDate'] = None
        
        data = load_data()
        
        # Проверяем, нет ли уже такого проекта
        if any(p['id'] == new_project['id'] for p in data):
            return jsonify({'error': 'Проект с таким ID уже существует'}), 409
        
        data.append(new_project)
        save_data(data)
        
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
        data = load_data()
        
        for i, project in enumerate(data):
            if project['id'] == project_id:
                # Обновляем только переданные поля
                data[i].update(updates)
                
                # Если фильм помечен как просмотренный и нет даты, добавляем её
                if updates.get('watched') == True and not data[i].get('watchedDate'):
                    data[i]['watchedDate'] = datetime.now().strftime('%Y-%m-%d')
                
                save_data(data)
                return jsonify({
                    'status': 'ok',
                    'message': 'Проект обновлён',
                    'project': data[i]
                })
        
        return jsonify({'error': 'Проект не найден'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/projects/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Удалить проект"""
    data = load_data()
    new_data = [p for p in data if p['id'] != project_id]
    
    if len(new_data) < len(data):
        save_data(new_data)
        return jsonify({
            'status': 'ok',
            'message': 'Проект удалён'
        })
    
    return jsonify({'error': 'Проект не найден'}), 404

@app.route('/projects/<project_id>/ratings', methods=['PUT'])
def update_ratings(project_id):
    """Обновить только оценки проекта"""
    try:
        ratings = request.json
        data = load_data()
        
        for i, project in enumerate(data):
            if project['id'] == project_id:
                if 'ratings' not in data[i]:
                    data[i]['ratings'] = {}
                data[i]['ratings'].update(ratings)
                
                # Автоматически помечаем как просмотренное, если есть хотя бы одна оценка
                has_rating = any(v is not None for v in data[i]['ratings'].values())
                if has_rating and not data[i].get('watched'):
                    data[i]['watched'] = True
                    data[i]['watchedDate'] = datetime.now().strftime('%Y-%m-%d')
                
                save_data(data)
                return jsonify({
                    'status': 'ok',
                    'message': 'Оценки обновлены',
                    'ratings': data[i]['ratings']
                })
        
        return jsonify({'error': 'Проект не найден'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    """Получить статистику по проектам"""
    data = load_data()
    total = len(data)
    watched = len([p for p in data if p.get('watched')])
    in_progress = len([p for p in data if p.get('inProgress')])
    
    # Статистика по типам
    types = {}
    for p in data:
        t = p.get('type', 'Фильм')
        types[t] = types.get(t, 0) + 1
    
    return jsonify({
        'total': total,
        'watched': watched,
        'in_progress': in_progress,
        'by_type': types
    })

@app.route('/reset', methods=['POST'])
def reset_data():
    """Сбросить все данные (только для разработки)"""
    if app.debug:  # Только в режиме отладки
        save_data([])
        return jsonify({'status': 'ok', 'message': 'Данные сброшены'})
    return jsonify({'error': 'Доступ запрещён'}), 403

if __name__ == '__main__':
    # Создаём пустой JSON-файл при первом запуске
    if not os.path.exists(JSON_FILE):
        save_data([])
        print(f"Создан пустой файл {JSON_FILE}")
    
    print("Сервер запущен! Доступные маршруты:")
    print("  GET  /         - информация о сервере")
    print("  GET  /projects - все проекты")
    print("  GET  /watched  - только просмотренные")
    print("  POST /projects - добавить проект")
    print("  PUT  /projects/<id> - обновить проект")
    print("  DELETE /projects/<id> - удалить проект")
    print("  GET  /stats    - статистика")
    
    app.run(debug=True, host='0.0.0.0', port=5000)