from dotenv import load_dotenv
from os import getenv

load_dotenv()

TOKEN = getenv("token")

GPT_URL = "http://localhost:1234/v1/chat/completions"  # Путь к серверу нейросети

LOGS_PATH = "log_file.txt"  # Путь к файлу логов

USER_DATA_PATH = "user_data.json"

MODEL_NAME = "mistralai/Mistral-7B-Instruct-v0.2"  # Название используемой нейросети

MAX_TASK_TOKENS = 150  # Максимальный размер запроса

DB_TABLE = 'sqlite3.db'  # Таблица SQL
