from flask import Flask, render_template, send_from_directory
import re
import os

def getUsers():
    # Открыть файл extensions.conf и прочитать его содержимое
    with open('extensions.conf', 'r', encoding='utf-8') as f:
        data = f.read()
        # print(data)

    # Паттерн для извлечения данных
    pattern = r'\$\[\"\$\{CALLERID\(num\)\}\" = "(.+)"\]\?(line\d+)'

    # Извлечение данных из строки
    matches = re.findall(pattern, data)

    # Создание списка словарей
    users = []
    for match in matches:
        telephone = match[0]
        folder = match[1].replace('line', '') + '0'
        fio = data.split(telephone)[-1].split('\n')[0].split(';')[-1].strip()
        counter = 0
        try:
            # Посчитаем кол-во записей
            with open('home/' + folder + '/counter.txt', 'r') as file:
                counter = file.read()
                counter = int(counter) - 1
        except:
            pass

        users.append({'telephone': telephone, 'fio': fio, 'folder': folder, 'counter': counter})

    return users

def getUser(id):
    users = getUsers()
    for user in users:
        if user.get('folder') == id:
            return user


app = Flask(__name__)

@app.route('/')
@app.route('/index')
def index():
    users = getUsers()
    return render_template('index.html', users=users)


@app.route('/user/<id>')
def user(id):
    user = getUser(id)
    recordings = []
    try:
        with open('home/' + id + '/corpus.txt', 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, start=1):
                line = line.strip()
                if line:
                    try:
                        filename, name = line.split(';', maxsplit=1)
                        if name and filename:
                            record = {'id': i, 'name': name, 'filename': filename}
                            recordings.append(record)
                    except:
                        record = {'id': i, 'name': line, 'filename': ''}
                        recordings.append(record)
    except:
        pass


    return render_template('user.html', recordings=recordings, user=user)

@app.route('/user/<string:folder>/records/<path:filename>')
def serve_record(folder, filename):
    return send_from_directory(f'./home/{folder}/records', filename)


@app.route('/delete-audio/<user_folder>/<filename>')
def delete_audio(user_folder, filename):
    try:
        # Удаляем аудиофайл
        os.remove(os.path.join('home', user_folder, 'records', filename))

        # Удаляем строку с именем файла и сохраняем ее содержимое
        with open(os.path.join('home', user_folder, 'corpus.txt'), 'r', encoding='utf-8') as f:
            lines = f.readlines()

        corpus_content = ''
        corpus_content_deleted = ''
        for line in lines:
            if line.strip() and not line.startswith(filename):

                corpus_content += line
            else:
                corpus_content_deleted = line.strip().split(';')[1] + '\n'

        # Записываем новую строку в corpus.txt без имени файла
        with open(os.path.join('home', user_folder, 'corpus.txt'), 'w', encoding='utf-8') as f:
            f.write(corpus_content)
            f.write(corpus_content_deleted)

        # Обновляем corpus.txt и подсчитываем количество точек с запятой
        semicolon_count = 1
        with open(os.path.join('home', user_folder, 'corpus.txt'), 'r', encoding='utf-8') as f:
            for line in f:
                semicolon_count += line.count(';')

        print(semicolon_count)

        # Записываем количество точек с запятой в файл counter.txt
        with open(os.path.join('home', user_folder, 'counter.txt'), 'w') as f:
            f.write(str(semicolon_count))


        # Возвращаем ответ 204 No Content в случае успеха
        return '', 204
    except:
        # Возвращаем ответ 500 Internal Server Error в случае ошибки
        return '', 500



if __name__ == '__main__':
    # app.static_folder = '.'
    app.run(debug=True, host="0.0.0.0", port="8080")
