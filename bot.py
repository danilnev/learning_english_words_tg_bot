from telebot import TeleBot, types
import db_work_sqlite as my_db
from config import bot_api_key
import random
import time
import check_functions

# making bot
bot = TeleBot(bot_api_key)


# start functions. register user
@bot.message_handler(commands=['start'])
def start(message):
    username = message.from_user.username
    if username == '':
        bot.send_message(message.chat.id, 'У вас не установлен уникальный username telegram, установить его, '
                                          'он нужен для создания вашего словаря! После этого снова напишите комманду '
                                          '/start')
        return

    # check register user or no, register user
    result = my_db.register_user_if_not_exists(username)
    if result:
        bot.send_message(message.chat.id, f'{username}, вы успешно зарегистрированы! /menu - попасть в главное меню')
    else:
        bot.send_message(message.chat.id, f'{username}, вы уже регистрировались) /menu - попасть в главное меню')
    main_menu(message)


# main menu with different actions
@bot.message_handler(commands=['menu'])
def main_menu(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Добавить слова', callback_data='add_words'))
    markup.add(types.InlineKeyboardButton('Удалить слова', callback_data='delete_words'))
    markup.add(types.InlineKeyboardButton('Тестирование: N рандомных слов', callback_data='get_n_random_words'))
    markup.add(types.InlineKeyboardButton('Тестирование: N последних слов', callback_data='get_n_last_words'))
    markup.add(types.InlineKeyboardButton('Получить последние N добавленных слов',
                                          callback_data='get_n_last_words_without_shuffle'))
    markup.add(types.InlineKeyboardButton('Получить перевод слова', callback_data='get_translation'))
    bot.send_message(message.chat.id, 'Чем займемся?', reply_markup=markup)


# callback query
@bot.callback_query_handler(func=lambda callback: True)
def callback_query(callback):
    match callback.data:
        # adding new words and translations to database
        case 'add_words':
            msg = bot.send_message(callback.message.chat.id,
                                   'Вводите слова по таким правилам:\n! слово или фраза на английском, двоеточие,'
                                   'и разделенные точкой с запятой твои переводы на русский\n'
                                   '! в каждом сообщении одно слово\n'
                                   '! когда захочешь остановиться просто введи "stop"\n'
                                   '! из символов разрешено использовать только пробел, запятую, дефис '
                                   '(в русском слове), вопросительные'
                                   ' знак и одинарную кавычку (в английском слове)'
                                   )
            bot.register_next_step_handler(msg, lambda f: add_words(f, dict()))
        # deleting words from database
        case 'delete_words':
            msg = bot.send_message(callback.message.chat.id,
                                   'Вводите слова которые надо удалить, разделяя переводом строки')
            bot.register_next_step_handler(msg, delete_words)
        # test with user's number of last words from database
        case 'get_n_last_words':
            msg = bot.send_message(callback.message.chat.id, 'Введите кол-во слов:\n! Аккуратнее с числом, '
                                                             'слова будут выводиться с промежутком в 2 секунды, '
                                                             'не вводите очень большие числа!')
            bot.register_next_step_handler(msg, lambda f: get_n_of_words_from_user(f, type='last'))
        # test with user's number of random words from database
        case 'get_n_random_words':
            msg = bot.send_message(callback.message.chat.id, 'Введите кол-во слов:\n! Аккуратнее с числом, '
                                                             'слова будут выводиться с промежутком в 2 секунды, '
                                                             'не вводите очень большие числа!')
            bot.register_next_step_handler(msg, lambda f: get_n_of_words_from_user(f, type='random'))
        # merely get n last words from database without test
        case 'get_n_last_words_without_shuffle':
            msg = bot.send_message(callback.message.chat.id, 'Введите кол-во слов:')
            bot.register_next_step_handler(msg, lambda f: get_n_of_words_from_user(f, type='merely'))
        # merely getting word's translation from database
        case 'get_translation':
            msg = bot.send_message(callback.message.chat.id, 'Введите слово:')
            bot.register_next_step_handler(msg, get_one_translation)
        # back to main menu
        case 'main_menu':
            main_menu(message=callback.message)


# function to get how many words return to user ( type = last | random | merely )
def get_n_of_words_from_user(message, type: str):
    # check to number of words is integer
    if not message.text.isdigit():
        msg = bot.send_message(message.chat.id, 'Нужно ввести число!')
        main_menu(message=msg)
        return

    n = int(message.text)
    get_n_words(message=message, n=n, type=type)


# function to adding new words to database
def add_words(message, data):
    # stop adding
    if message.text == 'stop':
        username = message.chat.username
        my_db.add_words(username=username, data=data)
        bot.send_message(message.chat.id, f'Добавленные слова: {", ".join(data.keys())}')
        main_menu(message=message)
        return

    # check to correct entered word or no
    check_error = check_functions.check_text_to_adding_words(text=message.text)
    if check_error['error']:
        msg = bot.send_message(message.chat.id, check_error['text'])
        bot.register_next_step_handler(msg, lambda f: add_words(f, data))
        return

    # adding word and his translation to dictionary
    main_word = message.text.split(':')[0]
    translations = message.text.split(':')[1].split(';')
    data[main_word] = translations
    message = bot.send_message(message.chat.id, 'ok')
    bot.register_next_step_handler(message, lambda f: add_words(f, data=data))


# function who delete words from database
def delete_words(message):
    words = message.text.split('\n')
    username = message.chat.username
    my_db.delete_word(username=username, data=words)
    message = bot.send_message(message.chat.id, 'Те слова, что были найлены в таблице, удалены!')
    main_menu(message=message)


# returns any last words to user from database ( type = last | random | merely)
def get_n_words(message, n: int, type: str):
    username = message.chat.username

    # return to user any last added words to database with shuffling
    if type == 'last':
        data = my_db.get_n_last_words(username=username, n=n, shuffle=True)
        print_words_to_user(message=message, database_columns=data)
        return
    # return to user any random words from database
    elif type == 'random':
        data = my_db.get_n_random_words(username=username, n=n)
        print_words_to_user(message=message, database_columns=data)
        return
    # return to user any last added words to database without shuffling
    elif type == 'merely':
        data = my_db.get_n_last_words(username=username, n=n, shuffle=False)
        words = '\n'.join(list(map(lambda x: f'{x[0]} - {"; ".join(x[1])}', data)))
        msg = bot.send_message(message.chat.id, f'Последние {n} слов:\n{words}')
        main_menu(message=msg)


# function who returns to user messages with words for test (translations don't display in begin)
def print_words_to_user(message, database_columns):
    messages = list(map(lambda x: f"{random.choice(x[1])}: ||{x[0]}||", database_columns))
    for one_message in messages[:-1]:
        bot.send_message(message.chat.id, one_message, parse_mode='MarkdownV2')
        time.sleep(2)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Главное меню', callback_data='main_menu'))
    bot.send_message(message.chat.id, messages[-1], reply_markup=markup, parse_mode='MarkdownV2')


# merely getting one translation of user's word
def get_one_translation(message):
    translations = my_db.get_one_translation(username=message.chat.username, word=message.text)
    words = "; ".join(translations)
    bot.send_message(message.chat.id, f'Перевод {message.text} на русский: {words}')
    main_menu(message=message)


if __name__ == '__main__':
    bot.polling(none_stop=True)
