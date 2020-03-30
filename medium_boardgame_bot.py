TOKEN = "953155266:AAF-g0tEk7qMCZwDxheNHQZD3oGMXn5w3G0"

# TODO:
# 1) don't let /begin work multiple times

import telegram
from telegram.ext import Updater, InlineQueryHandler, CommandHandler
# import requests
from word_lib import getWords
import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def register_user(update, context):
    userId = update.message.from_user.id
    name = update.message.from_user.first_name

    if ("waitingForPlayers" in context.chat_data) and (context.chat_data["waitingForPlayers"]):
        context.user_data["chat_data"] = context.chat_data
        context.user_data["chat_id"] = update.message.chat_id
        context.user_data["chat_bot"] = context.bot

        if userId not in context.chat_data["playersDict"]:
            context.chat_data["numPlayers"] += 1
            player = {"id":userId, "name":name, "entry":None, "points": 0}
            context.chat_data["playersArray"].append(player)
            context.chat_data["playersDict"][userId] = player

            context.bot.send_message(chat_id=update.message.chat_id, text="Psychic <b>%s</b> has joined the game!" % name, parse_mode=telegram.ParseMode.HTML)
        else:
            context.bot.send_message(chat_id=update.message.chat_id, text="Psychic <b>%s</b> is already in the game!" % name, parse_mode=telegram.ParseMode.HTML)

    else:
        context.bot.send_message(chat_id=update.message.chat_id, text="Game has not yet started!", parse_mode=telegram.ParseMode.HTML)


def begin(update, context):
    if (len(context.chat_data["playersArray"]) < 2):
        context.bot.send_message(chat_id=update.message.chat_id, text="You need at least 2 players to begin a game!", parse_mode=telegram.ParseMode.HTML)
    else:
        context.chat_data["gameStarted"] = True
        context.chat_data["subRound"] = 0
        handleNewRound(context.chat_data, update.message.chat_id, context.bot)

def playersLeft(update, context):
    if (len(context.chat_data["playersArray"]) < 2):
        context.bot.send_message(chat_id=update.message.chat_id, text="Waiting for game to begin!", parse_mode=telegram.ParseMode.HTML)
    else:
        leftText = "Still waiting for: "
        for player in context.chat_data["playersArray"]:
            if player["entry"] == None:
                leftText += "<b>%s</b>, " % player["name"]
        leftText = leftText[0:-2]
        context.bot.send_message(chat_id=update.message.chat_id, text=leftText, parse_mode=telegram.ParseMode.HTML)

POINTS_ARRAY = [10,5,2]
NON_MAIN_POINTS = 1 # points the non main players get for matching with main players
NUM_ROUNDS = len(POINTS_ARRAY)


def points(update, context):
    printScore(context.chat_data, update.message.chat_id, context.bot)

def printScore(chat_data, chat_id, chat_bot):
    # print points
    pointsText = "<b>Current points:</b>\n"
    for player in chat_data["playersArray"]:
        pointsText += "%s: %d points\n" % (player["name"], player["points"])
    chat_bot.send_message(chat_id=chat_id, text=pointsText, parse_mode=telegram.ParseMode.HTML)

def sendWordRequest(chat_data, chat_id, chat_bot):
    for player in chat_data["playersArray"]:
        player["entry"] == None

        chat_bot.send_message(chat_id=player["id"], text="Current words are <b>%s</b> and <b>%s</b>!" % chat_data["words"], parse_mode=telegram.ParseMode.HTML)
        chat_bot.send_message(chat_id=player["id"], text="When you are ready, enter your Medium Word (only one!) here by typing '/enter [Word]' or '/e [Word]'", parse_mode=telegram.ParseMode.HTML)


