TOKEN = "953155266:AAF-g0tEk7qMCZwDxheNHQZD3oGMXn5w3G0"

# TODO:
    # 1) don't let /begin work multiple times
    # 1) solve issue with empty entries, use original word instead
    # 2) solve issue with multiple ins
    # 3) solve issue with no past words

# 1) Fixed issue with /begin working multiple times
# 2) Fixed issue where original words could be re-used
# 3) Fixed issue where multiple /in commands would screw things update
# 4) Fixed issue where empty or multi-word entries were allowed
# 5) Added an "/out" command to allow for temporarily leaving the game
# 6) Modified "/help" command to print more useful information
# 7) Added reminder for new players to add the bot at @medium_boardgame_bot
# 8) Game now stops when enough players have left
# 9) No longer need /enter command

import telegram
from telegram.ext import Updater, MessageHandler, CommandHandler, Filters
# import requests
from word_lib import getWords
import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def kick_idle(update, context):

    if (update.message.chat_id > 0):
        context.bot.send_message(chat_id=update.message.chat_id, text="This command can only be sent in a group channel!", parse_mode=telegram.ParseMode.HTML)
        return

    if ("gameStarted" not in context.chat_data):
        context.bot.send_message(chat_id=update.message.chat_id, text="Type /new to create a new game!", parse_mode=telegram.ParseMode.HTML)
        return

    if (context.chat_data["gameStarted"]):
        chat_id = update.message.chat_id

        context.bot.send_message(chat_id=update.message.chat_id, text="Kicking the following idle players...", parse_mode=telegram.ParseMode.HTML)
        for player in context.chat_data["playersArray"]:
            if (player["inGame"] == True) and (player["entry"] == None):
                print ("-------------------------------------------------")
                print (player)
                print ("-------------------------------------------------")
                kickPlayer(player["id"], update, context, True)
    else:
        context.bot.send_message(chat_id=update.message.chat_id, text="Type /begin to begin the game first!", parse_mode=telegram.ParseMode.HTML)


def kickPlayer(userId, update, context, forced):
    chat_data = context.chat_data

    player = chat_data["playersDict"][userId]
    player["inGame"] = False
    player["entry"] = None
    if (not forced):
        context.bot.send_message(chat_id=update.message.chat_id, text="Psychic <b>%s</b> has left the game!" % player["name"], parse_mode=telegram.ParseMode.HTML)
    else:
        context.bot.send_message(chat_id=update.message.chat_id, text="Psychic <b>%s</b> has been booted from the game!" % player["name"], parse_mode=telegram.ParseMode.HTML)

    # Stop game if < 2 players
    numPlayersStillInGame = 0
    for player in chat_data["playersArray"]:
        if (player["inGame"] == True):
            numPlayersStillInGame += 1

    if numPlayersStillInGame < 2:
        context.bot.send_message(chat_id=update.message.chat_id, text="Not enough players to continue the game! Stopping game...", parse_mode=telegram.ParseMode.HTML)
        stop(update, context)

def deregister_user(update, context):

    if (update.message.chat_id > 0):
        context.bot.send_message(chat_id=update.message.chat_id, text="This command can only be sent in a group channel!", parse_mode=telegram.ParseMode.HTML)
        return

    if ("gameStarted" not in context.chat_data):
        context.bot.send_message(chat_id=update.message.chat_id, text="Type /new to create a new game!", parse_mode=telegram.ParseMode.HTML)
        return

    userId = update.message.from_user.id
    kickPlayer(userId, update, context, False)

