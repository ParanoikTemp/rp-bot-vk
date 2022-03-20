from vk_api import VkApi
from vk_api.bot_longpoll import VkBotLongPoll
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.bot_longpoll import VkBotEventType
from vk_api.utils import get_random_id
import json
import random
from utils import *
import pymorphy2
from transliterate import translit

# очень много вкусных импортов

vk_session = VkApi(token=token)
longpoll = VkBotLongPoll(vk_session, group_id=group_id)
vk = vk_session.get_api()
vktype = VkBotEventType
morph = pymorphy2.MorphAnalyzer()
# инициализация базовых переменных

cutid = lambda x: int(x.split('|')[0][3:])  # вырезает id из тега
cutname = lambda x: x.split('|')[1][:-1]  # вырезает имя из тега


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


def main():
    with open('datas/peers.txt') as f:
        peers = list(map(lambda x: int(x.replace('\n', '')), f.readlines()))  # подгружаем список бесед

    peers_commands = dict()  # тут находятся команды по ключу беседы
    people_sex = dict()
    # эта штука чтобы по 100 раз пол не запрашивать. На самом деле проще позапрашивать, но раз есть то ок
    with open('datas/marry.json', 'r') as f:
        marrys_list = json.load(f)
    marrys_wait = dict()
    static_commands = ['!гайд', '!переменные', '!команды', '!свадьбы', '!развод', '!добавить']

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
            try:
                if sender not in people_sex.keys():
                    sex = vk.users.get(user_ids=(event.message['from_id']), fields=['sex'])[0]['sex']
                    people_sex[sender] = sex
            except Exception:
                pass
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
<sender> - отправитель (в формате тега)
<random_user> - выбирает случайного пользователя из беседы. НУЖНЫ ПРАВА АДМИНИСТРАТОРА!
<random_user_id> - выбирает случайного пользователя из беседы и дает его id! НУЖНЫ ПРАВА АДМИНИСТРАТОРА!
    
Также при вырезании слов им можно дать падеж.
Пример: <word_2_datv> - второе слово в дательном падеже
    
Список падежей:
nomn - именительный
gent - родительный
datv - дательный
accs - винительный
ablt - творительный
loct - предложный
voct - звательный
gen2 - второй родительный (Стакан ядУ) - вот это часто используется. Например при действии по типу "Ударить".
acc2 - второй винительный (записался в солдатЫ)
loc2 - второй предложный (висит в шкафу)
                    
Пример команды:
!добавить !крос @id<sender_id>(<sender_name>) очень красивый||красивая''', from_chat)
                if test_message == '!свадьбы':
                    send_message('''Чтобы сделать предложение введите: !сделать предложение <человек>
