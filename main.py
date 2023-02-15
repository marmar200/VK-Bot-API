import random

import vk_api
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkLongPoll, VkEventType

# подключаем vk API
with open("token.txt") as f:
    token = f.readline()
vk = vk_api.VkApi(token=token)
longpool = VkLongPoll(vk)

list_unknown_msg = ["Не понял(", "Непонятно!", "Что?"]  # ответы на непонятные сообщения
list_hi_msg = ["Привет!", "Добрый день!", "Здорова!"]  # ответы на приветствия
users_hi_msg = ["привет", "ку", "здравствуйте", "здорова", "салам", "hi",
                "hello"]  # как может поздороваться пользователь

# записываем все города России в cities
cities = []
with open("cities.txt") as f:
    for line in f.readlines():
        cities.append(line.lower().replace('\n', ''))

uses = []  # города , которые были использованы в игре


class Flag:
    def __init__(self, x):
        self.x = x


def process_game_false(container_play_capital, container_question_play):
    container_play_capital.x = False
    container_question_play.x = False


flag_play_capital = Flag(False)  # flag обозначающий начало игры
flag_question_play = Flag(False)  # flag обозначающий, что предложение о начале игры было сделано

score = 0  # счет

# создаем клавиатуру с параматрами one_time=False, inline=False
keyboard = VkKeyboard()


# отправка сообщений
def send_some_msg(user_id, text, keyboard_send=None):
    post = {
        "user_id": user_id,
        "message": text,
        "random_id": 0
    }

    if keyboard_send != None:
        post["keyboard"] = keyboard_send.get_keyboard()

    vk.method("messages.send", post)


# начало игры
def start_game(user_id, cities_arr, uses_arr):
    uses_arr.append(random.choice(cities_arr))
    cities_arr.remove(uses_arr[-1])
    keyboard = VkKeyboard()
    keyboard.get_empty_keyboard()
    keyboard.add_button("Остановить игру", VkKeyboardColor.NEGATIVE)
    send_some_msg(user_id, "Вы можете в любой момент остановить игру, нажав на кнопку 'Остановить игру'", keyboard)
    send_some_msg(user_id, "Вы можете называть только Российские города")
    send_some_msg(user_id, uses_arr[-1].upper())


# процесс игры
def game_process(user_id, text, cities_arr, uses_arr, container_play_capital, container_question_play):
    uses_arr.append(msg) # добавляем город в использованные города

    flag_used_capital = False # flag подберем ли мы город

    # подбираем город
    for c in cities_arr:
        if text[-1].lower() == c[0] or ((text[-1].lower() == 'ь' or text[-1].lower() == 'ы') and text[-2] == c[0]):
            uses_arr.append(c)
            flag_used_capital = True
            break

    # если город подобрали
    if flag_used_capital:
        # исключаем города из списка всех городов России
        cities_arr.remove(text)
        cities_arr.remove(uses_arr[-1])
        send_some_msg(user_id, uses_arr[-1].upper())
    else:
        send_some_msg(user_id, "Вы выиграли!")
        process_game_false(container_play_capital, container_question_play)


# игра
def game(message, user_id, uses_arr, cities_arr, con_play_capital, con_question_play):
    f = True
    if message == "остановить игру":  # пользователь хочет остановить игру
        send_some_msg(user_id, "Игра остановлена")
        process_game_false(con_play_capital, con_question_play)
    elif message == "играть в города":  # хочет поиграть
        flag_play_capital.x = True
        start_game(user_id, cities_arr, uses_arr)
    elif flag_play_capital.x and len(message) >= 1: # проверяем что за город написал пользователь
        if (message[0].lower() == uses_arr[-1][-1].lower() or ((uses_arr[-1][-1].lower() == 'ь' or
                                                                uses_arr[-1][-1].lower() == 'ы')
                                                               and message[0].lower() == uses_arr[-1][-2].lower())) \
                and message not in uses_arr:
            if message in cities_arr:
                game_process(user_id, message, cities_arr, uses_arr, con_play_capital, con_question_play)
            else:
                send_some_msg(user_id, "Я не знаю такого города\nВы проиграли!")
                process_game_false(con_play_capital, con_question_play)
        else:
            send_some_msg(user_id, "Вы проиграли!")
            process_game_false(con_play_capital, con_question_play)

    if not (con_play_capital.x and con_question_play.x):
        f = False

    return f


# слушаем что хотят от нас
for event in longpool.listen():
    if event.type == VkEventType.MESSAGE_NEW:  # событие == новая смс
        if event.to_me:  # адресовано мне)
            flag_for_unknown_messages = 0
            msg = event.text.lower()  # текст смс
            current_id = event.user_id  # id пользователя , который отправил

            if not game(msg, current_id, uses, cities, flag_play_capital,
                        flag_question_play):  # проверяем играет ли пользователь
                # здороваемся , если пользователь поздаровался
                for word in users_hi_msg:
                    if word in msg:
                        send_some_msg(current_id, random.choice(list_hi_msg))
                        flag_for_unknown_messages = 1
                        break
                # если пользователь спросил как дела
                if "как дела" in msg:
                    send_some_msg(current_id, "Супер!")
                    flag_for_unknown_messages = 1
                # неизвестное сообщение
                if flag_for_unknown_messages == 0:
                    send_some_msg(current_id, random.choice(list_unknown_msg))

            # предлагаем пользователю сыграть в города
            if not flag_play_capital.x and not flag_question_play.x:
                uses = []
                keyboard = VkKeyboard()
                keyboard.get_empty_keyboard()
                keyboard.add_button("Играть в города", VkKeyboardColor.PRIMARY)
                send_some_msg(current_id, "Хотите поиграть в города?", keyboard)
                flag_question_play.x = True
                cities = []
                with open("cities.txt") as f:
                    for line in f.readlines():
                        cities.append(line.lower().replace('\n', ''))
