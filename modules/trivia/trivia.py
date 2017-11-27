from app.mac import mac, signals
from modules.trivia import helper
import requests
import texttable
import re

BASE_IP = '192.168.43.22'

@signals.command_received.connect
def handle(message):
    if message.command == "create":
        create_group(message)
    elif message.command == "register":
        register_user(message)
    elif message.command == "stake":
        create_stake(message)
    elif message.command == "help":
        help(message)
    elif message.command == "set":
        set_group(message)
    elif message.command == "start":
        start_game(message)
    elif message.command == "end":
        end_game(message)
    elif message.command == "check":
        check_stake(message)
    else:
        if message.command:
            help(message, True)


"""
Trivia Games Bot 
"""

"""
Long Messages
"""

HELP_MESSAGE = u'''
ℹ️ private command:
type #create [group_name] to create a group (only if you are registered as host)
ℹ️ host command:
type #start to start the game session
ℹ️ group command:
type #register to register you self to a game in this group
type #stake [animal] [ammount] to stake
'''

HELP_MESSAGE_ROOM = u'''
Hey, welcome to the room, I am your guide.
To be able to play along, you should register yourself with #register.

ℹ️ and here's some other commands I understand
📩 type #register to register yourself to a game in this group
💰 type #stake [animal] [ammount] to stake

Have fun!
'''

GROUP_CREATED = '''
Please set the detail of your game by sending this command below : 
#set (space) (initial balance for player) (space) (return to player in percentage) 
for example :
#set 1000 80
above command means that when a player register, each player will get 1000 upon registration and your game is set to 80% return to the player, 
and you will get minimum 20% of commission when you finish the game. 
'''

GROUP_FINISH_SETTING = '''
I finish setting up your game,
You can ask me to start your game at any time by using #start command
'''

GAME_STARTED = u'''
🏁 Ok we can start the game. 🏁
💰 Player can place a stake by using #stake [animal] [ammount]
🎉 You can invite your friends to the group now.
ℹ️ type help anytime and I'll inform about game commands
'''

"""
Main Function
"""

def create_group(message):
    params = message.predicate
    print(params)
    if len(params) == 0:
        ambigous("You need to initiate group name", message)
        return
    if len(params) > 24:
        ambigous("Group Name maximal character is 24. Yours is {}".format(len(params)), message)
        return
    group_name = params
    user_number = message.who.split("@")[0]
    group_id = '{}_{}'.format(user_number, group_name)
    payload = { "wa_group_name": group_name, "wa_ph_number": user_number }
    group_check_post = requests.post('http://{}/trivia/api/whatsappbot/create_group'.format(BASE_IP), data=payload )
    group_check_data = group_check_post.json()
    is_successful = helper.isResponseSuccess(group_check_post.status_code)
    if not is_successful:
        mac.send_message('Sorry you are failed to create group. the error is: \n', message.conversation)
        mac.send_message(group_check_data['message'], message.conversation)
        return

    mac.create_group(user_number, group_name, message.conversation, callback=update_group)


def update_group(groupId, group_name, user_number, conversation):
    payload = {'wa_group_id': groupId, 'wa_group_name': group_name, 'wa_ph_number': user_number}
    group_update_post = requests.post('http://{}/trivia/api/whatsappbot/update_group'.format(BASE_IP), data=payload)
    group_check_data = group_update_post.json()
    mac.send_message("Hi, I am Trivibot, I'll guide your game", conversation)
    mac.send_message("Your Group {} has succesfully created.".format(group_name), conversation)
    mac.send_message(GROUP_CREATED, conversation)
    mac.send_message("Type #help if you ever need any help", conversation)
    print(group_check_data["message"])

