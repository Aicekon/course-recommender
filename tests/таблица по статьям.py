from flask import Flask, render_template
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, select
from sqlalchemy.orm import sessionmaker

# Параметры подключения к PostgreSQL
DATABASE_URI = 'postgresql://postgres:1111@localhost:5432/postgres'

# Создаем движок базы данных
engine = create_engine(DATABASE_URI)
metadata = MetaData()

# Описываем таблицу
articles = Table('articles', metadata,
    Column('id', Integer, primary_key=True),
    Column('title', String),
    Column('link', String),
    Column('views', String),  # Изменен тип на String
    Column('date_published', String),
    Column('source', String),
    Column('tag', String),
    Column('description', String),
    Column('complexity_level', String),
    Column('informational_value', String)
)

Session = sessionmaker(bind=engine)
session = Session()

# Создаем приложение Flask
app = Flask(__name__, template_folder='templates', static_folder='static')

@app.route('/')
def index():
    # Получаем все данные из таблицы
    stmt = select(articles)
    rows = session.execute(stmt).fetchall()
    return render_template('index2.html', rows=rows)

if __name__ == '__main__':
    app.run(debug=True)