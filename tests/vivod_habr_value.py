import psycopg2
from tabulate import tabulate

# Параметры подключения к БД
db_params = {
    'dbname': 'postgres',
    'user': 'postgres',
    'password': '1111',
    'host': 'localhost',
    'port': '5432'
}

def fetch_data(query):
    """Выполняет SQL-запрос и возвращает данные"""
    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        cur.execute(query)
        return cur.fetchall()
    except Exception as e:
        print(f"Ошибка при выполнении запроса: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()

# 1. Статьи по категориям (по 2 из каждой)
query1 = '''
    (SELECT title, informational_value 
     FROM articles 
     WHERE informational_value = 'news/announcement' 
     ORDER BY date_published DESC 
     LIMIT 2)
    UNION ALL
    (SELECT title, informational_value 
     FROM articles 
     WHERE informational_value = 'technical tutorial' 
     ORDER BY date_published DESC 
     LIMIT 2)
    UNION ALL
    (SELECT title, informational_value 
     FROM articles 
     WHERE informational_value = 'opinion/discussion' 
     ORDER BY date_published DESC 
     LIMIT 2)
'''

# 2. Технические учебники по уровням сложности (по 2 каждого уровня)
query2 = '''
    (SELECT title, complexity_level 
     FROM articles 
     WHERE informational_value = 'technical tutorial' 
     AND complexity_level = 'hard' 
     ORDER BY date_published DESC 
     LIMIT 2)
    UNION ALL
    (SELECT title, complexity_level 
     FROM articles 
     WHERE informational_value = 'technical tutorial' 
     AND complexity_level = 'easy' 
     ORDER BY date_published DESC 
     LIMIT 2)
    UNION ALL
    (SELECT title, complexity_level 
     FROM articles 
     WHERE informational_value = 'technical tutorial' 
     AND complexity_level = 'normal' 
     ORDER BY date_published DESC 
     LIMIT 2)
'''

# Получаем данные для таблиц
data1 = fetch_data(query1)
data2 = fetch_data(query2)

# Генерируем HTML
html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Отчет по статьям и учебникам</title>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            max-width: 1200px;
            margin-left: auto;
            margin-right: auto;
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
            margin-bottom: 30px;
        }}
        h2 {{
            color: #2c3e50;
            margin-top: 40px;
            margin-bottom: 15px;
            padding-bottom: 5px;
            border-bottom: 1px solid #eee;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            font-size: 14px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #f8f9fa;
            position: sticky;
            top: 0;
            font-weight: bold;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        tr:hover {{
            background-color: #f1f1f1;
        }}
        .table-container {{
            overflow: auto;
            margin-bottom: 40px;
            border-radius: 5px;
            border: 1px solid #eee;
        }}
    </style>
</head>
<body>
    <h1>Отчет по материалам</h1>

    <h2>Статьи по категориям</h2>
    <div class="table-container">
        {tabulate(data1, headers=['Название статьи', 'Тип статьи'], tablefmt='html')}
    </div>

    <h2>Технические учебники по уровням сложности</h2>
    <div class="table-container">
        {tabulate(data2, headers=['Название учебника', 'Уровень сложности'], tablefmt='html')}
    </div>
</body>
</html>
"""

with open('vertical_tables_report.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print("HTML-отчет успешно создан: vertical_tables_report.html")