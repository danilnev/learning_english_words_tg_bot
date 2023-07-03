import re


# function check to correct entered data or no
# if data is uncorrect then return error text
def check_text_to_adding_words(text):
    # check to correct position of ':'
    if len(text.split(':')) != 2:
        return {
            'error': True,
            'text': 'Двоеточие нужно использовать только один раз и разделять им английское слово и перевод!'
        }

    # check to word above ':' is english
    string = text.split(':')
    if not bool(re.match(r'^[a-zA-Z\s,-?\']+$', string[0])):
        return {'error': True, 'text': 'Слово до двоеточия должно быть английским!'}

    # check to search null translations
    if ('' in string[1].split(';')) or (' ' in string[1].split(';')):
        return {'error': True, 'text': 'Не должно быть пустых или пробельных переводов!'}

    # check to translations if russian
    string = string[1].split(';')
    if len(string) != len(list(filter(lambda x: bool(re.match(r'^[а-яА-ЯёЁ\s,-?]+$', x)), string))):
        return {'error': True, 'text': 'Переводы должны быть на русском языке!'}

    return {'error': False}
