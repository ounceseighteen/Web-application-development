from flask import Flask, render_template, request, redirect, url_for
import random
import string
import json
import os

app = Flask(__name__)

# Файлы для хранения данных
USERS_FILE = 'users.json'
PASSWORDS_FILE = 'password_history.json'


def load_users():
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return []
                return json.loads(content)
        else:
            return []
    except json.JSONDecodeError:
        return []
    except Exception as e:
        print(f"Ошибка при загрузке пользователей: {e}")
        return []


def save_users(users):
    try:
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Ошибка при сохранении пользователей: {e}")


def load_passwords():
    try:
        if os.path.exists(PASSWORDS_FILE):
            with open(PASSWORDS_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return {}
                return json.loads(content)
        else:
            return {}
    except json.JSONDecodeError:
        return {}
    except Exception as e:
        print(f"Ошибка при загрузке паролей: {e}")
        return {}


def save_passwords(passwords_data):
    try:
        with open(PASSWORDS_FILE, 'w', encoding='utf-8') as f:
            json.dump(passwords_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Ошибка при сохранении паролей: {e}")


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

        users = load_users()

        if action == 'register':
            for user in users:
                if user['username'] == username:
                    return render_template('login.html', error='Пользователь с таким именем уже существует')

            users.append({
                'username': username,
                'password': password
            })
            save_users(users)
            return render_template('login.html', success='Регистрация успешна! Теперь войдите в систему')

        else:
            for user in users:
                if user['username'] == username and user['password'] == password:
                    return redirect(url_for('generator', username=username))

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

    password = ''
    if request.method == 'POST':
        site = request.form.get('site')
        login_name = request.form.get('login_name')
        complexity = request.form.get('complexity')

        # Генерируем пароль
        password = generate_password(complexity)

        # Сохраняем в историю если указаны сайт и логин
        if site and login_name:
            passwords_data = load_passwords()

            if username not in passwords_data:
                passwords_data[username] = []

            # Добавляем новую запись
            passwords_data[username].append({
                'site': site,
                'login': login_name,
                'password': password
            })

            save_passwords(passwords_data)

    # Загружаем историю паролей для отображения
    passwords_data = load_passwords()
    user_passwords = passwords_data.get(username, [])

    return render_template('manager.html',
                         password=password,
                         username=username,
                         passwords_history=user_passwords)


@app.route('/logout')
def logout():
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=2000)