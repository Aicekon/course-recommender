from flask import Flask, render_template, request, redirect, url_for, session, flash
from passlib.hash import sha256_crypt
import psycopg2
from flask_session import Session
from psycopg2 import sql
import json
import uuid
from datetime import datetime, timedelta
import os
import numpy as np
import random
from io import BytesIO
import base64
from datetime import datetime
import matplotlib
matplotlib.use('Agg')  # Устанавливаем бэкенд, не требующий GUI
from matplotlib import pyplot as plt
from dotenv import load_dotenv
import logging
#logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.CRITICAL)
app = Flask(__name__)
load_dotenv()  # загружает переменные из .env
app.secret_key = os.getenv('SECRET_KEY')
# Очистка старых сессий при запуске


# Конфигурация БД
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME', 'postgres'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', '1111'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432')
}

TAGS = [
    'Python', 'JavaScript', 'Java', 'C#', 'C++', 'Операционные системы',
    'Тестирование', 'Системное администрирование', 'DevOps',
    'Data Science', 'Базы данных', 'Web-разработка',
    'Информационная безопасность', 'Мобильная разработка',
    'Искусственный интеллект', 'Веб-дизайн', 'Робототехника',
    'Figma', 'Blockchain'
]


def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


def get_user_id(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        return cursor.fetchone()[0]
    finally:
        cursor.close()
        conn.close()


def create_results_chart(tag_stats):
    plt.switch_backend('Agg')
    try:
        tags = list(tag_stats.keys())
        correct = [stats['correct'] for stats in tag_stats.values()]
        total = [stats['total'] for stats in tag_stats.values()]
        incorrect = [t - c for t, c in zip(total, correct)]

        # Увеличиваем высоту и уменьшаем ширину
        fig, ax = plt.subplots(figsize=(10, 6))  # Шире и выше

        bar_width = 0.35
        index = range(len(tags))

        bar1 = ax.bar(index, correct, bar_width, label='Правильно', color='#28a745')
        bar2 = ax.bar(index, incorrect, bar_width, bottom=correct, label='Неправильно', color='#dc3545')

        ax.set_xlabel('Теги', fontsize=10)
        ax.set_ylabel('Количество ответов', fontsize=10)
        ax.set_title('Результаты по тегам', fontsize=12)
        ax.set_xticks(index)
        ax.set_xticklabels(tags, rotation=45, ha='right', fontsize=8)

        # Переносим легенду под диаграмму и делаем компактной
        ax.legend(
            loc='upper center',
            bbox_to_anchor=(0.5, -0.15),  # Под диаграммой
            ncol=2,  # В 2 колонки
            fontsize=8  # Уменьшаем шрифт
        )

        # Увеличиваем нижний отступ для легенды
        plt.subplots_adjust(bottom=0.25)

        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        plt.close(fig)
        return base64.b64encode(buf.getvalue()).decode('utf-8')
    except Exception as e:
        plt.close('all')
        #print(f"Error creating results chart: {e}")
        return None


def create_repeat_chart(improved, worsened, unchanged, new_questions):
    try:
        sizes = [new_questions, improved, unchanged, worsened]
        if sum(sizes) == 0:
            return None

        plt.switch_backend('Agg')
        fig, ax = plt.subplots(figsize=(6, 4))

        labels = ['Новые', 'Улучшено', 'Без измен.', 'Ухудшено']
        colors = ['#17a2b8', '#28a745', '#ffc107', '#dc3545']

        # Фильтруем нулевые значения
        filtered = [(s, l, c) for s, l, c in zip(sizes, labels, colors) if s > 0]
        if not filtered:
            return None

        sizes, labels, colors = zip(*filtered)

        wedges, texts = ax.pie(
            sizes,
            colors=colors,
            startangle=90,
            wedgeprops={'linewidth': 1, 'edgecolor': 'white'}
        )

        # Добавляем легенду с количеством
        legend_labels = [f"{l}: {s}" for l, s in zip(labels, sizes)]
        ax.legend(wedges, legend_labels,
                  title="Результаты",
                  loc="center left",
                  bbox_to_anchor=(1, 0, 0.5, 1),
                  fontsize=8)

        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        plt.close(fig)
        return base64.b64encode(buf.getvalue()).decode('utf-8')
    except Exception as e:
        #print(f"Error creating repeat chart: {e}")
        return None

def update_question_rating(user_id, question_id, is_correct):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Получаем текущий рейтинг
            cursor.execute("""
                SELECT rating FROM question_ratings 
                WHERE user_id = %s AND question_id = %s
            """, (user_id, question_id))
            current_rating = cursor.fetchone()

            # Начальное значение рейтинга для новых вопросов
            new_rating = 0.5
            delta = 0.1  # Базовое изменение рейтинга

            if current_rating:
                current_rating = current_rating[0]
                # Адаптивное изменение для крайних значений
                if current_rating <= 0.1:
                    delta = 0.1 * current_rating
                elif current_rating >= 0.9:
                    delta = 0.1 * (1 - current_rating)

                if is_correct:
                    new_rating = min(current_rating + delta, 0.99)
                else:
                    new_rating = max(current_rating - delta, 0.01)
            else:
                # Первый ответ на вопрос
                new_rating = 0.6 if is_correct else 0.4

            # Обновляем или создаём запись (используем CURRENT_TIMESTAMP вместо NOW())
            cursor.execute("""
                INSERT INTO question_ratings 
                (user_id, question_id, rating, last_correct, correct_count, incorrect_count) 
                VALUES (%s, %s, %s, 
                    CASE WHEN %s THEN CURRENT_TIMESTAMP ELSE NULL END,
                    %s, %s)
                ON CONFLICT (user_id, question_id) 
                DO UPDATE SET
                    rating = EXCLUDED.rating,
                    last_correct = CASE 
                        WHEN EXCLUDED.last_correct IS NOT NULL THEN EXCLUDED.last_correct
                        ELSE question_ratings.last_correct
                    END,
                    correct_count = question_ratings.correct_count + EXCLUDED.correct_count,
                    incorrect_count = question_ratings.incorrect_count + EXCLUDED.incorrect_count
            """, (
                user_id,
                question_id,
                new_rating,
                is_correct,
                1 if is_correct else 0,
                0 if is_correct else 1
            ))
            conn.commit()
    finally:
        conn.close()


def get_adaptive_questions(user_id, tags, limit_per_tag=5):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            questions = []
            for tag in tags:
                cursor.execute("""
                    SELECT q.id 
                    FROM questions q
                    LEFT JOIN question_ratings r ON r.question_id = q.id AND r.user_id = %s
                    WHERE q.tag = %s
                    ORDER BY 
                        COALESCE(r.rating, 0.5) ASC,  
                        COALESCE(r.last_asked, '1970-01-01') ASC,  
                        RANDOM()  
                    LIMIT %s
                """, (user_id, tag, limit_per_tag))
                questions.extend([row[0] for row in cursor.fetchall()])
            return questions
    finally:
        conn.close()


@app.route('/')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('select_tags'))
@app.teardown_request
def close_matplotlib(exception=None):
    plt.close('all')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT password_hash FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user and sha256_crypt.verify(password, user[0]):
            session['username'] = username
            flash('Вход выполнен успешно!', 'success')
            return redirect(url_for('select_tags'))
        else:
            flash('Неверные учетные данные', 'danger')

        cursor.close()
        conn.close()

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_hash = sha256_crypt.hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Создаем пользователя
            cursor.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id",
                (username, password_hash)
            )
            user_id = cursor.fetchone()[0]

            # Получаем все вопросы
            cursor.execute("SELECT id FROM questions")
            question_ids = [row[0] for row in cursor.fetchall()]

            # Создаем начальные рейтинги для всех вопросов
            for question_id in question_ids:
                cursor.execute("""
                    INSERT INTO question_ratings 
                    (user_id, question_id, rating, correct_count, incorrect_count)
                    VALUES (%s, %s, 0.5, 0, 0)
                """, (user_id, question_id))

            conn.commit()
            flash('Регистрация прошла успешно! Теперь вы можете войти.', 'success')
            return redirect(url_for('login'))
        except psycopg2.IntegrityError:
            conn.rollback()
            flash('Пользователь с таким именем уже существует', 'danger')
        finally:
            cursor.close()
            conn.close()

    return render_template('register.html')
