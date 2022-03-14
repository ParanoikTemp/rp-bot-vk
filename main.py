from vk_api import VkApi
from vk_api.bot_longpoll import VkBotLongPoll
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.bot_longpoll import VkBotEventType
from vk_api.utils import get_random_id
import json
import random
from utils import *

# очень много вкусных импортов

vk_session = VkApi(token=token)
longpoll = VkBotLongPoll(vk_session, group_id=group_id)
vk = vk_session.get_api()
vktype = VkBotEventType
# инициализация базовых переменных

cutid = lambda x: int(x.split('|')[0][3:])  # вырезает id из тега


def send_message(messag, sender, keyboard=None, attachment=None):  # оптимальная функция для отправки сообщений
    global vk
    try:
        keyboard = keyboard.get_keyboard() if keyboard else None
        answer = vk.messages.send(message=messag, random_id=get_random_id(), peer_ids=(int(sender)),
                                  attachment=attachment, keyboard=keyboard)
        return answer
    except Exception:
        vk = vk_session.get_api()
        send_message(messag, sender, keyboard=keyboard, attachment=attachment)


def edit_message(message_id, messag, sender, keyboard=None, attachment=None):  # функция для редактирования сообщений
    global vk
    try:
        keyboard = keyboard.get_keyboard() if keyboard else None
        vk.messages.edit(message=messag, random_id=get_random_id(), peer_id=int(sender),
                         keyboard=keyboard, message_id=message_id, attachment=attachment)
    except Exception:
        vk = vk_session.get_api()
        edit_message(message_id, messag, sender, keyboard)


with open('datas/peers.txt') as f:
    peers = list(map(lambda x: int(x.replace('\n', '')), f.readlines()))  # подгружаем список бесед

peers_commands = {}  # тут находятся команды по ключу беседы
people_sex = {}  # эта штука чтобы по 100 раз пол не запрашивать. На самом деле проще позапрашивать, но раз есть то ок

