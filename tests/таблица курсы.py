from flask import Flask, render_template
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, select
from sqlalchemy.orm import sessionmaker

# Параметры подключения к PostgreSQL
DATABASE_URI = 'postgresql://postgres:1111@localhost:5432/postgres'

# Создаем движок базы данных
engine = create_engine(DATABASE_URI)
metadata = MetaData()


# Описываем таблицу
курсы = Table('курсы', metadata,
    Column('id', Integer, primary_key=True),
    Column('название', String),
    Column('id_курса', Integer),
    Column('ссылка', String),
    Column('краткое_описание', String),
    Column('полное_описание', String),
    Column('уровень_сложности', String),
    Column('тег', String),
    Column('площадка', String)
)

Session = sessionmaker(bind=engine)
session = Session()
# Создаем приложение Flask
app = Flask(__name__, template_folder='templates', static_folder='static')

@app.route('/')
def index():
    # Получаем все данные из таблицы
    stmt = select(курсы)
    rows = session.execute(stmt).fetchall()
    return render_template('index.html', rows=rows)

if __name__ == '__main__':
    app.run(debug=True)