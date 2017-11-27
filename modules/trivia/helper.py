import  re
"""
HELPER FOR TRIVIA
"""

def isResponseSuccess(statusCode):
    """
    check if response is successful http response
    :param statusCode:
    :return:
    """
    if statusCode >= 200 and statusCode < 300:
        return True
    return False

def conversationIsGroup(message):
    """
    Check if conversation is group or personal
    if sender == conversation name it means it a private for user
    if sender != conversation it need to check
    :param conversation:
    :return boolean:
    """
    if message.conversation == message.who:
        return False
    return True

def isAllNumber(value):
    regex = re.compile("[0-9]")
    if not regex.match(value):
        return False
    return True
