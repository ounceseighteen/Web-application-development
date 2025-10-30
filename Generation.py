from flask import Flask, render_template, request, redirect, url_for
import random
import string
import sqlite3
import os

app = Flask(__name__)

# Название файла базы данных
DATABASE = 'passwords.db'


def init_db():
    """Инициализация базы данных и создание таблиц"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    # Таблица паролей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS passwords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            site TEXT NOT NULL,
            login_name TEXT NOT NULL,
            password TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    conn.commit()
    conn.close()


def get_db_connection():
    """Создание соединения с базой данных"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Чтобы получать результаты как словари
    return conn


def generate_password(complexity):
    if complexity == 'simple':
        characters = string.ascii_letters + string.digits
    else:
        characters = string.ascii_letters + string.digits + string.punctuation

    length = random.randint(8, 16)
    password = ''.join(random.choice(characters) for _ in range(length))
    return password


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        action = request.form.get('action')

        conn = get_db_connection()

        if action == 'register':
            # Проверяем, существует ли пользователь
            existing_user = conn.execute(
                'SELECT id FROM users WHERE username = ?', (username,)
            ).fetchone()

            if existing_user:
                conn.close()
                return render_template('login.html', error='Пользователь с таким именем уже существует')

            # Создаем нового пользователя
            conn.execute(
                'INSERT INTO users (username, password) VALUES (?, ?)',
                (username, password)
            )
            conn.commit()
            conn.close()
            return render_template('login.html', success='Регистрация успешна! Теперь войдите в систему')

        else:
            # Проверяем логин и пароль
            user = conn.execute(
                'SELECT id, username FROM users WHERE username = ? AND password = ?',
                (username, password)
            ).fetchone()
            conn.close()

            if user:
                return redirect(url_for('generator', username=username))
            else:
                return render_template('login.html', error='Неверное имя пользователя или пароль')

    return render_template('login.html')


@app.route('/generator', methods=['GET', 'POST'])
def generator():
    username = request.args.get('username')

    if not username:
        return redirect('/')

    password = ''
    if request.method == 'POST':
        complexity = request.form.get('complexity')
        password = generate_password(complexity)

    return render_template('generator.html',
                           password=password,
                           username=username)


@app.route('/manager', methods=['GET', 'POST'])
def manager():
    username = request.args.get('username')

    if not username:
        return redirect('/')

    conn = get_db_connection()

    # Получаем ID пользователя
    user = conn.execute(
        'SELECT id FROM users WHERE username = ?', (username,)
    ).fetchone()

    if not user:
        conn.close()
        return redirect('/')

    user_id = user['id']
    password = ''

    if request.method == 'POST':
        site = request.form.get('site')
        login_name = request.form.get('login_name')
        complexity = request.form.get('complexity')

        # Генерируем пароль
        password = generate_password(complexity)

        # Сохраняем в базу данных если указаны сайт и логин
        if site and login_name:
            conn.execute(
                'INSERT INTO passwords (user_id, site, login_name, password) VALUES (?, ?, ?, ?)',
                (user_id, site, login_name, password)
            )
            conn.commit()

    # Загружаем историю паролей для отображения
    passwords_history = conn.execute('''
        SELECT site, login_name, password
        FROM passwords 
        WHERE user_id = ? 
        ORDER BY id DESC
    ''', (user_id,)).fetchall()

    conn.close()

    return render_template('manager.html',
                           password=password,
                           username=username,
                           passwords_history=passwords_history)


@app.route('/logout')
def logout():
    return redirect('/')


if __name__ == '__main__':
    # Инициализируем базу данных при запуске
    init_db()
    app.run(debug=True, host='0.0.0.0', port=3000)