def register_user(update, context):

    if (update.message.chat_id > 0):
        context.bot.send_message(chat_id=update.message.chat_id, text="This command can only be sent in a group channel!", parse_mode=telegram.ParseMode.HTML)
        return

    if ("gameStarted" not in context.chat_data):
        context.bot.send_message(chat_id=update.message.chat_id, text="Type /new to create a new game!", parse_mode=telegram.ParseMode.HTML)
        return

    userId = update.message.from_user.id
    name = update.message.from_user.first_name

    context.user_data["chat_data"] = context.chat_data
    context.user_data["chat_id"] = update.message.chat_id
    context.user_data["chat_bot"] = context.bot

    if userId not in context.chat_data["playersDict"]:
        player = {"id":userId, "name":name, "entry":None, "points": 0, "inGame": True}

        # TEMP
        if name == "Wee Loong":
            player["points"] = -9999999999999
            player["name"] = "To Wee Or Not To Wee That Is The Question"

        context.chat_data["playersArray"].append(player)
        context.chat_data["playersDict"][userId] = player

        context.bot.send_message(chat_id=update.message.chat_id, text="Psychic <b>%s</b> has joined the game!" % player["name"], parse_mode=telegram.ParseMode.HTML)

        # Player has joined midway, send them the message
        if (context.chat_data["gameStarted"]):
            sendWordRequest(player, context.chat_data, context.bot)
    else:
        player = context.chat_data["playersDict"][userId]
        if (player["inGame"] == True):
            context.bot.send_message(chat_id=update.message.chat_id, text="Psychic <b>%s</b> is already in the game!" % player["name"], parse_mode=telegram.ParseMode.HTML)
        else:
            player["inGame"] = True
            player["entry"] = None
            context.bot.send_message(chat_id=update.message.chat_id, text="Psychic <b>%s</b> has re-joined the game!" % player["name"], parse_mode=telegram.ParseMode.HTML)
            sendWordRequest(player, context.chat_data, context.bot)

    # else:
    #     context.bot.send_message(chat_id=update.message.chat_id, text="Game has not yet started!", parse_mode=telegram.ParseMode.HTML)

def players_left(update, context):

    if (update.message.chat_id > 0):
        context.bot.send_message(chat_id=update.message.chat_id, text="This command can only be sent in a group channel!", parse_mode=telegram.ParseMode.HTML)
        return

    if ("gameStarted" not in context.chat_data):
        context.bot.send_message(chat_id=update.message.chat_id, text="Type /new to create a new game!", parse_mode=telegram.ParseMode.HTML)
        return

    if (len(context.chat_data["playersArray"]) < 2):
        context.bot.send_message(chat_id=update.message.chat_id, text="Waiting for game to begin!", parse_mode=telegram.ParseMode.HTML)
    else:
        leftText = "Still waiting for: "
        for player in context.chat_data["playersArray"]:
            if player["inGame"] and (player["entry"] == None):
                leftText += "<b>%s</b>, " % player["name"]
        leftText = leftText[0:-2]
        context.bot.send_message(chat_id=update.message.chat_id, text=leftText, parse_mode=telegram.ParseMode.HTML)

POINTS_ARRAY = [10,5,2]
NON_MAIN_POINTS = 1 # points the non main players get for matching with main players
NUM_ROUNDS = len(POINTS_ARRAY)

def points(update, context):

    if (update.message.chat_id > 0):
        context.bot.send_message(chat_id=update.message.chat_id, text="This command can only be sent in a group channel!", parse_mode=telegram.ParseMode.HTML)
        return

    if ("gameStarted" not in context.chat_data):
        context.bot.send_message(chat_id=update.message.chat_id, text="Type /new to create a new game!", parse_mode=telegram.ParseMode.HTML)
        return

    printScore(context.chat_data, update.message.chat_id, context.bot)

def printScore(chat_data, chat_id, chat_bot):
    # print points
    pointsText = "<b>Current points:</b>\n"
    for player in chat_data["playersArray"]:
        if player["inGame"]:
            pointsText += "<b>%s</b>: %d points\n" % (player["name"], player["points"])
        else:
            pointsText += "<b>%s</b> [out]: %d points\n" % (player["name"], player["points"])

    chat_bot.send_message(chat_id=chat_id, text=pointsText, parse_mode=telegram.ParseMode.HTML)

def sendWordRequest(player, chat_data, chat_bot):
    player["entry"] == None

    chat_bot.send_message(chat_id=player["id"], text="Current words are <b>%s</b> and <b>%s</b>!" % chat_data["words"], parse_mode=telegram.ParseMode.HTML)
    chat_bot.send_message(chat_id=player["id"], text="When you are ready, enter your Medium Word (just one) here!", parse_mode=telegram.ParseMode.HTML)

def sendWordRequestToAll(chat_data, chat_id, chat_bot):
    for player in chat_data["playersArray"]:
        sendWordRequest(player, chat_data, chat_bot)

