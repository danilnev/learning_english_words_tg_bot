import sqlite3
import json
import random


# function which register new user
def register_user_if_not_exists(username: str):
    connection = sqlite3.connect('english_words.db')
    cursor = connection.cursor()

    # check register user or no by request to database table
    cursor.execute('''SELECT * FROM users WHERE username == :username''', {'username': username})
    if len(cursor.fetchall()) > 0:
        connection.close()
        return False

    # register user in database table
    cursor.execute('''INSERT INTO users (username) VALUES (:username)''', {'username': username})

    # creating table which include that user's words
    tablename = f'{username}_words'
    cursor.execute(f'''CREATE TABLE IF NOT EXISTS {tablename} (
        word_id INTEGER PRIMARY KEY AUTOINCREMENT,
        word TEXT NOT NULL,
        date DATETIME DEFAULT CURRENT_TIMESTAMP,
        translations TEXT NOT NULL
    )''')

    connection.commit()
    connection.close()
    return True


# function which add new words with their translations to user's table in database
def add_words(username: str, data: dict):
    connection = sqlite3.connect('english_words.db')
    cursor = connection.cursor()

    # checking for repeat of words
    for i in range(len(data.keys())):
        if list(data.keys()).count(list(data.keys())[i]) > 1:
            del data[list(data.keys())[i]]

    # checking for the '-' (would be '\-', because bot use MarkdownV2 parse mod)
    deleteds = []
    new_words = []
    for word in data:
        for trn in data[word]:
            if '-' in trn and '\\-' not in trn:
                data[word].append(trn.replace('-', '\\-'))
                del data[word][data[word].index(trn)]

        if '-' in word and '\\-' not in word:
            new_word = word.replace('-', '\\-')
            print(new_word)
            new_words.append((new_word, data[word]))
            deleteds.append(word)

    for word in deleteds:
        del data[word]

    for el in new_words:
        data[el[0]] = el[1]

    # adding words
    for word in data:
        # check to have user's table got this word
        cursor.execute(f'''SELECT translations FROM {username}_words WHERE word == "{word}"''')
        translations = cursor.fetchall()
        if len(translations) > 0:
            # update word translation
            translations = json.loads(translations[0][0])
            translations.extend(data[word])
            translations = list(set(translations))
            translations = json.dumps(translations)
            cursor.execute(f'''UPDATE {username}_words
            SET translations = :translations
            WHERE word == :word''', {'translations': translations, 'word': word})
            continue

        # adding new word and translations
        cursor.execute(f'''INSERT INTO {username}_words (word, translations) VALUES (
            :word, :translations
        )''', {'word': word, 'translations': json.dumps(data[word])})

    connection.commit()
    connection.close()


# function which get any words with their translations from user's table
def get_n_last_words(username: str, n: int, shuffle: bool):
    connection = sqlite3.connect('english_words.db')
    cursor = connection.cursor()

    # select data
    cursor.execute(f'''SELECT word, translations FROM {username}_words ORDER BY date DESC, word_id DESC LIMIT :n''', {'n': n})
    data = list(map(lambda x: (x[0], json.loads(x[1])), cursor.fetchall()))

    # shuffling result
    if shuffle:
        random.shuffle(data)

    connection.close()
    return data


# function which get any words from different places of the table in database
def get_n_random_words(username: str, n: int):
    connection = sqlite3.connect('english_words.db')
    cursor = connection.cursor()

    # get data
    cursor.execute(f'''SELECT word, translations FROM {username}_words''')
    data = cursor.fetchall()

    # random selecting
    if len(data) > n:
        data = random.sample(data, n)
    data = list(map(lambda x: (x[0], json.loads(x[1])), data))

    connection.close()
    return data


# function which delete word from table
def delete_word(username: str, data: list):
    connection = sqlite3.connect('english_words.db')
    cursor = connection.cursor()

    # deleting data
    for word in data:
        cursor.execute(f'''DELETE FROM {username}_words WHERE word == "{word}"''')
        connection.commit()

    connection.close()


# function which returns one translation
def get_one_translation(username: str, word: str):
    connection = sqlite3.connect('english_words.db')
    cursor = connection.cursor()

    # get translation
    cursor.execute(f'''SELECT translations FROM {username}_words WHERE word == "{word}"''')
    translation = cursor.fetchall()
    if len(translation) > 0:
        translation = json.loads(translation[0][0])
    else:
        translation = ['нет такого слова в таблице']

    connection.close()
    return translation


# mini tests
# register_user_if_not_exists('veemz')
# add_words('veemz', {'set': ['набор'], 'plain': ['простой', 'самолет']})
# print(get_n_last_words('veemz', 2))