def get_test_session(session_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT data::text FROM user_test_sessions 
                WHERE session_id = %s 
                AND expires_at > CURRENT_TIMESTAMP
            """, (session_id,))
            result = cursor.fetchone()
            if result:
                try:
                    return json.loads(result[0])  # Явно преобразуем text в dict
                except json.JSONDecodeError as e:
                    #print(f"JSON decode error: {e}")
                    return None
            return None
    except Exception as e:
        #print(f"Error getting session: {e}")
        return None
    finally:
        conn.close()

def update_test_session(session_id, data):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE user_test_sessions 
                SET data = %s,
                    expires_at = (CURRENT_TIMESTAMP + INTERVAL '24 hours')
                WHERE session_id = %s
            """, (json.dumps(data), session_id))  # Кодируем словарь в JSON строку
            conn.commit()
    except Exception as e:
        #print(f"Error updating session: {e}")
        conn.rollback()
    finally:
        conn.close()

def cleanup_session(session_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                DELETE FROM user_test_sessions 
                WHERE session_id = %s
            """, (session_id,))
            conn.commit()
    except Exception as e:
        #print(f"Error cleaning up session: {e}")
        conn.rollback()
    finally:
        conn.close()

def cleanup_expired_sessions():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                DELETE FROM user_test_sessions 
                WHERE expires_at <= CURRENT_TIMESTAMP
            """)
            conn.commit()
            #print(f"Cleaned up expired sessions")
    except Exception as e:
        #print(f"Error cleaning expired sessions: {e}")
        conn.rollback()
    finally:
        conn.close()