def register_user(message):
    user_number = message.who.split("@")[0]
    group_id = message.conversation.split("@")[0]
    if (not user_number or not group_id):
        message.send_message("Error when registering user", message.conversation)
        return
    payload = {'wa_group_id': group_id, 'wa_ph_number': user_number}
    register_post = requests.post('http://{}/trivia/api/whatsappbot/register_group'.format(BASE_IP), data=payload)
    register_data =register_post.json()
    is_successful = helper.isResponseSuccess(register_post.status_code)
    if not register_data:
        mac.send_message('Sorry I Failed connecting to server', message.conversation)
        return
    if not is_successful:
        mac.send_message('Sorry Failed to register You to server, your error is \n ', message.conversation)
        mac.send_message(register_data['message'], message.conversation)
        print(register_post.text)
        return
    mac.send_message("Great !", message.conversation)
    mac.send_message(register_data['message'], message.conversation)
    print(register_post.text)

def create_stake(message):
    params = message.predicate.split(" ")

    if message.conversation == message.who:
        mac.send_message("You can't place a stake from here, please place a stake from the group", message.who)
        return
    if len(params) < 2:
        mac.send_message("Too few arguments ! you should specify animal type and the value", message.conversation)
        return
    if len(params) > 2:
        mac.send_message("I can't understand your stake, seems it contain too much arguments !", message.conversation)
        return
    user_phone = message.who.split("@")[0]
    group_id = message.conversation.split("@")[0]
    stake = params[0]
    value = params[1]


    if not helper.isAllNumber(value):
        mac.send_message('Sorry I cannot understand the currency yet please just use plain number for value', message.conversation)
        return

    payload = {'wa_group_id': group_id, 'wa_ph_number': user_phone, 'stake': stake, 'value': value}
    stake_post = requests.post('http://{}/trivia/api/whatsappbot/stakes'.format(BASE_IP), data=payload)
    stake_post_data = stake_post.json()
    is_successful = helper.isResponseSuccess(stake_post.status_code)
    if not stake_post_data or not stake_post_data['message']:
        mac.send_message('ERROR connecting to server', message.conversation)
        return
    if not is_successful:
        mac.send_message(stake_post_data['message'], message.who)
        return
    mac.send_message("💰 {} place a stake!".format(message.who_name), message.conversation)
    mac.send_message("{} your stake is {}".format(stake_post_data['message'], message.predicate), message.who)

def set_group(message):
    params = message.predicate.split(" ")
    is_in_group = helper.conversationIsGroup(message)
    if not is_in_group:
        mac.send_message("Hello, I can't set your from here, please do it from your group.", message.conversation)
        return
    if len(params) < 2:
        mac.send_message("Please specify the default balance and the rtp ammount for your players", message.conversation)
        mac.send_message("You can ask for my #help if you are not sure", message.conversation)
        return
    if len(params) > 2:
        mac.send_message("Please check your command again, it seems it contain too much arguments", message.conversation)
        mac.send_message("You can ask for my #help if you are not sure how to setup", message.conversation)
        return
    for param in params:
        is_number_only = helper.isAllNumber(param)
        if not is_number_only:
            mac.send_message("Hey, I can't really understand your command. Please only use number for balance and rtp"
                             , message.conversation)
            return

    mac.send_message("Setting the group..", message.conversation)
    group_id= message.conversation.split("@")[0]
    (balance, rtp) = params
    payload = {'wa_group_id': group_id, 'init_point': balance, 'rtp': rtp}
    set_group_post = requests.post('http://{}/trivia/api/whatsappbot/update_point'.format(BASE_IP), data=payload)
    set_group_data =set_group_post.json()
    if not set_group_data or not set_group_data['message']:
        mac.send_message("I Failed to setup the group, no message field", message.conversation)
        return
    if not helper.isResponseSuccess(set_group_post.status_code):
        mac.send_message('I failed to setup the group, here is the message \n {}'
                         .format(set_group_data['message']), message.conversation)
        return
    mac.send_message(GROUP_FINISH_SETTING, message.conversation)

def check_stake(message):
    is_in_group = helper.conversationIsGroup(message)
    if not is_in_group:
        mac.send_message("Hello, I can't set your from here, please do it from your group.", message.conversation)
        return
    mac.send_message(u"📡 Wait, contacting the server guy to see current results", message.conversation)