def handleNewRound(chat_data, chat_id, chat_bot):
    numPlayers = len(chat_data["playersArray"])

    if (chat_data["subRound"] == 0):
        chat_data["seenWords"] = []
        chat_data["words"] = getWords()

    currentRound = chat_data["currentRound"]
    currentSubRound = chat_data["subRound"]

    if (currentRound > 0 and currentRound % numPlayers == 0):
        printScore(chat_data, chat_id, chat_bot)

    player1Index = currentRound % numPlayers
    player2Index = (currentRound+1) % numPlayers

    # Initialize main player to false first
    for player in chat_data["playersArray"]:
        player["isMainPlayer"] = False

    chat_data["player1"] = chat_data["playersArray"][player1Index]
    chat_data["player2"] = chat_data["playersArray"][player2Index]

    chat_data["player1"]["isMainPlayer"] = True
    chat_data["player2"]["isMainPlayer"] = True

    startText = "<b>Round %d - Attempt %d</b>\n" % (currentRound+1, currentSubRound+1)
    startText += "Main players: %s and %s\n" % (chat_data["player1"]["name"], chat_data["player2"]["name"])

    startText += "Let's get psychic! The two words are: <b>%s</b> and <b>%s</b>" % chat_data["words"]
    chat_bot.send_message(chat_id=chat_id, text=startText, parse_mode=telegram.ParseMode.HTML)

    sendWordRequest(chat_data, chat_id, chat_bot)

def begin(update, context):
    if (len(context.chat_data["playersArray"]) < 2):
        context.bot.send_message(chat_id=update.message.chat_id, text="You need at least 2 players to begin a game!", parse_mode=telegram.ParseMode.HTML)
    else:
        context.chat_data["gameStarted"] = True
        context.chat_data["subRound"] = 0
        handleNewRound(context.chat_data, update.message.chat_id, context.bot)

def start(update, context):

    words = getWords()
    context.chat_data["gameStarted"] = False
    context.chat_data["waitingForPlayers"] = True
    context.chat_data["numPlayers"] = 0
    context.chat_data["playersArray"] = []
    context.chat_data["playersDict"] = {}
    context.chat_data["chat_id"] = update.message.chat_id
    context.chat_data["currentRound"] = 0
    context.chat_data["seenWords"] = []

    # startText = "Let's get psychic! The two words are: [%s] and [%s]" % words
    userId = update.message.from_user.id
    context.bot.send_message(chat_id=update.message.chat_id, text="New game has begun! Type '/in' to join the game!", parse_mode=telegram.ParseMode.HTML)


def help(update, context):
    message = "Welcome to the Telegram Bot for the Medium Board Game!\n\n"
    message += "In the game Medium, players act as psychic mediums, harnessing their powerful extra-sensory abilities to access other players’ thoughts. Together in pairs, they mentally determine the Medium: the word that connects the words on their two cards, and then attempt to say the same word at the same time!\n\nTwo cards. Two thoughts. One mind."

    context.bot.send_message(chat_id=update.message.chat_id, text=message, parse_mode=telegram.ParseMode.HTML)

def stop(update, context):
    pointsText = "Game ended!\n-----------------------\nCurrent points:\n"
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
        pointsText += "%s: %d points\n" % (player["name"], player["points"])

    pointsText += "\nWinner(s): "
    for name in winners:
        pointsText += name + ", "
    pointsText = pointsText[0:-2]
    context.bot.send_message(chat_id=update.message.chat_id, text=pointsText, parse_mode=telegram.ParseMode.HTML)