def handleNewRound(chat_data, chat_id, chat_bot):

    if (chat_data["subRound"] == 0):
        (wordA, wordB) = getWords()

        chat_data["words"] = (wordA, wordB)
        chat_data["seenWords"] = [wordA.lower(), wordB.lower()]

    currentRound = chat_data["currentRound"]
    currentSubRound = chat_data["subRound"]

    if (currentRound > 0):
        printScore(chat_data, chat_id, chat_bot)

    # player1Index = currentRound % numPlayers
    # player2Index = (currentRound+1) % numPlayers
    # chat_data["nextPlayer1Index"] = player2Index;

    numPlayers = len(chat_data["playersArray"])
    potentialPlayer1Index = chat_data["nextPlayer1Index"]
    # Initialize main player to false first
    for player in chat_data["playersArray"]:
        player["isMainPlayer"] = False

    mainPlayers = []
    currentIndex = chat_data["nextPlayer1Index"]
    while len(mainPlayers) < 2:
        potentialPlayer = chat_data["playersArray"][currentIndex]
        if potentialPlayer["inGame"]:
            potentialPlayer["isMainPlayer"] = True
            mainPlayers.append(potentialPlayer)
        chat_data["nextPlayer1Index"] = currentIndex # Index of latest player
        currentIndex  = (currentIndex + 1) % numPlayers

    chat_data["player1"] = mainPlayers[0]
    chat_data["player2"] = mainPlayers[1]

    startText = "<b>Round %d - Attempt %d</b>\n" % (currentRound+1, currentSubRound+1)
    startText += "Main players: %s and %s\n" % (chat_data["player1"]["name"], chat_data["player2"]["name"])

    startText += "Let's get psychic! The two words are: <b>%s</b> and <b>%s</b>" % chat_data["words"]
    chat_bot.send_message(chat_id=chat_id, text=startText, parse_mode=telegram.ParseMode.HTML)

    sendWordRequestToAll(chat_data, chat_id, chat_bot)

def begin(update, context):
    if (update.message.chat_id > 0):
        context.bot.send_message(chat_id=update.message.chat_id, text="This command can only be sent in a group channel!", parse_mode=telegram.ParseMode.HTML)
        return

    if ("gameStarted" not in context.chat_data):
        context.bot.send_message(chat_id=update.message.chat_id, text="Type /new to create a new game!", parse_mode=telegram.ParseMode.HTML)
        return

    if (context.chat_data["gameStarted"]):
        context.bot.send_message(chat_id=update.message.chat_id, text="Game has already begun!", parse_mode=telegram.ParseMode.HTML)
    elif (len(context.chat_data["playersArray"]) < 2):
        context.bot.send_message(chat_id=update.message.chat_id, text="You need at least 2 players to begin a game!", parse_mode=telegram.ParseMode.HTML)
    else:
        context.chat_data["gameStarted"] = True
        context.chat_data["currentRound"] = 0
        context.chat_data["subRound"] = 0

        handleNewRound(context.chat_data, update.message.chat_id, context.bot)

def new_game(update, context):

    if (update.message.chat_id > 0):
        context.bot.send_message(chat_id=update.message.chat_id, text="This command can only be sent in a group channel!", parse_mode=telegram.ParseMode.HTML)
        return

    context.chat_data["gameStarted"] = False
    context.chat_data["playersArray"] = []
    context.chat_data["playersDict"] = {}
    context.chat_data["chat_id"] = update.message.chat_id
    context.chat_data["currentRound"] = 0
    context.chat_data["subRound"] = 0
    context.chat_data["seenWords"] = []
    context.chat_data["nextPlayer1Index"] = 0

    userId = update.message.from_user.id
    context.bot.send_message(chat_id=update.message.chat_id, text="New game has begun! Type '/in' to join the game! When everyone has joined, type /begin to begin the first round.", parse_mode=telegram.ParseMode.HTML)
    context.bot.send_message(chat_id=update.message.chat_id, text="For completely new players, remember to add the bot by clicking @medium_boardgame_bot before joining the game!", parse_mode=telegram.ParseMode.HTML)

def help(update, context):
    message = "Welcome to the Telegram Bot for the Medium Board Game!\n\n"
    message += "In the game Medium, players act as psychic mediums, harnessing their powerful extra-sensory abilities to access other players’ thoughts. Together in pairs, they mentally determine the Medium: the word that connects the words on their two cards, and then attempt to say the same word at the same time!\n\n"
    message += "For example, if the words are <b>fruit</b> and <b>gravity</b> a Medium Word might be <b>apple</b>. If both parties say the SAME Medium Word, they both get 10 points! Otherwise they fail and get a second attempt, except now the two new words to match are the words they've just given. If they match in the second attempt they get 5 points, and 2 if they match in the third and last attempt.\n\n"
    message += "Meanwhile, other players can try to snatch 1 point by matching either of the 2 main players\n\n"
    message += "To begin, add this bot at @medium_boardgame_bot and type /new to create a new game!\n\n"

    context.bot.send_message(chat_id=update.message.chat_id, text=message, parse_mode=telegram.ParseMode.HTML)

