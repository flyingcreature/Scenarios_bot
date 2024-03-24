import json
import logging
import time

from telebot.types import ReplyKeyboardMarkup

from config import IAM_TOKEN_ENDPOINT, IAM_TOKEN_PATH
import requests



def load_data(path: str) -> dict:
    """
    Загружает данные из json по переданному пути и возвращает
    преобразованные данные в виде словаря.

    Если json по переданному
    пути не найден или его структура некорректна, то возвращает
    пустой словарь.
    """
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        return {}


def save_data(data: dict, path: str) -> None:
    """
    Сохраняет переданный словарь в json по переданному пути.
    """
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def create_keyboard(buttons: list[str]) -> ReplyKeyboardMarkup:
    """
    Создает объект клавиатуры для бота по переданному списку строк.
    """
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(*buttons)
    return keyboard


def create_new_iam_token():
    """Создание нового токена"""
    headers = {"Metadata-Flavor": "Google"}

    try:
        response = requests.get(IAM_TOKEN_ENDPOINT, headers=headers)
        if response.status_code == 200:
            token_data = response.json()
            token_data["expires_at"] = time.time() + token_data['expires_in']

            with open(IAM_TOKEN_PATH, "W") as token_file:
                json.dump(token_data, token_file)

            logging.info("Iam токен создан")
            return response.json()["access_token"]

        else:
            print(f"Проблемы с запросом: {response.status_code} токен не был создан")
            logging.error(f"Проблемы с запросом: {response.status_code} токен не был создан")

    except Exception as e:
        print(f"Произошла ошибка {e}, токен не был создан")
        logging.error(f"Произошла ошибка {e}, токен не был создан")


def get_iam_token():
    try:
        with open(IAM_TOKEN_PATH, "r") as file:
            data = json.load(file)
            expiration = data["expires_at"]

        if expiration < time.time():
            return create_new_iam_token()
        else:
            return data["access_token"]

    except:
        return create_new_iam_token()

