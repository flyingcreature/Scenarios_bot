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
    """
    Получает новый IAM-TOKEN и дату истечения его срока годности и
    записывает полученные данные в json
    """
    headers = {"Metadata-Flavor": "Google"}

    try:
        response = requests.get(IAM_TOKEN_ENDPOINT, headers=headers)

    except Exception as e:
        print(f"Не удалось выполнить запрос: {e}, токен не получен")
        logging.error(f"Не удалось выполнить запрос: {e}, токен не получен")
    else:
        if response.status_code == 200:
            token_data = {
                "access_token": response.json().get("access_token"),
                "expires_at": response.json().get("expires_in") + time.time()
            }

            with open(IAM_TOKEN_PATH, "w") as token_file:
                json.dump(token_data, token_file)
                logging.info("Iam токен создан")
        else:
            print(f"Ошибка при получении ответа: {response.status_code}, токен не получен")
            logging.error(f"Ошибка при получении ответа: {response.status_code}, токен не получен")


def get_iam_token() -> str:
    """
    Получает действующий IAM-TOKEN и возвращает его
    """
    try:
        with open(IAM_TOKEN_PATH, "r") as token_file:
            token_data = json.load(token_file)

        expires_at = token_data.get("expires_at")

        if expires_at <= time.time():
            create_new_iam_token()

    except FileNotFoundError:
        create_new_iam_token()

    with open(IAM_TOKEN_PATH, "r") as token_file:
        token_data = json.load(token_file)

    return token_data.get("access_token")