def start_game(message):
    mac.send_message(u"📡 Ok, let's play ! But first, wait me to contact the server guy", message.conversation)
    group_id = message.conversation.split("@")[0]
    payload = {'wa_group_id': group_id}
    start_game_post = requests.post("http://{}/trivia/api/whatsappbot/start_game".format(BASE_IP), data=payload)
    start_game_data =start_game_post.json()
    if not start_game_data or not start_game_data['message']:
        mac.send_message("I failed to start the game session, no message field", message.conversation)
        return
    if not helper.isResponseSuccess(start_game_post.status_code):
        mac.send_message('I failed to start the game, here some error \n {}'
                         .format(start_game_data['message']), message.conversation)
        return
    mac.send_message(GAME_STARTED, message.conversation)

def end_game(message):
    group_id = message.conversation.split("@")[0]
    user_number = message.who.split("@")[0]
    payload = {'wa_group_id': group_id, 'wa_ph_number': user_number}
    end_game_post = requests.post("http://{}/trivia/api/whatsappbot/end_game".format(BASE_IP), data=payload)
    end_game_data = end_game_post.json()
    if not end_game_data or not end_game_data['message']:
        mac.send_message("I failed to end the game session, no message field", message.conversation)
        return
    if not helper.isResponseSuccess(end_game_post.status_code):
        mac.send_message('I failed to end the game, here what the server guy say: \n {}'
                         .format(end_game_data['message']), message.conversation)
        print(end_game_post.text)
        return
    winner_lists = end_game_data["winner_list"]
    if len(winner_lists) == 0:
        mac.send_message("There isn't any winner in this game", message.conversation)
    winner_rows= [["phone_number", "stakes", "profit"]]
    for winner in winner_lists:
        winner_rows.append([winner["phone_number"], winner["stake"], winner["profit"]])
    table = texttable.Texttable()
    table.add_rows(winner_rows)
    print("winner")
    print(table.draw())
    mac.send_message(u'🏁 We have reach the end of the game 🏁 \n '
                     u'🥁🥁🥁 Now I\'ll announce the winners! 🥁🥁🥁', message.conversation)
    mac.send_message(table.draw(), message.conversation)


"""
Helper and other command
"""

def check_group(message, callback=None):
    """
    #TODO [UNUSED]
    Check whether the user are the admin of the group
    it needed for some command that can only be call by admin
    :param message:
    :param callback:
    :return:
    """
    is_in_group = helper.conversationIsGroup(message)
    if not is_in_group:
        mac.send_message("Hello, I can't do it from here, please do it from your group.", message.conversation)
        return
    def callback_check_group(isAdmin):
        if not callback:
            return
        callback(isAdmin)
    mac.get_group_info(message.conversation, message.who, callback=callback_check_group())

def ambigous(text, message):
    ambigous_text = 'Your message seem ambigous. here is your error: \n {}'.format(text)
    mac.send_message(ambigous_text, message.conversation)


def help(message, isLost=False):
    def callback_check_group(isAdmin):
        if isAdmin:
            mac.send_message("Feeling lost ? Here is some command I understand", message.conversation)
            mac.send_message(HELP_MESSAGE_ROOM, message.conversation)
        else:
            mac.send_message("Here is some commaind I understand", message.who)
            mac.send_message(HELP_MESSAGE, message.who)
    if isLost:
        mac.send_message("Hi, {} seems you getting lost".format(message.who_name), message.conversation)
    # check wether sender == conversation
    # if sender == conversation it means it's private chat
    if message.who == message.conversation:
        mac.send_message("Here is some command I understand", message.conversation)
        mac.send_message(HELP_MESSAGE, message.conversation )
    else:
        group_id = message.conversation.split("@")[0]
        print(message.conversation)
        mac.get_group_info(message.conversation, message.who, callback=callback_check_group)

