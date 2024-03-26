import json
import logging

import telebot
from telebot.types import Message, ReplyKeyboardRemove

import db
from config import (ADMINS, LOGS_PATH, MAX_TOKENS_PER_SESSION, MAX_SESSIONS, MAX_USERS, MAX_MODEL_TOKENS, BOT_TOKEN,
                    TOKENS_DATA_PATH)
from gpt import ask_gpt_helper, count_tokens_in_dialogue, get_system_content
from utils import create_keyboard

# Инициируем логгер по пути константы с уровнем логгирования debug
logging.basicConfig(
    filename=LOGS_PATH,
    level=logging.DEBUG,
    format="%(asctime)s %(message)s",
    filemode="w",
)

bot = telebot.TeleBot(BOT_TOKEN)

# Создаем базу и табличку в ней
db.create_db()
db.create_table()

# Определяем списки предметов и уровней сложности
genre_list = [
    "Хоррор",
    "Комедия",
    "Боевик",
]
hero_list = [
    "Дарт Вейдер",
    "Ада Лавлейс",
    "Легионер",
    "Анна Ахматова"
]

end_list = [
    "Сгенерировать историю",
    "Показать всю историю"
]

setting_list = {
    "В горах": "События будут разворачиваться на фоне красивых природных пейзажей, "
               "а герои будут сталкиваться с опасностями и преодолевать трудности, связанными с горной местностью🏔️.",
    "В космосе": "События развиваются за пределами Земли. Герои могут сталкиваться с различными опасностями, "
                 "связанные с космическими путешествиями🪐.",
    "В ГТА5": "События разворачиваются в открытом мире игры, "
              "который включает в себя три крупных города и множество небольших населенных пунктов. "
              "Главные герои - трое преступников, которые пытаются наладить свою жизнь, "
              "но постоянно попадают в новые неприятности. "
              "В игре присутствует огромный выбор различных миссий, заданий и развлечений, "
              "а также возможность свободно исследовать мир и взаимодействовать с его обитателями🤩."
}


@bot.message_handler(commands=["start"])
def start(message):
    user_name = message.from_user.first_name
    user_id = message.from_user.id

    if not db.is_user_in_db(user_id):  # Если пользователя в базе нет
        if len(db.get_all_users_data()) < MAX_USERS:  # Если число зарегистрированных пользователей меньше допустимого
            db.add_new_user(user_id)  # Регистрируем нового пользователя
        else:
            text = "К сожалению, лимит пользователей исчерпан. Вы не сможете воспользоваться ботом:("

            bot.send_message(
                chat_id=user_id,
                text=text
            )
            return

    # Этот блок срабатывает только для зарегистрированных пользователей

    text = (
        f"Привет, {user_name}! Я бот-сценарист, и мы вместе можем придумать увлекательную историю 🎇.\n\n"
        f"Ты должен выбрать жанр своей истории, главного героя,"
        f" и сеттинг(это место где будет происходить итсория 🌳 🌆 🌑), "
        f"по желанию можешь написать дополнителные комментарии, или оставить всё, как есть.\n"
        f"Иногда ответы получаются слишком длинными - в этом случае ты можешь попросить продолжить.\n\n"
        f"Ну что, начём?"
    )

    bot.send_message(
        chat_id=user_id,
        text=text,
        reply_markup=create_keyboard(["Начать историю!"])  # Добавляем кнопочку для ответа
    )
    # Насильно уводим пользователя в функцию выбора предмета (независимо от того нажмет ли он кнопку или отправит
    # какое-нибудь другое сообщение)
    bot.register_next_step_handler(message, choose_genre)


def filter_choose_genre(message: Message) -> bool:
    user_id = message.from_user.id
    if db.is_user_in_db(user_id):
        return message.text in ["Начать историю!", "Изменить жанр/героя/сеттинг", "Начать новую сессию"]