Чтобы отменить предложение введите: !отказаться от предложения <человек>
Чтобы принять предложение введите: !принять предложение <человек>
Чтобы развестить введите: !развод <человек>''', from_chat)
                if event.from_chat and str(from_chat) not in marrys_list.keys():
                    marrys_list[str(from_chat)] = {}
                if event.from_chat and from_chat not in marrys_wait.keys():
                    marrys_wait[from_chat] = {}
                if test_message.startswith('!сделать предложение') and len(test_message.split()) == 3:
                    partner_id = cutid(test_message.split()[2])
                    if sender not in marrys_wait[from_chat].keys() and sender not in marrys_wait[
                        from_chat].values() and partner_id != sender:
                        if str(sender) not in marrys_list[str(from_chat)]:
                            marrys_list[str(from_chat)][str(sender)] = list()
                        if str(partner_id) not in marrys_list[str(from_chat)]:
                            marrys_list[str(from_chat)][str(partner_id)] = list()
                        if str(sender) in marrys_list[str(from_chat)][str(partner_id)]:
                            send_message('Огорчу вас, но вы уже...', from_chat)
                        else:
                            marrys_wait[from_chat][sender] = partner_id
                            name1 = vk.users.get(user_ids=(sender), fields=['first_name'])[0]['first_name']
                            name2 = vk.users.get(user_ids=(partner_id), fields=['first_name_dat'])[0]['first_name_dat']
                            sex = vk.users.get(user_ids=(sender), fields=['sex'])[0]['sex']
                            keyboard = VkKeyboard(inline=True)
                            keyboard.add_button(f'!принять предложение @id{sender}', color=VkKeyboardColor.POSITIVE)
                            keyboard.add_button(f'!отказаться от предложения @id{sender}', color=VkKeyboardColor.NEGATIVE)
                            keyboard.add_line()
                            keyboard.add_button(f'!отменить предложение @id{partner_id}', color=VkKeyboardColor.PRIMARY)
                            if sex == 1:
                                send_message(
                                    f'@id{sender}({name1}) предлагает @id{partner_id}({name2}) взять ее в жены!\nЧтобы согласиться введите: "!принять предложение @id{sender} "\nЧтобы отказаться введите: "!отказаться от предложения @id{sender}"',
                                    from_chat, keyboard=keyboard)
                            else:
                                send_message(
                                    f'@id{sender}({name1}) предлагает @id{partner_id}({name2}) выйти за него замуж!\nЧтобы согласиться введите: "!принять предложение @id{sender} "\nЧтобы отказаться введите: "!отказаться от предложения @id{sender}"',
                                    from_chat, keyboard=keyboard)
                        continue
                    elif sender in marrys_wait[from_chat].values():
                        send_message('Этот человек уже сделал вам предложение.', from_chat)
                    elif partner_id == sender:
                        send_message('Своей руке можно и не делать предложение.', from_chat)
                    else:
                        send_message('Блин, ну куда ты спешишь емае...', from_chat)
                if test_message.startswith('!отменить предложение'):
                    if sender in marrys_wait[from_chat].keys():
                        del marrys_wait[from_chat][sender]
                        send_message('Вы отменили ваше предложение руки и сердца', from_chat)
                if test_message.startswith('!принять предложение') and len(test_message.split()) == 3:
                    partner_id = cutid(test_message.split()[2])
                    if marrys_wait[from_chat].get(partner_id) and marrys_wait[from_chat][partner_id] == sender:
                        del marrys_wait[from_chat][partner_id]
                        marrys_list[str(from_chat)][str(partner_id)].append(sender)
                        marrys_list[str(from_chat)][str(sender)].append(partner_id)
                        with open('datas/marry.json', 'w') as f:
                            json.dump(marrys_list, f)
                        name1 = vk.users.get(user_ids=(sender), fields=['first_name'])[0]['first_name']
                        name2 = vk.users.get(user_ids=(partner_id), fields=['first_name'])[0]['first_name']
                        send_message(f'В этот день @id{partner_id}({name2}) и @id{sender}({name1}) '
                                     f'заключили волшебный союз во имя Любви!\nПоздравим молодоженов!', from_chat)
                    else:
                        send_message('К сожалению, ты никому не нужен...', from_chat)
                if test_message.startswith('!отказаться от предложения') and len(test_message.split()) == 4:
                    partner_id = cutid(test_message.split()[3])
                    if marrys_wait[from_chat].get(partner_id) and marrys_wait[from_chat][partner_id] == sender:
                        del marrys_wait[from_chat][partner_id]
                        name1 = vk.users.get(user_ids=(sender), fields=['first_name'])[0]['first_name']
                        name2 = vk.users.get(user_ids=(partner_id), fields=['first_name'])[0]['first_name']
                        send_message(f'Извини @id{partner_id}({name2}), но @id{sender}({name1}) '
                                     f'отказался от твоего предложения.', from_chat)
                    else:
                        send_message('К сожалению, ты никому не нужен...', from_chat)
                if test_message.startswith('!развод') and len(test_message.split()) == 2:
                    partner_id = cutid(test_message.split()[1])
                    if marrys_list[str(from_chat)].get(str(sender)) and partner_id in marrys_list[str(from_chat)][str(sender)]:
                        marrys_list[str(from_chat)][str(sender)].remove(partner_id)
                        marrys_list[str(from_chat)][str(partner_id)].remove(sender)
                        with open('datas/marry.json', 'w') as f:
                            json.dump(marrys_list, f)
                        name1 = vk.users.get(user_ids=(sender), fields=['first_name'])[0]['first_name']
                        name2 = vk.users.get(user_ids=(partner_id), fields=['first_name'])[0]['first_name']
                        send_message(f'Печальные вести! @id{partner_id}({name2}) и @id{sender}({name1}) развелись! :C',
                                     from_chat)
                    else:
                        send_message('Вы не женаты на этом человеке', from_chat)
                if event.from_chat and test_message.startswith('!браки'):
                    if str(sender) in marrys_list[str(from_chat)] and marrys_list[str(from_chat)][str(sender)]:
                        message = f'@id{sender}(Ваши) партнеры:\n'
                        for i in marrys_list[str(from_chat)][str(sender)]:
                            name = vk.users.get(user_ids=(i), fields=['first_name'])[0]['first_name']
                            message += f'@id{i}({name})\n'
                        send_message(message, from_chat)
                    else:
                        send_message(f'Сорян но @id{sender}(ты) никому не нужен.', from_chat)
                if event.from_chat and test_message.startswith('!добавить') and len(
                        message) < 5001:  # а тут мы добавляем команды
                    message = message.replace('\n',
                                              '<br_>')
                    # так как я ленивая жопа, то вместо попыток сохранить символ тупо сделал свой
                    args = message.split()[1:]
                    command = args[0]
                    answer = args[1:]  # нарезочка
                    with open('peers_commands/' + str(from_chat) + '.json') as f:
                        cmds = json.load(f)
                        if command in cmds.keys() or command in static_commands:
                            send_message('Упс! Такая команда уже есть!', from_chat)
                            continue
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
                    text = ' '.join(answer)

                    att = []
                    keyboard = None
                    users = list()
                    name = ''
                    last_name = ''
                    if '<random_user' in text:
                        users = vk.messages.getConversationMembers(peer_id=from_chat)
                    if '<sender_name>' in text or '<sender>' in text:
                        name = vk.users.get(user_ids=(event.message['from_id']), fields=['first_name'])[0][
                            'first_name']
                    if '<sender_last_name>' in text:
                        last_name = vk.users.get(user_ids=(event.message['from_id']), fields=['first_name'])[0][
                            'last_name']
                    if '<button_' in text:
                        keyboard = VkKeyboard(inline=True)
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
                                word = random.choice(words)
                        # тупо переменные
                        if '<sender_id>' in word:
                            answer[i] = answer[i].replace('<sender_id>', str(sender))
                        if '<sender_name>' in word:
                            answer[i] = answer[i].replace('<sender_name>', name)
                        if '<sender_last_name>' in word:
                            answer[i] = answer[i].replace('<sender_last_name>', last_name)
                        if '<text_message>' in word:
                            answer[i] = answer[i].replace('<text_message>',
                                                          message.replace(message.split()[0] + ' ', ''))
                        if '<sender>' in word:
                            answer[i] = answer[i].replace('<sender>', f'@id{sender}({name})')
                        while '<random_user>' in word:
                            user = random.choice(users['profiles'])
                            users['profiles'].remove(user)
                            answer[i] = answer[i].replace('<random_user>', f'@id{user["id"]}({user["first_name"]})', 1)
                            word = word.replace('<random_user>', f'@id{user["id"]}({user["first_name"]})', 1)
                        if '<random_user_id>' in word:
                            user = random.choice(users['profiles'])
                            users['profiles'].remove(user)
                            answer[i] = answer[i].replace('<random_user>', str(user['id']))
                        tot = 0
                        while '<att_' in word:
                            tot += 1
                            if tot > 10:
                                break
                            photo_id = word.split('<att_')[1].split('>')[0]
                            att.append(photo_id)
                            word = word.replace(f'<att_{photo_id}>', '')
                            answer[i] = word
                        tot = 0
                        while '<word_' in word:
                            tot += 1
                            if tot > 10:
                                break
                            # а это в каком то плане "аргументы"
                            num = word.split('<word_')[1].split('>')[0]
                            try:
                                if len(num.split('_')) == 2:
                                    spr = num.split('_')[1]
                                    num = num.split('_')[0]
                                    new_word = message.split()[int(num)]
                                    if new_word[:3] == '[id' and new_word[-1] == ']' and new_word.count('|') == 1:
                                        nname = cutname(new_word)
                                        nname = translit(nname, 'ru')
                                        nname = nname.replace('x', 'кс')
                                        iid = cutid(new_word)
                                        aboba = morph.parse(nname)[0]
                                        x = aboba.inflect({spr})
                                        word = answer[i].replace(f'<word_{num}_{spr}>', f'@id{iid}({x.word.capitalize()})')
                                        answer[i] = answer[i].replace(f'<word_{num}_{spr}>',
                                                                      f'@id{iid}({x.word.capitalize()})')
                                    else:
                                        aboba = morph.parse(translit(new_word, 'ru'))[0]
                                        x = aboba.inflect({spr})
                                        word = answer[i].replace(f'<word_{num}_{spr}>', x.word)
                                        answer[i] = answer[i].replace(f'<word_{num}_{spr}>', x.word)
                                else:
                                    word = answer[i].replace(f'<word_{num}>', message.split()[int(num)])
                                    answer[i] = answer[i].replace(f'<word_{num}>', message.split()[int(num)])
                            except Exception:
                                word = answer[i].replace(f'<word_{num}>', '')
                            answer[i] = answer[i].replace(f'<word_{num}>', '')
                    else:
                        answer = ' '.join(answer)

                        # тут обрабатываются мои "спецсимволы"
                        answer = answer.replace('<br_>', '\n').replace('<+>', ' ').replace(' <-> ', '').replace('<-> ',
                                                                                                                '').replace(
                            ' <->', '')
                        # Работа с клавиатурой
                        tot = 0
                        while '<button_' in answer:
                            tot += 1
                            if tot > 20:
                                break
                            if answer.find('<button_') < answer.find('<add_line>') or answer.find('<add_line>') == -1:
                                if answer.find('<button_') == answer.find('<button_link_'):
                                    text, *link = answer.split('<button_link_')[1].split('>')[0].split('_')
                                    link = '_'.join(link)
                                    keyboard.add_openlink_button(text, link)
                                    answer = answer.replace(f'<button_link_{text}_{link}>', '')
                                else:
                                    text, color = answer.split('<button_')[1].split('>')[0].split('_')
                                    if color == 'positive':
                                        keyboard.add_button(text, VkKeyboardColor.POSITIVE)
                                    elif color == 'primary':
                                        keyboard.add_button(text, VkKeyboardColor.PRIMARY)
                                    elif color == 'negative':
                                        keyboard.add_button(text, VkKeyboardColor.NEGATIVE)
                                    elif color == 'secondary':
                                        keyboard.add_button(text, VkKeyboardColor.SECONDARY)
                                    answer = answer.replace(f'<button_{text}_{color}>', '')
                            elif answer.find('<add_line>'):
                                keyboard.add_line()
                                answer = answer.replace(f'<add_line>', '', 1)
                        if answer or att or keyboard:
                            send_message(answer, from_chat, keyboard=keyboard, attachment=att)
                        else:
                            continue
            except Exception as err:
                print(err, test_message)


while True:
    try:
        main()
    except Exception:
        pass