@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('login'))


@app.route('/select_tags', methods=['GET', 'POST'])
def select_tags():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        selected_tags = request.form.getlist('tags')
        if not selected_tags:
            flash('Выберите хотя бы один тег', 'warning')
            return redirect(url_for('select_tags'))

        session['selected_tags'] = selected_tags
        return redirect(url_for('start_test'))

    return render_template('select_tags.html', tags=TAGS)


@app.route('/start_test')
def start_test():
    if 'username' not in session or 'selected_tags' not in session:
        return redirect(url_for('login'))

    user_id = get_user_id(session['username'])
    session_id = str(uuid.uuid4())

    conn = None
    try:
        questions = get_adaptive_questions(user_id, session['selected_tags'])

        # Подготовка данных сессии
        session_data = {
            'questions': questions,
            'current_question': 0,
            'score': 0,
            'answers': [],
            'user_id': user_id,
            'start_time': datetime.now().isoformat()
        }

        # Сохраняем во временную таблицу
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Явно преобразуем в JSON строку
            cursor.execute("""
                INSERT INTO user_test_sessions 
                (session_id, user_id, data, expires_at) 
                VALUES (%s, %s, %s::jsonb, CURRENT_TIMESTAMP + INTERVAL '24 hours')
            """, (session_id, user_id, json.dumps(session_data)))
            conn.commit()

        # Сохраняем session_id в куки сессии
        session['test_session_id'] = session_id
       #print(f"Started test session: {session_id}")  # Для отладки
        return redirect(url_for('show_question'))

    except Exception as e:
        flash(f'Ошибка при запуске теста: {str(e)}', 'danger')
        return redirect(url_for('select_tags'))
    finally:
        if conn:
            conn.close()


@app.route('/question')
def show_question():
    if 'test_session_id' not in session:
        flash('Сессия теста не найдена', 'danger')
        return redirect(url_for('select_tags'))

    session_id = session['test_session_id']
    #print(f"Trying to load session: {session_id}")  # Для отладки

    session_data = get_test_session(session_id)
    if not session_data:
        flash('Сессия теста не найдена или истекла', 'danger')
        return redirect(url_for('select_tags'))

    #print(f"Session data loaded: {session_data}")  # Для отладки

    current = session_data['current_question']
    questions = session_data['questions']

    if current >= len(questions):
        return redirect(url_for('test_results'))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, question_text, tag FROM questions WHERE id = %s",
                           (questions[current],))
            question = cursor.fetchone()

            if not question:
                flash('Вопрос не найден', 'danger')
                return redirect(url_for('select_tags'))

            question_data = {
                'id': question[0],
                'question_text': question[1],
                'tag': question[2]
            }

            cursor.execute("""
                SELECT id, answer_text, is_correct, option_code 
                FROM answers 
                WHERE question_id = %s
                ORDER BY RANDOM()
            """, (questions[current],))
            answers = cursor.fetchall()

            return render_template('question.html',
                                   question=question_data,
                                   answers=answers,
                                   question_num=current + 1,
                                   total=len(questions))
    except Exception as e:
        flash(f'Ошибка при загрузке вопроса: {str(e)}', 'danger')
        return redirect(url_for('select_tags'))
    finally:
        conn.close()


