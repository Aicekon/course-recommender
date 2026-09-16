import psycopg2

db_params = {
    'dbname': 'postgres',
    'user': 'postgres',
    'password': '1111',
    'host': 'localhost',
    'port': '5432'
}

with psycopg2.connect(**db_params) as conn:
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id SERIAL PRIMARY KEY,
            question_text TEXT NOT NULL,
            tag TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS answers (
            id SERIAL PRIMARY KEY,
            question_id INTEGER REFERENCES questions(id),
            answer_text TEXT NOT NULL,
            is_correct BOOLEAN NOT NULL
        );
    ''')
    conn.commit()