def stop(update, context):

    if (update.message.chat_id > 0):
        context.bot.send_message(chat_id=update.message.chat_id, text="This command can only be sent in a group channel!", parse_mode=telegram.ParseMode.HTML)
        return

    if ("gameStarted" not in context.chat_data):
        context.bot.send_message(chat_id=update.message.chat_id, text="Type /new to create a new game!", parse_mode=telegram.ParseMode.HTML)
        return

    pointsText = "Game ended!\n-----------------------\n<b>Current points:</b>\n"
    currentMaxPoints = -1
    winners = []
    for player in context.chat_data["playersArray"]:
        name = player["name"]
        points = player["points"]
        if (points > currentMaxPoints):
            winners = [name]
            currentMaxPoints = points
        elif (points == currentMaxPoints):
            winners.append(name)
        pointsText += "<b>%s</b>: %d points\n" % (player["name"], player["points"])

    pointsText += "\nWinner(s): "
    for name in winners:
        pointsText += name + ", "
    pointsText = pointsText[0:-2]
    context.bot.send_message(chat_id=update.message.chat_id, text=pointsText, parse_mode=telegram.ParseMode.HTML)

    # Reset data
    context.chat_data["gameStarted"] = False
    context.chat_data["playersArray"] = []
    context.chat_data["playersDict"] = {}
    context.chat_data["currentRound"] = 0
    context.chat_data["subRound"] = 0
    context.chat_data["seenWords"] = []
    context.chat_data["nextPlayer1Index"] = 0

def checkForAllEntered(chat_data, chat_id, chat_bot):
    allEntered = True
    enteredCount = 0
    for player in chat_data["playersArray"]:
        if (player["inGame"] == True):
            if (player["entry"] == None):
                allEntered = False
            else:
                enteredCount += 1

    if (allEntered):
        if enteredCount <= 1:
            chat_bot.send_message(chat_id=chat_data["chat_id"], text="We need at least 2 people to enter entries!", parse_mode=telegram.ParseMode.HTML)
            return

        chat_bot.send_message(chat_id=chat_data["chat_id"], text="Everyone has entered their words!", parse_mode=telegram.ParseMode.HTML)
        currentEntry = None
        testPassed = True
        entryText = "<b>Main Players:</b>\n"
        for player in chat_data["playersArray"]:
            if player["inGame"] and player["isMainPlayer"]:
                entry = player["entry"]
                chat_data["seenWords"].append(entry.lower())
                entryText += "Psychic %s entered - <b>%s</b>\n" % (player["name"], entry)

        # Check if anyone else matched
        if (len(chat_data["playersArray"]) > 2):
            found = False
            for player in chat_data["playersArray"]:
                if player["inGame"] and (not player["isMainPlayer"]):
                    entry = player["entry"]
                    if entry.lower() == chat_data["player1"]["entry"].lower() or entry.lower() == chat_data["player2"]["entry"].lower():

                        # Give player one point for matching one of the main players
                        player["points"] += NON_MAIN_POINTS

                        if not found:
                            found = True
                            entryText += "\n<b>Other Players:</b>\n"
                        entryText += "Psychic %s also entered - <b>%s</b>! (+%d points)\n" % (player["name"], entry, NON_MAIN_POINTS)

        chat_bot.send_message(chat_id=chat_id, text=entryText, parse_mode=telegram.ParseMode.HTML)

        # Main player has left the game!
        if not (chat_data["player1"]["inGame"] and chat_data["player2"]["inGame"]):
            chat_bot.send_message(chat_id=chat_id, text="One of the main players has temporarily left the game! Moving on to the next round...", parse_mode=telegram.ParseMode.HTML)
            chat_data["currentRound"] += 1
            chat_data["subRound"] = 0
            chat_bot.send_message(chat_id=chat_id, text="Oops! Last attempt failed! Moving on to next round...", parse_mode=telegram.ParseMode.HTML)
            handleNewRound(chat_data, chat_id, chat_bot)

        # Calculate if succeeded
        succeeded = chat_data["player1"]["entry"].lower() == chat_data["player2"]["entry"].lower()
        if succeeded:
            numPoints = POINTS_ARRAY[chat_data["subRound"]]
            chat_data["player1"]["points"] += numPoints
            chat_data["player2"]["points"] += numPoints
            chat_bot.send_message(chat_id=chat_id, text="Success! %s and %s get %d points each." % (chat_data["player1"]["name"], chat_data["player2"]["name"], numPoints), parse_mode=telegram.ParseMode.HTML)

            chat_data["currentRound"] += 1
            chat_data["subRound"] = 0
            handleNewRound(chat_data, chat_id, chat_bot)
        else:
            chat_data["subRound"] += 1

            if (chat_data["subRound"] == NUM_ROUNDS):
                chat_data["currentRound"] += 1
                chat_data["subRound"] = 0
                chat_bot.send_message(chat_id=chat_id, text="Oops! Last attempt failed! Moving on to next round...", parse_mode=telegram.ParseMode.HTML)
                handleNewRound(chat_data, chat_id, chat_bot)
            else:
                chat_data["words"] = (chat_data["player1"]["entry"], chat_data["player2"]["entry"])
                chat_bot.send_message(chat_id=chat_id, text="Oops! Try again with these two new words! - [%s] and [%s]" % (chat_data["words"]), parse_mode=telegram.ParseMode.HTML)

                sendWordRequestToAll(chat_data, chat_id, chat_bot)
        for player in chat_data["playersArray"]:
            player["entry"] = None