print('Бот запущен!')
for event in longpoll.listen():
    if event.type == VkBotEventType.MESSAGE_NEW and (event.from_user or event.from_chat) and event.message['text'] and \
            event.message['from_id'] > 0:  # если это входящее, где угодно, с текстов и не от группы то реагируем
        message = event.message['text']
        test_message = event.message['text'].lower()
        if test_message.startswith('[club211218245|@bot_rp_vk] '):
            test_message = test_message.replace('[club211218245|@bot_rp_vk] ', '', 1)
        sender = event.message['from_id']
        from_chat = event.message['peer_id']
        # делаем вспомогательные переменные
        if sender not in people_sex.keys():
            sex = vk.users.get(user_ids=(event.message['from_id']), fields=['sex'])[0]['sex']
            people_sex[sender] = sex
        # вноска людей в словарик полов
        if event.from_chat and from_chat not in peers:  # если беседы нет то она вносится в список
            peers.append(from_chat)
            with open('datas/peers.txt', 'w') as f:
                for i in peers:
                    f.write(str(i) + '\n')
            with open('peers_commands/' + str(from_chat) + '.json', 'w') as f:
                f.write('{}')
        try:
            if test_message == '!команды':  # выводит все команды которые есть в данной беседе
                if from_chat not in peers_commands.keys():
                    with open('peers_commands/' + str(from_chat) + '.json') as f:
                        cmds = json.load(f)
                        peers_commands[from_chat] = cmds
                cmds = peers_commands[from_chat]
                message_new = 'Команды:\n'
                for k in cmds.keys():
                    message_new += k + '\n'
                send_message(message_new, from_chat)
            if test_message == '!гайд':  # гайд для людей чтобы они могли делать свои команды
                send_message('''Чтобы добавить команду нужно ввести:
!добавить <название команды> <сама команда>
Например: !добавить !привет Здравствуй дружище!
На команду "!привет" бот отреагирует словами "Здравствуй дружище"

Некоторые тексты зависят от пола человека. В таком случае каждое слово надо писать через ||
Например: !добавить !выстрел Ты выстрелил||выстрелила в воздух
Если команду пропишет парень, то сообщение будет таким: "Ты выстрелил в воздух"
Если напишет девушка, то будет: "Ты выстрелила в воздух

Также можно добавить немного случайности. Если поставить без пробела слова через &&, то выберется
случайное:
Пример: !добавить !рандом орел&&решка&&ребро
Если же тут будет указано два числа, то выберется случайное в диапазоне между ними.

Также можно вставлять переменные в сообщения:
Например: !добавить !папуг <text_message>
Данная команда будет повторять то что вы написали.

Также стоит знать что если вы пересылаете чье то сообщение, то этот человек автоматически подставляется в команду.

Для того чтобы просмотреть полный список переменных, введите "!переменные"''', from_chat)
            if test_message == '!переменные':  # тоже гайд
                send_message('''<text_message> - сообщение которое отправил пользователь
<sender_id> - id пользователя, только в цифрах
<sender_name> - имя пользователя, без фамилии.
<br_> - это наш спецсимвол для переноса текста на следующую строку. Он нужен тупо для корректной работы.
<+> - это наш спецсимвол для пробела. В случае если у вас идет выбор между предложениями, то их нельзя делить обычными пробелами. Так что используйте специальные.
<-> - этот спецсимвол наоборот убирает следующий пробел. Нужно если вам надо слитный текст.
<sender_last_name> - фамилия пользователя.
<word_номер> - любое слово из сообщение.
                
Пример команды:
!добавить !крос @id<sender_id>(<sender_name>) очень красивый||красивая''', from_chat)

        except Exception:
            pass
        if event.from_chat and test_message.startswith('!добавить') and len(
                message) < 201:  # а тут мы добавляем команды
            message = message.replace('\n',
                                      '<br_>')
            # так как я ленивая жопа, то вместо попыток сохранить символ тупо сделал свой
            args = message.split()[1:]
            command = args[0]
            answer = args[1:]  # нарезочка
            with open('peers_commands/' + str(from_chat) + '.json') as f:
                cmds = json.load(f)
                cmds[command] = answer
                peers_commands[from_chat] = cmds
            with open('peers_commands/' + str(from_chat) + '.json', 'w') as f:
                json.dump(cmds, f)  # вносим команду: слово которое реагирует и ответ разделенный на пробелы.
                # все это хранится в json файлах в папке peers_commands
            send_message('Ваша команда успешно добавлена!', from_chat)
        if event.from_chat and test_message.startswith('!удалить'):  # если кто то накосячил можно и удалить команду
            args = message.split()[1:]
            command = args[0]
            try:
                with open('peers_commands/' + str(from_chat) + '.json') as f:
                    cmds = json.load(f)
                    del cmds[command]
                    peers_commands[from_chat] = cmds
                with open('peers_commands/' + str(from_chat) + '.json', 'w') as f:
                    json.dump(cmds, f)
                send_message('Ваша команда успешно удалена!', from_chat)
            except Exception:
                send_message('Упс... Ошибочка вышла...', from_chat)
        if event.from_chat:
            if from_chat not in peers_commands.keys():  # подгружаем команды для этой беседы
                with open('peers_commands/' + str(from_chat) + '.json') as f:
                    cmds = json.load(f)
                    peers_commands[from_chat] = cmds
            else:
                cmds = peers_commands[from_chat]
            if cmds.get(message.split()[0]):
                if event.message.get('reply_message'):
                    # если это пересланое сообщение то автоматически подставляем автора
                    name = vk.users.get(user_ids=(event.message.get('reply_message')['from_id']),
                                        fields=['first_name'])[0]['first_name']
                    message += ' @id' + str(event.message.get('reply_message')['from_id']) + '(' + \
                               name + ')'
                answer = cmds[message.split()[0]].copy()
                for i, word in enumerate(answer):
                    # чередование слов в зависимости от пола
                    if '||' in word:
                        if people_sex[sender] == 1:
                            answer[i] = word.split('||')[1]
                        elif people_sex[sender] == 0 or people_sex[sender] == 2:
                            answer[i] = word.split('||')[0]
                    if '&&' in word:
                        # пресвятой рандом
                        words = word.split('&&')
                        if len(words) == 2 and words[0].isdigit() and words[1].isdigit():
                            answer[i] = str(random.randint(int(words[0]), int(words[1])))
                        else:
                            answer[i] = random.choice(words)
                    # тупо переменные
                    if '<sender_id>' in word:
                        answer[i] = answer[i].replace('<sender_id>', str(sender))
                    if '<sender_name>' in word:
                        name = vk.users.get(user_ids=(event.message['from_id']), fields=['first_name'])[0]['first_name']
                        answer[i] = answer[i].replace('<sender_name>', name)
                    if '<sender_last_name>' in word:
                        name = vk.users.get(user_ids=(event.message['from_id']), fields=['first_name'])[0]['last_name']
                        answer[i] = answer[i].replace('<sender_last_name>', name)
                    if '<text_message>' in word:
                        answer[i] = answer[i].replace('<text_message>', message.replace(message.split()[0] + ' ', ''))
                    while '<word_' in word:
                        # а это в каком то плане "аргументы"
                        num = int(word.split('<word_')[1].split('>')[0])
                        try:
                            word = answer[i].replace(f'<word_{num}>', message.split()[num])
                            answer[i] = answer[i].replace(f'<word_{num}>', message.split()[num])
                        except Exception:
                            word = answer[i].replace(f'<word_{num}>', '')
                            answer[i] = answer[i].replace(f'<word_{num}>', '')
                else:
                    answer = ' '.join(answer)
                    # тут обрабатываются мои "спецсимволы"
                    answer = answer.replace('<br_>', '\n').replace('<+>', ' ').replace(' <-> ', '').replace('<-> ',
                                                                                                            '').replace(
                        ' <->', '')
                    if answer:
                        send_message(answer, from_chat)
                    else:
                        continue
