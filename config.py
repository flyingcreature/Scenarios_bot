import os

from dotenv import load_dotenv


LOGS_PATH = "log_file.txt"  # Путь к файлу логов

MAX_MODEL_TOKENS = 200  # Максимальный размер ответа

DB_NAME = "db.sqlite"  # Название базы данных

DB_TABLE_USERS_NAME = "users"  # Название таблицы пользователей в базе

ADMINS = [1645457137]  # Список user_id админов

MAX_SESSIONS = 3  # Максимальное количество сессий на пользователя

MAX_TOKENS_PER_SESSION = 1000  # Максимальное количество токенов на сессию

MAX_USERS = 5  # Максимальное количество пользователей приложения

load_dotenv()

FOLDER_ID = os.getenv("folder_id")

IAM_TOKEN = os.getenv("iam_token")

BOT_TOKEN = os.getenv("token")

URL_GPT = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"  # Cылка на gpt

URL_TOKENS = "https://llm.api.cloud.yandex.net/foundationModels/v1/tokenize"  # Cылка на токены gpt

MODELURI_GPT = f"gpt://{FOLDER_ID}/yandexgpt-lite"  # Модель gpt

MODELURI_TOKENS = f"gpt://{FOLDER_ID}/yandexgpt/latest"  # Токены для модели



