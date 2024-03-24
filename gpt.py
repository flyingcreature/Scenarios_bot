import logging

import requests

from config import LOGS_PATH, MAX_MODEL_TOKENS, FOLDER_ID, URL_GPT, URL_TOKENS, MODELURI_GPT, MODELURI_TOKENS
from utils import get_iam_token

logging.basicConfig(
    filename=LOGS_PATH,
    level=logging.DEBUG,
    format="%(asctime)s %(message)s",
    filemode="w",
)


# Функция для подсчета токенов в истории сообщений. На вход обязательно принимает список словарей, а не строку!
def count_tokens_in_dialogue(messages):
    iam_token = get_iam_token()

    headers = {
        'Authorization': f'Bearer {iam_token}',
        'Content-Type': 'application/json'
    }
    data = {
        "modelUri": MODELURI_TOKENS,
        "maxTokens": MAX_MODEL_TOKENS,
        "text": messages
    }

    return len(
        requests.post(
            url=URL_TOKENS,
            json=data,
            headers=headers
        ).json()["tokens"]
    )


def get_system_content(genre, hero, setting):  # Собирает строку для system_content
    return (
        f"Придумай захватывающую историю в стиле {genre}. Главным героем будет {hero}."
        f" Происходить всё это будет {setting}. "
    )


def ask_gpt_helper(messages) -> str:
    """
    Отправляет запрос к модели GPT с задачей и предыдущим ответом
    для получения ответа или следующего шага
    """
    iam_token = get_iam_token()

    data = {
        "modelUri": MODELURI_GPT,
        "completionOptions": {
            "stream": False,
            "temperature": 0.6,
            "maxTokens": MAX_MODEL_TOKENS
        },
        "messages": [
            {
                "role": "user",
                "text": messages
            }
        ]
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {iam_token}",
        "x-folder-id": f"{FOLDER_ID}",
    }

    response = requests.post(
        url=URL_GPT,
        headers=headers,
        json=data
    )
    if response.status_code == 200:
        result = response.json()["result"]["alternatives"][0]["message"]["text"]
        logging.debug(f"Получен результат: {result}")
        return result
    else:
        print("Не удалось получить ответ :(")
        logging.error(f"Получена ошибка: {response.json()}")
