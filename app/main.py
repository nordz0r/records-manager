from flask import Flask, render_template, send_from_directory
import re
import os
import logging

# Настройка логгера
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s',
                    handlers=[
                        logging.FileHandler("app.log"),
                        logging.StreamHandler()
                    ])
logger = logging.getLogger(__name__)

def getUsers():
    logger.info("Чтение файла extensions.conf")
    try:
        with open('extensions.conf', 'r', encoding='utf-8') as f:
            data = f.read()
    except FileNotFoundError:
        logger.error("Файл extensions.conf не найден")
        return []

    pattern = r'\$\[\"\$\{CALLERID\(num\)\}\" = "(.+)"\]\?(line\d+)'
    matches = re.findall(pattern, data)
    users = []
    for match in matches:
        telephone = match[0]
        folder = match[1].replace('line', '') + '0'
        fio = data.split(telephone)[-1].split('\n')[0].split(';')[-1].strip()
        counter = 0
        try:
            with open('home/' + folder + '/counter.txt', 'r') as file:
                counter = file.read()
                counter = int(counter) - 1
        except FileNotFoundError:
            logger.warning(f"Файл counter.txt не найден для папки {folder}")
        except ValueError:
            logger.warning(f"Неверное значение в файле counter.txt для папки {folder}")

        users.append({'telephone': telephone, 'fio': fio, 'folder': folder, 'counter': counter})

    return users

def getUser(id):
    users = getUsers()
    for user in users:
        if user.get('folder') == id:
            return user
    logger.warning(f"Пользователь с id {id} не найден")
    return None

app = Flask(__name__)

@app.route('/')
@app.route('/index')
def index():
    users = getUsers()
    return render_template('index.html', users=users)

@app.route('/user/<id>')
def user(id):
    user = getUser(id)
    if not user:
        logger.error(f"Пользователь с id {id} не найден")
        return "Пользователь не найден", 404
    recordings = []
    try:
        with open(f'home/{id}/corpus.txt', 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, start=1):
                line = line.strip()
                if line:
                    try:
                        filename, name = line.split(';', maxsplit=1)
                        if name and filename:
                            recordings.append({'id': i, 'name': name, 'filename': filename})
                    except ValueError:
                        recordings.append({'id': i, 'name': line, 'filename': ''})
    except FileNotFoundError:
        logger.warning(f"Файл corpus.txt не найден для пользователя {id}")

    return render_template('user.html', recordings=recordings, user=user)

@app.route('/user/<string:folder>/records/<path:filename>')
def serve_record(folder, filename):
    return send_from_directory(f'./home/{folder}/records', filename)

@app.route('/delete-audio/<user_folder>/<filename>')
def delete_audio(user_folder, filename):
    try:
        os.remove(os.path.join('home', user_folder, 'records', filename))
        with open(os.path.join('home', user_folder, 'corpus.txt'), 'r', encoding='utf-8') as f:
            lines = f.readlines()

        corpus_content = ''
        corpus_content_deleted = ''
        for line in lines:
            if line.strip() and not line.startswith(filename):
                corpus_content += line
                logger.debug(f'{line} добавлено в corpus_content')
            else:
                corpus_content_deleted = line.strip().split(';')[1] + '\n'
                logger.debug(f'{line} добавлено в corpus_content_deleted')

        with open(os.path.join('home', user_folder, 'corpus.txt'), 'w', encoding='utf-8') as f:
            f.write(corpus_content)
            f.write(corpus_content_deleted)

        semicolon_count = 1
        with open(os.path.join('home', user_folder, 'corpus.txt'), 'r', encoding='utf-8') as f:
            for line in f:
                semicolon_count += line.count(';')

        with open(os.path.join('home', user_folder, 'counter.txt'), 'w') as f:
            f.write(str(semicolon_count))

        logger.info(f"Аудиофайл {filename} успешно удален для пользователя {user_folder}")
        return '', 204
    except Exception as e:
        logger.error(f'Ошибка при удалении аудиофайла: {e}')
        return '', 500

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port="8080")