def enter(update, context):

    chat_data = context.user_data["chat_data"]
    chat_bot = context.user_data["chat_bot"]
    chat_id = context.user_data["chat_id"]

    if ("gameStarted" in chat_data) and (chat_data["gameStarted"]):
        userId = update.message.from_user.id
        entry = update.message.text.partition(' ')[2]

        if entry not in chat_data["seenWords"]:
            chat_data["playersDict"][userId]["entry"] = entry
            context.bot.send_message(chat_id=userId, text="Received! - [%s]" % entry, parse_mode=telegram.ParseMode.HTML)
        else:
            context.bot.send_message(chat_id=userId, text="The word <b>%s</b> has been seen this round already!" % entry, parse_mode=telegram.ParseMode.HTML)

        allEntered = True
        for player in chat_data["playersArray"]:
            if (player["entry"] == None):
                allEntered = False

        if (allEntered):
            context.bot.send_message(chat_id=chat_data["chat_id"], text="Everyone has entered their words!", parse_mode=telegram.ParseMode.HTML)
            currentEntry = None
            testPassed = True
            entryText = "<b>Main Players:</b>\n"
            for player in chat_data["playersArray"]:
                if player["isMainPlayer"]:
                    entry = player["entry"]
                    chat_data["seenWords"].append(entry)
                    entryText += "Psychic %s entered - <b>%s</b>\n" % (player["name"], entry)

            # Check if anyone else matched
            if (len(chat_data["playersArray"]) > 2):
                found = False
                for player in chat_data["playersArray"]:
                    if not player["isMainPlayer"]:
                        entry = player["entry"]
                        if entry.lower() == chat_data["player1"]["entry"].lower() or entry.lower() == chat_data["player2"]["entry"].lower():

                            # Give player one point for matching one of the main players
                            player["points"] += NON_MAIN_POINTS

                            if not found:
                                found = True
                                entryText += "\n<b>Other Players:</b>\n"
                            entryText += "Psychic %s also entered - <b>%s</b>! (+%d points)\n" % (player["name"], entry, NON_MAIN_POINTS)


            context.bot.send_message(chat_id=chat_id, text=entryText, parse_mode=telegram.ParseMode.HTML)

            # Calculate if succeeded
            succeeded = chat_data["player1"]["entry"].lower() == chat_data["player2"]["entry"].lower()
            if succeeded:
                numPoints = POINTS_ARRAY[chat_data["subRound"]]
                chat_data["player1"]["points"] += numPoints
                chat_data["player2"]["points"] += numPoints
                context.bot.send_message(chat_id=chat_id, text="Success! %s and %s get %d points each." % (chat_data["player1"]["name"], chat_data["player2"]["name"], numPoints), parse_mode=telegram.ParseMode.HTML)

                chat_data["currentRound"] += 1
                chat_data["subRound"] = 0
                handleNewRound(chat_data, chat_id, chat_bot)
            else:
                chat_data["subRound"] += 1

                if (chat_data["subRound"] == NUM_ROUNDS):
                    chat_data["currentRound"] += 1
                    chat_data["subRound"] = 0
                    context.bot.send_message(chat_id=chat_id, text="Oops! Last attempt failed! Moving on to next round...", parse_mode=telegram.ParseMode.HTML)
                    handleNewRound(chat_data, chat_id, chat_bot)
                else:
                    chat_data["words"] = (chat_data["player1"]["entry"], chat_data["player2"]["entry"])
                    context.bot.send_message(chat_id=chat_id, text="Oops! Try again with these two new words! - [%s] and [%s]" % (chat_data["words"]), parse_mode=telegram.ParseMode.HTML)

                    sendWordRequest(chat_data, chat_id, chat_bot)
            for player in chat_data["playersArray"]:
                player["entry"] = None
    else:
        context.bot.send_message(chat_id=chat_id, text="Game has not yet started!", parse_mode=telegram.ParseMode.HTML)

def main():
    updater = Updater(token=TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('start',start))
    dispatcher.add_handler(CommandHandler('in',register_user))
    dispatcher.add_handler(CommandHandler('begin',begin))
    dispatcher.add_handler(CommandHandler('enter',enter))
    dispatcher.add_handler(CommandHandler('e',enter))
    dispatcher.add_handler(CommandHandler('help',help))
    dispatcher.add_handler(CommandHandler('stop',stop))
    dispatcher.add_handler(CommandHandler('points',points))
    dispatcher.add_handler(CommandHandler('left',playersLeft))

    # dispatcher.add_handler(CommandHandler('put', put))
    # dispatcher.add_handler(CommandHandler('get', get))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
