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

# IAM_TOKEN = os.getenv("iam_token")  используем, этот вариант, если автоматически не получаем токен на сервере

BOT_TOKEN = os.getenv("token")

GPT_MODEL = "yandexgpt"  # Модель gpt

URL_GPT = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"  # Cылка на gpt

URL_TOKENS = "https://llm.api.cloud.yandex.net/foundationModels/v1/tokenizeCompletion"  # Cылка на токены gpt

IAM_TOKEN_ENDPOINT = "http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token"  # Адресс токена

IAM_TOKEN_PATH = "token_data.json"  # Путь к json файлу с ключом

TOKENS_DATA_PATH = "tokens_count.json"  # Файл json с кол-ом токенов потраченного в боте