def test(update, context):
    chat_id = update.effective_chat.id
    userId = update.message.from_user.id
    entry = update.message.text

    context.bot.send_message(chat_id=userId, text=entry, parse_mode=telegram.ParseMode.HTML)

def enter(update, context):

    chat_id = update.effective_chat.id
    userId = update.message.from_user.id
    entry = update.message.text

    # Guarantees that this is private chat with player, rather than a group chat
    if (update.message.chat_id > 0):
        if ("chat_data" not in context.user_data):
            context.bot.send_message(chat_id=userId, text="Game has not yet started!", parse_mode=telegram.ParseMode.HTML)
            return

        chat_data = context.user_data["chat_data"]
        chat_bot = context.user_data["chat_bot"]
        chat_id = context.user_data["chat_id"]
        if ("gameStarted" in chat_data) and (chat_data["gameStarted"]):

            if entry.strip() == "":
                context.bot.send_message(chat_id=userId, text="Empty entry detected, please try again!" % entry, parse_mode=telegram.ParseMode.HTML)
            elif len(entry.split()) > 1:
                context.bot.send_message(chat_id=userId, text="You can only send <b>one</b> word!" % entry, parse_mode=telegram.ParseMode.HTML)
            elif entry.lower() not in chat_data["seenWords"]:
                chat_data["playersDict"][userId]["entry"] = entry
                context.bot.send_message(chat_id=userId, text="Received! - [%s]" % entry, parse_mode=telegram.ParseMode.HTML)
            else:
                context.bot.send_message(chat_id=userId, text="The word <b>%s</b> has been seen this round already!" % entry, parse_mode=telegram.ParseMode.HTML)

            checkForAllEntered(chat_data, chat_id, chat_bot)
        else:
            context.bot.send_message(chat_id=userId, text="Game has not yet started!", parse_mode=telegram.ParseMode.HTML)


def main():
    updater = Updater(token=TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('new',new_game))
    dispatcher.add_handler(CommandHandler('in',register_user))
    dispatcher.add_handler(CommandHandler('out',deregister_user))
    dispatcher.add_handler(CommandHandler('begin',begin))
    # dispatcher.add_handler(CommandHandler('enter',enter))
    # dispatcher.add_handler(CommandHandler('e',enter))
    dispatcher.add_handler(CommandHandler('help',help))

    dispatcher.add_handler(CommandHandler('stop',stop))
    dispatcher.add_handler(CommandHandler('points',points))
    dispatcher.add_handler(CommandHandler('left',players_left))
    dispatcher.add_handler(CommandHandler('kick_idle',kick_idle))

    dispatcher.add_handler(MessageHandler(Filters.text, enter))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
