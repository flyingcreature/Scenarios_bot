import json

import logging

import requests

from config import (LOGS_PATH, MAX_MODEL_TOKENS, FOLDER_ID, URL_GPT, URL_TOKENS, TOKENS_DATA_PATH, GPT_MODEL)
from utils import get_iam_token

logging.basicConfig(
    filename=LOGS_PATH,
    level=logging.DEBUG,
    format="%(asctime)s %(message)s",
    filemode="w",
)


# Функция для подсчета токенов в истории сообщений. На вход обязательно принимает список словарей, а не строку!
def count_tokens_in_dialogue(messages: list) -> int:
    iam_token = get_iam_token()
    headers = {
        'Authorization': f'Bearer {iam_token}',
        'Content-Type': 'application/json'
    }
    data = {
        "modelUri": f"gpt://{FOLDER_ID}/{GPT_MODEL}/latest",
        "maxTokens": MAX_MODEL_TOKENS,
        "messages": []
    }

    for row in messages:
        data["messages"].append(
            {
                "role": row["role"],
                "text": row["content"]
            }
        )

    result = requests.post(
        url=URL_TOKENS,
        json=data,
        headers=headers
    )

    return len(result.json()["tokens"])


def get_system_content(genre, hero, setting):  # Собирает строку для system_content
    return (
        f"Придумай захватывающую историю в стиле {genre}. Главным героем будет {hero}."
        f"{setting}. Историю вы пишете по очереди. Начинает человек, а ты продолжаешь."
        f"Не пиши никакого пояснительного текста в начале, а просто логично продолжай историю."
    )


def increment_tokens_by_request(messages: list[dict]):
    """
    Добавляет количество токенов потраченных на запрос и ответ
    к общей сумме в json файле
    """
    try:
        with open(TOKENS_DATA_PATH, "r") as token_file:
            tokens_count = json.load(token_file)["tokens_count"]

    except FileNotFoundError:
        tokens_count = 2000

    current_tokens_used = count_tokens_in_dialogue(messages)
    tokens_count += current_tokens_used

    with open(TOKENS_DATA_PATH, "w") as token_file:
        json.dump({"tokens_count": tokens_count}, token_file)


def ask_gpt_helper(messages) -> str:
    """
    Отправляет запрос к модели GPT с задачей и предыдущим ответом
    для получения ответа или следующего шага
    """
    iam_token = get_iam_token()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {iam_token}",
        "x-folder-id": f"{FOLDER_ID}",
    }

    data = {
        "modelUri": f"gpt://{FOLDER_ID}/{GPT_MODEL}/latest",
        "completionOptions": {
            "stream": False,
            "temperature": 0.6,
            "maxTokens": MAX_MODEL_TOKENS
        },
        "messages": []
    }

    for row in messages:
        data["messages"].append(
            {
                "role": row["role"],
                "text": row["content"]
            }
        )
    try:
        response = requests.post(
            url=URL_GPT,
            headers=headers,
            json=data
        )
    except Exception as e:
        print(f"Произошла непредвиденная ошибка: {e}.")
        logging.error(f"Произошла непредвиденная ошибка: {e}.")
    else:
        if response.status_code != 200:
            print("Не удалось получить ответ :(")
            logging.error(f"Получена ошибка: {response.json()}")

        else:
            result = response.json()["result"]["alternatives"][0]["message"]["text"]
            messages.append({"role": "assistant", "content": result})
            increment_tokens_by_request(messages)
            return result

