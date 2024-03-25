import json

import logging

import requests

from config import (LOGS_PATH, MAX_MODEL_TOKENS, FOLDER_ID, URL_GPT, URL_TOKENS, MODELURI_GPT, MODELURI_TOKENS,
                    TOKENS_DATA_PATH)
from utils import get_iam_token

logging.basicConfig(
    filename=LOGS_PATH,
    level=logging.DEBUG,
    format="%(asctime)s %(message)s",
    filemode="w",
)


# Функция для подсчета токенов в истории сообщений. На вход обязательно принимает список словарей, а не строку!
def count_tokens_in_dialogue(messages: list) -> int:
    iam_token = "t1.9euelZqLzpSRyI6bk8uWnJSNy4qRlu3rnpWam4qWkYzGzI7OxpCWls-clZ7l8_cYYHpP-e93ZmJV_t3z91gOeE_573dmYlX-zef1656Vmp3MnpLGzsacnJPNjs-bnZ6Z7_zF656Vmp3MnpLGzsacnJPNjs-bnZ6ZveuelZqQnIzMls3OmMmQyZKPjZyTirXehpzRnJCSj4qLmtGLmdKckJKPioua0pKai56bnoue0oye.HUCcHusDbDtqG3HQOoehu0Ajdyj3sMsfLFaLfVJ-cx79gqTKJxwoViMvogvlFrCSHBJUkIcZyZK2tsEme_2NBQ"

        #get_iam_token()

    headers = {
        'Authorization': f'Bearer {iam_token}',
        'Content-Type': 'application/json'
    }
    data = {
        "modelUri": MODELURI_TOKENS,
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
    iam_token ="t1.9euelZqLzpSRyI6bk8uWnJSNy4qRlu3rnpWam4qWkYzGzI7OxpCWls-clZ7l8_cYYHpP-e93ZmJV_t3z91gOeE_573dmYlX-zef1656Vmp3MnpLGzsacnJPNjs-bnZ6Z7_zF656Vmp3MnpLGzsacnJPNjs-bnZ6ZveuelZqQnIzMls3OmMmQyZKPjZyTirXehpzRnJCSj4qLmtGLmdKckJKPioua0pKai56bnoue0oye.HUCcHusDbDtqG3HQOoehu0Ajdyj3sMsfLFaLfVJ-cx79gqTKJxwoViMvogvlFrCSHBJUkIcZyZK2tsEme_2NBQ"

        #get_iam_token()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {iam_token}",
        "x-folder-id": f"{FOLDER_ID}",
    }

    data = {
        "modelUri": MODELURI_GPT,
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

