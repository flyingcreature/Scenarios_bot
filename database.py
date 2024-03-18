import sqlite3
from config import DB_TABLE
from utils import logging


def prepare_database():
    """
    Функция для создания таблицы.
    """
    try:
        # Установка соединения с базой данных
        connection = sqlite3.connect(DB_TABLE)
        cur = connection.cursor()

        # Создание таблицы users, если она не существует
        cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY,
                            user_id INTEGER,
                            user_name TEXT,
                            subject TEXT,
                            level TEXT,
                            task TEXT,
                            answer TEXT
        );''')
        # cur.execute("""DROP TABLE users""")

        connection.commit()

    except sqlite3.Error as e:
        print("Ошибка при работе с SQLite:", e)
        logging.error("Ошибка при создании SQLite:", e)
    finally:
        connection.close()


def execute_query(query: str, data: tuple | None = None, db_file: str = DB_TABLE):
    """
    Функция для выполнения запроса к базе данных.
    Принимает имя файла базы данных, SQL-запрос и опциональные данные для вставки.
    """
    try:
        connection = sqlite3.connect(db_file)
        cursor = connection.cursor()

        if data:
            cursor.execute(query, data)
            connection.commit()
        else:
            cursor.execute(query)

    except sqlite3.Error as e:
        print("Ошибка при выполнении запроса:", e)
        logging.error("Ошибка при выполнении запроса:", e)

    else:
        result = cursor.fetchall()
        connection.close()
        return result


def is_user_in_db(user_id: int) -> bool:
    """
    Проверка есть ли, пользователь в базе

    """
    query = (
        """
        SELECT user_id 
        FROM users 
        WHERE user_id = ?;
        """
    )
    return bool(execute_query(query, (user_id,)))


def get_user_data(user_id: int):
    """
    Функция для получения значений пользователя.
    """
    if is_user_in_db(user_id):

        #  SQL-запрос для выборки всех студентов из таблицы users
        query = (
            f"SELECT * "
            f"FROM users "
            f"WHERE user_id = {user_id}"

        )

        row = execute_query(query)[0]
        result = {
            "user_id": row[1],
            "subject": row[3],
            "level": row[4],
            "task": row[5],
            "answer": row[6]
        }
        return result
    else:
        print("Не удалось найти значения пользователя.")
        logging.info("Не удалось найти значения пользователя.")


def add_user(user_id: int, user_name: str,
             subject: str | None, level: str | None, task: str | None, answer: str | None):
    """
    Функция для добавления нового студента в базу данных.
    """
    if not is_user_in_db(user_id):
        #  SQL-запрос для вставки данных о новом пользователе в таблицу users
        query = '''
        INSERT INTO users (user_id, user_name, subject, level, task, answer)
        VALUES (?, ?, ?, ?, ?, ?);
         '''
        data = (user_id, user_name, subject, level, task, answer)

        execute_query(query, data)
        print(f"Новый пользователь {user_name} успешно добавлен в таблицу.")
        logging.info(f"Новый пользователь {user_name} успешно добавлен в таблицу.")
    else:
        print(f"Пользователь {user_name}у же существует.")
        logging.info(f"Пользователь {user_name} уже существует.")


def delete_user(user_id):
    """
    Функция для удаления записи о пользователе из базы данных.
    """
    if is_user_in_db(user_id):
        # SQL-запрос для удаления записи о пользователе
        query = '''
        DELETE 
        FROM users 
        WHERE user_id = ?;
        '''
        data = (user_id,)  # Запятая нужна для кортежа

        execute_query(query, data)
        print("Запись о студенте успешно удалена.")
        logging.info("Запись о студенте успешно удалена.")
    else:
        print("Пользователь не найден в базе.")
        logging.error("Пользователь не найден в базе.")


def update_row(user_id: int, column_name: str, new_value: str | None):
    """
    Функция для обновления данных пользователя.
    """
    if is_user_in_db(user_id):
        query = (
            f"UPDATE users "
            f"SET {column_name} = ? "
            f"WHERE user_id = ?;"
        )
        execute_query(query, (new_value, user_id))
        print("Значение обновлено.")
        logging.info("Значение обновлено.")
    else:
        print("Пользователь не найден.")
        logging.error("Пользователь не найден.")


def get_user():
    """
    Функция для получения списка всех студентов, отсортированных по имени.
    """

    #  SQL-запрос для выборки всех студентов из таблицы users
    query = '''
    SELECT * 
    FROM users;
    '''
    users = execute_query(query)

    for row in users:
        print(row)