@app.route('/answer', methods=['POST'])
def process_answer():
    # Проверка наличия активной сессии
    if 'test_session_id' not in session:
        flash('Сессия теста не найдена', 'danger')
        return redirect(url_for('select_tags'))

    session_id = session['test_session_id']
    session_data = get_test_session(session_id)

    if not session_data:
        flash('Сессия теста не найдена или истекла', 'danger')
        return redirect(url_for('select_tags'))

    user_id = session_data['user_id']
    current_question_idx = session_data['current_question']
    question_id = session_data['questions'][current_question_idx]
    selected_answers = request.form.getlist('answers')

    if not selected_answers:
        flash('Выберите хотя бы один ответ', 'warning')
        return redirect(url_for('show_question'))

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Получаем данные вопроса
            cursor.execute("""
                SELECT question_text, tag FROM questions WHERE id = %s
            """, (question_id,))
            question = cursor.fetchone()
            if not question:
                flash('Вопрос не найден', 'danger')
                return redirect(url_for('select_tags'))

            question_text, tag = question

            # Получаем правильные ответы
            cursor.execute("""
                SELECT option_code, answer_text FROM answers 
                WHERE question_id = %s AND is_correct = TRUE
            """, (question_id,))
            correct_answers = cursor.fetchall()
            correct_answers_codes = {row[0] for row in correct_answers}
            correct_answers_texts = [row[1] for row in correct_answers]

            # Получаем тексты выбранных ответов
            user_answers_texts = []
            for answer_code in selected_answers:
                cursor.execute("""
                    SELECT answer_text FROM answers 
                    WHERE question_id = %s AND option_code = %s
                """, (question_id, answer_code))
                result = cursor.fetchone()
                if result:
                    user_answers_texts.append(result[0])

            # Проверяем правильность ответа
            is_correct = set(selected_answers) == correct_answers_codes

            # Получаем историю предыдущих попыток
            cursor.execute("""
                SELECT is_correct FROM user_question_history 
                WHERE user_id = %s AND question_id = %s
                ORDER BY answered_at
            """, (user_id, question_id))
            history = cursor.fetchall()
            previous_attempts = len(history)
            result_change = None

            # Анализируем изменение результата
            if previous_attempts > 0:
                last_result = history[-1][0]
                if last_result and not is_correct:
                    result_change = 'worsened'
                elif not last_result and is_correct:
                    result_change = 'improved'

            # Сохраняем попытку в историю
            cursor.execute("""
                INSERT INTO user_question_history (
                    user_id, question_id, is_correct, 
                    attempt_count, session_id, user_answer, correct_answer
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id, question_id, is_correct,
                previous_attempts + 1, session_id,
                ', '.join(selected_answers), ', '.join(correct_answers_codes)
            ))

            # Обновляем рейтинг вопроса
            update_question_rating(user_id, question_id, is_correct)

            # Обновляем временную сессию
            answer_data = {
                'question': question_text,
                'user_answer': ', '.join(user_answers_texts),
                'correct_answers': correct_answers_texts,
                'is_correct': is_correct,
                'tag': tag,
                'previous_attempts': previous_attempts,
                'result_change': result_change,
                'question_id': question_id,
                'answered_at': datetime.now().isoformat()
            }

            session_data['answers'].append(answer_data)
            if is_correct:
                session_data['score'] += 1

            session_data['current_question'] += 1
            update_test_session(session_id, session_data)

            conn.commit()

        # Перенаправляем на следующий вопрос или результаты
        if session_data['current_question'] >= len(session_data['questions']):
            return redirect(url_for('test_results'))
        return redirect(url_for('show_question'))

    except Exception as e:
        if conn:
            conn.rollback()
        flash(f'Ошибка при обработке ответа: {str(e)}', 'danger')
        return redirect(url_for('select_tags'))
    finally:
        if conn:
            conn.close()


@app.route('/results')
def test_results():
    if 'test_session_id' not in session:
        flash('Сессия теста не найдена', 'danger')
        return redirect(url_for('select_tags'))

    session_id = session['test_session_id']
    session_data = get_test_session(session_id)

    if not session_data:
        flash('Сессия теста не найдена или истекла', 'danger')
        return redirect(url_for('select_tags'))

    # Извлекаем данные из сессии
    answers = session_data.get('answers', [])
    if not answers:
        flash('Нет данных для отображения результатов', 'warning')
        return redirect(url_for('select_tags'))

    # Сбор статистики по тегам
    tag_stats = {}
    for answer in answers:
        tag = answer['tag']
        if tag not in tag_stats:
            tag_stats[tag] = {'correct': 0, 'total': 0}

        tag_stats[tag]['total'] += 1
        if answer['is_correct']:
            tag_stats[tag]['correct'] += 1

    # Сбор статистики по повторным вопросам
    repeat_stats = {
        'new': 0,
        'improved': 0,
        'worsened': 0,
        'unchanged': 0,
        'total': len(answers)
    }

    for answer in answers:
        attempts = answer.get('previous_attempts', 0)
        change = answer.get('result_change')

        if attempts == 0:
            repeat_stats['new'] += 1
        else:
            if change == 'improved':
                repeat_stats['improved'] += 1
            elif change == 'worsened':
                repeat_stats['worsened'] += 1
            else:
                repeat_stats['unchanged'] += 1

    # Создание диаграмм
    chart_image = create_results_chart(tag_stats) if tag_stats else None

    if sum([repeat_stats['new'], repeat_stats['improved'],
            repeat_stats['worsened'], repeat_stats['unchanged']]) > 0:
        repeat_chart_image = create_repeat_chart(
            repeat_stats['improved'],
            repeat_stats['worsened'],
            repeat_stats['unchanged'],
            repeat_stats['new']
        )
    else:
        repeat_chart_image = None

    # Получение рекомендаций
    recommended_courses = get_recommended_courses(tag_stats)
    recommended_articles = get_recommended_articles(tag_stats)

    # Очистка временной сессии
    cleanup_session(session_id)
    session.pop('test_session_id', None)

    # Отладочный вывод
    #print(f"[DEBUG] Статистика по тегам: {tag_stats}")
    #print(f"[DEBUG] Статистика повторений: {repeat_stats}")
    #print(f"[DEBUG] Количество ответов: {len(answers)}")

    return render_template('results.html',
                           answers=answers,
                           tag_stats=tag_stats,
                           recommended_courses=recommended_courses,
                           recommended_articles=recommended_articles,
                           chart_image=chart_image,
                           repeat_stats=repeat_stats,
                           repeat_chart_image=repeat_chart_image)


def get_recommended_courses(tag_stats):
    conn = get_db_connection()
    cursor = conn.cursor()
    recommended = []

    for tag, stats in tag_stats.items():
        accuracy = stats['correct'] / stats['total']

        if accuracy < 0.5:
            difficulty = 'easy'
        elif accuracy < 0.85:
            difficulty = 'normal'
        else:
            difficulty = 'hard'

        cursor.execute(
            """SELECT название, ссылка, краткое_описание, площадка, уровень_сложности, тег 
               FROM курсы 
               WHERE тег = %s AND уровень_сложности = %s
               ORDER BY RANDOM() """,
            (tag, difficulty)
        )
        courses = cursor.fetchall()
        for course in courses:
            tags = [t.strip() for t in course[5].split(',')] if course[5] else []
            recommended.append((
                course[0], course[1], course[2], course[3], course[4], tags
            ))

    cursor.close()
    conn.close()
    return recommended


def get_recommended_articles(tag_stats):
    conn = get_db_connection()
    cursor = conn.cursor()
    recommended = []

    for tag, stats in tag_stats.items():
        accuracy = stats['correct'] / stats['total']

        if accuracy < 0.5:
            difficulty = 'easy'
        elif accuracy < 0.85:
            difficulty = 'normal'
        else:
            difficulty = 'hard'

        cursor.execute(
            """SELECT title, link, date_published, source, tag, complexity_level, views 
               FROM articles 
               WHERE tag = %s AND complexity_level = %s
               ORDER BY RANDOM() """,
            (tag, difficulty)
        )
        recommended.extend(cursor.fetchall())

    cursor.close()
    conn.close()
    return recommended


if __name__ == '__main__':
    app.run(debug=True)