@bot.message_handler(func=filter_choose_genre)
def choose_genre(message: Message):
    user_id = message.from_user.id
    sessions = db.get_user_data(user_id)["sessions"]  # Получаем из БД актуальное количество сессий пользователя
    if sessions < MAX_SESSIONS:  # Если число сессий пользователя не достигло предела
        db.update_row(user_id, "sessions", sessions + 1)  # Накручиваем ему +1 сессию
        db.update_row(user_id, "tokens", MAX_TOKENS_PER_SESSION)  # И обновляем его токены
        bot.send_message(
            chat_id=user_id,
            text="Выбери жанр 🎭, для своей истории:",
            reply_markup=create_keyboard(genre_list)
        )
        bot.register_next_step_handler(message, genre_selection)

    else:
        bot.send_message(
            chat_id=user_id,
            text="К сожалению, лимит твоих историй исчерпан:("
        )


def genre_selection(message: Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    user_choice = message.text  # Получаем выбор жанра пользователя
    if user_choice in genre_list:  # Проверка выбора пользователя
        db.update_row(user_id, "genre", user_choice)
        bot.send_message(
            chat_id=user_id,
            text=(
                f"Отлично, {user_name}, мы определились с жанром '{user_choice}'!"
                f"Давай теперь выберем главного героя 🦸‍♂️.")
            ,
            reply_markup=create_keyboard(hero_list)
        )
        bot.register_next_step_handler(message, hero_selection)

    else:  # Если был выбран предмет не из нашего списка
        bot.send_message(
            chat_id=user_id,
            text="К сожалению, такого жанра нет, выбери один из предложенных в меню.",
            reply_markup=create_keyboard(genre_list),
        )
        bot.register_next_step_handler(message, genre_selection)


def hero_selection(message: Message):  # Всё то же самое только для выбора героя.
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    user_choice = message.text
    if user_choice in hero_list:
        db.update_row(user_id, "hero", user_choice)

        bot.send_message(
            chat_id=user_id,
            text=(
                f"Принято, {user_name}! В главной роли будет: '{user_choice}'. "
                f"Давай теперь выберем сеттинг."
            ),
        )
        text = (
            "В какой сеттинг ты хочешь поместить героя:\n\n"
        )
        for setting in setting_list:
            text += f"{setting}: {setting_list[setting]}\n\n"

        bot.send_message(
            chat_id=user_id,
            text=text,
            reply_markup=create_keyboard(list(setting_list.keys())),
        )
        bot.register_next_step_handler(message, setting_selection)

    else:
        bot.send_message(
            chat_id=user_id,
            text="Пожалуйста, выбери сеттинг из предложенных:",
            reply_markup=create_keyboard(list(setting_list.keys())),
        )
        bot.register_next_step_handler(message, hero_selection)


def setting_selection(message: Message):  # Всё то же самое только для выбора сеттинга.
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    user_choice = message.text
    if user_choice in setting_list:
        db.update_row(user_id, "setting", setting_list[user_choice])
        bot.send_message(
            chat_id=user_id,
            text=(
                f"Принято, {user_name}! Действие будет происходить в '{user_choice}'. "
                f"Тебе есть, что добавить?"
            ),
            reply_markup=create_keyboard([
                "Добавить условие",
                "Сгенерировать  историю"
            ]
            )
        )

    else:
        bot.send_message(
            chat_id=user_id,
            text="Пожалуйста, выбери сеттинг из предложенных:",
            reply_markup=create_keyboard(list(setting_list.keys())),
        )
        bot.register_next_step_handler(message, setting_selection)


def filter_additionally(message: Message) -> bool:
    user_id = message.from_user.id
    if db.is_user_in_db(user_id):
        return message.text == "Добавить условие"


@bot.message_handler(func=filter_additionally)  # Если пользователь выбирает добавить условие выполняется этот блок
def write_additionally(message: Message):
    user_id = message.from_user.id

    bot.send_message(
        chat_id=user_id,
        text="Напиши дополнительные условия✍️:"
    )
    bot.register_next_step_handler(message, additionally_selection)


def additionally_selection(message: Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    selection = message.text

    db.update_row(user_id, "additionally", selection)
    bot.send_message(
        chat_id=user_id,
        text=(
            f"Принято, {user_name}! Дополнительное условие: '{selection}'. "
            f"А теперь жми на кнопочку  'Добавить в историю'"
        ),
        reply_markup=create_keyboard([
            "Добавить в историю"
        ]
        )
    )

    user_data = db.get_user_data(int(user_id))
    messages = user_data["messages"]

    if messages is None:
        bot.register_next_step_handler(message, create_a_story)
    else:
        bot.register_next_step_handler(message, continue_explaining)


def filter_create_a_story(message: Message) -> bool:
    user_id = message.from_user.id
    if db.is_user_in_db(user_id):
        return message.text == "Сгенерировать историю"


# Блок решения задач
@bot.message_handler(func=filter_create_a_story)
def create_a_story(message: Message):
    user_id = message.from_user.id
    user_tokens = db.get_user_data(user_id)["tokens"]  # Получаем актуальное количество токенов пользователя из БД
    genre = db.get_user_data(user_id)["genre"]  # Получаем выбранный жанр из БД
    hero = db.get_user_data(user_id)["hero"]  # Получаем выбранного героя из БД
    setting = db.get_user_data(user_id)["setting"]  # Получаем выбранный сеттинг из БД
    additionally = db.get_user_data(user_id)["additionally"]  # Получаем доп комментарии из БД

    db.update_row(user_id, "messages", None)  # При создании новой истории, обновляем БД

    system_content = get_system_content(genre, hero, setting)  # Формируем system_content

    messages = [
        {"role": "system", "content": system_content}
    ]  # Приводим контент к стандартизированному виду - списку из словарей сообщений

    if additionally is not None:  # Если пользователь ввел дополнительную информацию.
        content = (
            f"Также пользователь попросил учесть "
            f"следующую дополнительную информацию: {additionally}"
        )
        messages.append({"role": "system", "content": content})

    tokens_messages = count_tokens_in_dialogue(messages)  # Посчитаем вес запроса в токенах

    if tokens_messages + MAX_MODEL_TOKENS <= user_tokens:  # Проверим что вес запроса + максимального ответа меньше, чем
        # оставшееся количество токенов у пользователя, чтобы пользователю хватило и на запрос и на максимальный ответ
        bot.send_message(
            chat_id=user_id,
            text="Генерирую..."
        )
        answer = ask_gpt_helper(messages)  # Получаем ответ от GPT
        messages.append({"role": "assistant", "content": answer})  # Добавляем в наш словарик ответ GPT

        user_tokens -= count_tokens_in_dialogue([{"role": "assistant", "content": answer}])  # Получаем новое значение
        # оставшихся токенов пользователя - вычитаем стоимость запроса и ответа
        db.update_row(user_id, "tokens", user_tokens)  # Записываем новое значение в БД

        json_string = json.dumps(messages, ensure_ascii=False)  # Преобразуем список словарей сообщений к виду json
        # строки для хранения в одной ячейке БД
        db.update_row(user_id, "messages", json_string)  # Записываем получившуюся строку со всеми
        # сообщениями в ячейку 'messages'

        if answer is None:
            bot.send_message(
                chat_id=user_id,
                text="Не могу получить ответ от GPT :(",
                reply_markup=create_keyboard(
                    [
                        "Сгенерировать историю",
                        "Изменить жанр/героя/сеттинг",
                    ]
                ),
            )
            logging.info(f"Отправлено: {message.text}\nПолучена ошибка: не могу получить ответ от GPT")
        elif answer == "":
            bot.send_message(
                chat_id=user_id,
                text="Не могу сформулировать решение :(",
                reply_markup=create_keyboard(
                    [
                        "Сгенерировать историю",
                        "Изменить жанр/героя/сеттинг",
                    ]
                ),
            )
            logging.info(
                f"Отправлено: {message.text}\nПолучена ошибка: нейросеть вернула пустую строку"
            )
        else:
            bot.send_message(
                chat_id=user_id,
                text=answer,
                reply_markup=create_keyboard(
                    [
                        "Продолжить историю",
                        "Добавить условие",
                        "Завершить историю"
                    ]
                ),
            )

    else:  # Если у пользователя не хватает токенов на запрос + ответ
        bot.send_message(
            chat_id=user_id,
            text="Токенов на ответ может не хватить:( Начни новую сессию, или заверши историю.",
            reply_markup=create_keyboard(
                [
                    "Начать новую сессию",
                    "Завершить историю",
                    "Показать всю историю"
                ]
            )
        )
        logging.info(
            f"Отправлено: {message.text}\nПолучено: Предупреждение о нехватке токенов"
        )
        if message.text == "Завершить историю":
            bot.register_next_step_handler(message, send_end_story)


def filter_continue_explaining(message: Message) -> bool:
    user_id = message.from_user.id
    if db.is_user_in_db(user_id):
        return message.text == "Продолжить историю"


@bot.message_handler(func=filter_continue_explaining)
def continue_explaining(message):
    user_id = message.from_user.id
    json_string_messages = db.get_user_data(user_id)["messages"]  # Достаем из базы все предыдущие сообщения
    # в виде json-строки
    messages = json.loads(json_string_messages)  # Преобразуем json-строку в нужный нам формат списка словарей
    if not messages:  # Если попытались продолжить, но запроса еще не было
        bot.send_message(
            chat_id=user_id,
            text="Ты ещё не создавал историй, сделай это кнопкой ниже.",
            reply_markup=create_keyboard(["Начать историю!"]),
        )
        return
    user_content = "Продолжи историю."  # Формируем user_content

    messages.append({"role": "user", "content": user_content})  # Добавляем запрос от пользователя

    user_tokens = db.get_user_data(user_id)["tokens"]  # Получаем актуальное количество токенов пользователя
    tokens_messages = count_tokens_in_dialogue(messages)  # Считаем вес запроса в токенах из всех предыдущих сообщений

    if tokens_messages + MAX_MODEL_TOKENS <= user_tokens:  # Проверяем хватает ли токенов на запрос + ответ
        bot.send_message(
            chat_id=user_id,
            text="Формулирую продолжение..."
        )
        answer = ask_gpt_helper(messages)  # Получаем продолжение от gpt
        messages.append({"role": "assistant", "content": answer})  # Добавляем очередной ответ в список сообщений

        user_tokens -= count_tokens_in_dialogue([{"role": "assistant", "content": answer}])  # Вычитаем токены
        db.update_row(user_id, "tokens", user_tokens)  # Сохраняем новое значение токенов в БД

        json_string_messages = json.dumps(messages, ensure_ascii=False)  # Преобразуем список сообщений в строку для БД
        db.update_row(user_id, "messages", json_string_messages)  # Сохраняем строку сообщений в БД

        if answer is None:
            bot.send_message(
                chat_id=user_id,
                text="Не могу получить ответ от GPT :(",
                reply_markup=create_keyboard(
                    [
                        "Сгенерировать историю",
                        "Изменить жанр/героя/сеттинг",
                    ]
                ),
            )
        elif answer == "":
            bot.send_message(
                chat_id=user_id,
                text="История окончена ^-^",
                reply_markup=create_keyboard(
                    [
                        "Сгенерировать историю",
                        "Изменить жанр/героя/сеттинг",
                    ]
                ),
            )
        else:
            bot.send_message(
                chat_id=user_id,
                text=answer,
                reply_markup=create_keyboard(
                    [
                        "Продолжить историю",
                        "Добавить условие",
                        "Завершить историю"
                    ]
                ),
            )
    else:  # Если токенов на продолжение не хватило
        user_id = message.from_user.id
        bot.send_message(
            chat_id=user_id,
            text="Токенов на ответ может не хватить:( Пожалуйста, попробуй  создать новую историю.",
            reply_markup=create_keyboard(["Сгенерировать историю", "Завершить историю"]),
            # Предлагаем задать новый вопрос в рамках сессии
        )
        logging.info(
            f"Отправлено: {message.text}\nПолучено: Предупреждение о нехватке токенов"
        )

        if message.text == "Завершить историю":
            bot.register_next_step_handler(message, send_end_story)


def filter_end_story(message: Message) -> bool:
    user_id = message.from_user.id
    if db.is_user_in_db(user_id):
        return message.text == "Завершить историю"


@bot.message_handler(func=filter_end_story)
def send_end_story(message: Message):
    user_id = message.from_user.id
    json_string_messages = db.get_user_data(user_id)["messages"]  # Достаем из базы все предыдущие сообщения
    # в виде json-строки
    messages = json.loads(json_string_messages)  # Преобразуем json-строку в нужный нам формат списка словарей
    if not messages:  # Если попытались закончить, но запроса еще не было
        bot.send_message(
            chat_id=user_id,
            text="Ты ещё не создавал историй, сделай это кнопкой ниже.",
            reply_markup=create_keyboard(["Начать историю!"]),
        )
        return

    user_content = (
        "Напиши завершение истории c неожиданной развязкой. "
        "Не пиши никакой пояснительный текст от себя."
    )  # Формируем user_content

    messages.append({"role": "user", "content": user_content})  # Добавляем запрос пользовтаеля

    user_tokens = db.get_user_data(user_id)["tokens"]  # Получаем актуальное количество токенов пользователя
    tokens_messages = count_tokens_in_dialogue(messages)  # Считаем вес запроса в токенах из всех предыдущих сообщений

    required_tokens = (tokens_messages + MAX_MODEL_TOKENS) - user_tokens
    end_tokens = user_tokens + required_tokens
    db.update_row(user_id, "tokens", end_tokens)

    bot.send_message(
        chat_id=user_id,
        text="Формулирую концовку..."
    )
    answer = ask_gpt_helper(messages)  # Получаем концовку от gpt
    messages.append({"role": "assistant", "content": answer})  # Добавляем очередной ответ в список сообщений

    user_tokens -= count_tokens_in_dialogue([{"role": "assistant", "content": answer}])  # Вычитаем токены
    db.update_row(user_id, "tokens", user_tokens)  # Сохраняем новое значение токенов в БД

    json_string_messages = json.dumps(messages, ensure_ascii=False)  # Преобразуем список сообщений в строку для БД
    db.update_row(user_id, "messages", json_string_messages)  # Сохраняем строку сообщений в БД

    if answer is None:
        bot.send_message(
            chat_id=user_id,
            text="Не могу получить ответ от GPT :(",
            reply_markup=create_keyboard(
                [
                    "Сгенерировать историю",
                    "Изменить жанр/героя/сеттинг",
                ]
            ),
        )
    elif answer == "":
        bot.send_message(
            chat_id=user_id,
            text="История окончена ^-^",
            reply_markup=create_keyboard(
                [
                    "Сгенерировать историю",
                    "Изменить жанр/героя/сеттинг",
                ]
            ),
        )
    else:
        bot.send_message(
            chat_id=user_id,
            text=answer,
            reply_markup=create_keyboard(
                [
                    "Сгенерировать историю",
                    "Показать всю историю",

                ]
            ),
        )


def filter_all_story(message: Message) -> bool:
    user_id = message.from_user.id
    if db.is_user_in_db(user_id):
        return message.text == "Показать всю историю"


@bot.message_handler(func=filter_all_story)  # Функция для подсчёта токенов
def send_all_story(message: Message):
    user_id = message.from_user.id
    json_string_messages = db.get_user_data(user_id)["messages"]  # Достаем из базы все предыдущие сообщения
    # в виде json-строки
    messages = json.loads(json_string_messages)  # Преобразуем json-строку в нужный нам формат списка словарей
    if not messages:  # Если попытались посмотреть историю, но запроса еще не было
        bot.send_message(
            chat_id=user_id,
            text="Ты ещё не создавал историй, сделай это кнопкой ниже.",
            reply_markup=create_keyboard(["Начать историю!"]),
        )
        return

    all_story = ""
    for message in messages:
        if message["role"] == "assistant":
            all_story += message["content"]

    bot.send_message(
        chat_id=user_id,
        text=all_story,
        reply_markup=create_keyboard(
            [
                "Сгенерировать историю",
                "Изменить жанр/героя/сеттинг",
            ]
        )
    )


@bot.message_handler(commands=["kill_my_session"])
def kill_session(message: Message):
    user_id = message.from_user.id
    if user_id in ADMINS:
        try:
            db.update_row(user_id, "sessions", 1)

        except Exception as e:
            print(f"Произошла ошибка {e}, сессии не обновлены")
            logging.error(f"Произошла ошибка {e}, сессии не обновлены")
    else:
        print(f"{user_id} попытался обновить сессии")
        logging.info(f"{user_id} попытался обновить сессии")


@bot.message_handler(commands=["how_many_tokens"])
def how_many_tokens(message: Message):
    user_id = message.from_user.id
    if user_id in ADMINS:
        try:
            with open(TOKENS_DATA_PATH, "r") as f:
                tokens_count = json.load(f)["tokens_count"]

            bot.send_message(
                chat_id=user_id,
                text=f"За всё время израсходовано:{tokens_count} токенов."
            )
        except Exception as e:
            print(f"Произошла ошибка {e}, токены не выведены.")
            logging.error(f"Произошла ошибка {e}, токены не выведены.")
    else:
        print(f"{user_id} попытался узнать сколько токенов использовано.")
        logging.info(f"{user_id} попытался сколько токенов использовано.")


@bot.message_handler(commands=["all_tokens"])
def send_tokens(message: Message):  # Функция для подсчёта токенов
    user_id = message.from_user.id
    user_tokens = db.get_user_data(user_id)["tokens"]

    bot.send_message(
        chat_id=user_id,
        text=f"У тебя осталось {user_tokens} токенов."
    )


@bot.message_handler(commands=['debug'])
def send_logs(message):
    user_id = message.from_user.id
    if user_id in ADMINS:
        try:
            with open(LOGS_PATH, "rb") as f:
                bot.send_document(
                    message.chat.id,
                    f
                )
        except telebot.apihelper.ApiTelegramException:
            bot.send_message(
                chat_id=message.chat.id,
                text="Логов нет!"
            )
    else:
        print(f"{user_id} захотел посмотреть логи")
        logging.info(f"{user_id} захотел посмотреть логи")


@bot.message_handler(commands=['help'])
def help_command(message: Message):
    text = (
        "👋 Я твой цифровой собеседник.\n\n"
        "Что бы воспользоваться функцией gpt помощника 🕵‍♀️ следуй инструкциям бота .\n\n"
        "Этот бот сделан на базе нейронной сети YandexGPT Lite. \n"
        "Это мой первый опыт знакомства с gpt, "
        "поэтому не переживай если возникла какая-то ошибка. Просто сообщи мне об этом)\n"
        "И я постараюсь её решить."
    )
    bot.send_message(
        chat_id=message.chat.id,
        text=text,
        reply_markup=ReplyKeyboardRemove()
    )


def filter_hello(message):
    word = "привет"
    return word in message.text.lower()


@bot.message_handler(content_types=['text'], func=filter_hello)
def say_hello(message: Message):
    user_name = message.from_user.first_name
    bot.send_message(
        chat_id=message.chat.id,
        text=f"{user_name}, приветики 👋!"
    )


def filter_bye(message):
    word = "пока"
    return word in message.text.lower()


@bot.message_handler(content_types=["text"], func=filter_bye)
def say_bye(message: Message):
    bot.send_message(
        chat_id=message.chat.id,
        text="Пока, заходи ещё!"
    )


@bot.message_handler(func=lambda message: True, content_types=['audio', 'photo', 'voice', 'video', 'document',
                                                               'text', 'location', 'contact', 'sticker'])
def send_echo(message: Message):
    text = (
        f"Вы отправили ({message.text}).\n"
        f"Но к сожалению я вас не понял😔, для общения со мной используйте встроенные кнопки.🤗"
    )
    bot.send_message(
        chat_id=message.chat.id,
        text=text
    )


logging.info("Бот запущен")
bot.infinity_polling(timeout=60, long_polling_timeout=5)
