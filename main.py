
import base64
from collections import namedtuple
from datetime import datetime, timedelta
import io
import json
import os
import sys
import threading
from threading import Thread
import time
# from my classes
# from the orginal Telegram API
from telegram import InlineKeyboardButton, KeyboardButton, Message, ReplyMarkup, Update, User
from telegram import InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import CallbackContext
from telegram.ext import CallbackQueryHandler
# The Updater class continuously fetches new updates from telegram and passes them on to the Dispatcher class
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import InlineQueryHandler
from telegram.ext import ConversationHandler
from telegram.ext import RegexHandler
from telegram.ext import MessageHandler, Filters
from telegramToken import Token
from google_photos_uploader import GooglePhotosUploader

from PIL import Image
# we set up the logging module, so you will know when (and why) things don't work as expected (see Exception Handling in docs)
import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

updater = Updater(token=Token.token, use_context=True)
dispatcher = updater.dispatcher

chat_id = ""

#####################################################################################
# Commands
#####################################################################################
# /start command
# start() is a function that should process a specific type of update
# sendMessage() - use this method to send messages
def startMessage(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id

    print("Function: startMessage")
    updater.bot.send_message(chat_id=update.message.chat_id, text="Hi, I'm Album Bot. I'll keep track of your images that get dumped to the chat.")
    updater.bot.send_message(chat_id=update.message.chat_id, text="If you wish to post an image or video without adding it to the google photos album, add 'exclude' or 'meme' to the message")
    sent_message = updater.bot.send_message(chat_id=update.message.chat_id, text="Here is this google photos album for this chat: https://photos.app.goo.gl/GrFrz5KwKWk4DgUp7")
    
    updater.bot.pin_chat_message(chat_id, sent_message.message_id)

# /help command
def help(update: Update, context: CallbackContext):
    text="\n\nHi. I cannot help you."
    sendTelegramMessage(update, context, text)

#####################################################################################
# Message Handling
#####################################################################################

def downloadImages(update: Update, context: CallbackContext):
    print("Function: downloadImages")
    message_text = str(update.message.caption).lower() + " " + str(update.message.text).lower()
    print("message: " + message_text)
    
    test_list = ['exclude', 'meme']
    res = [ele for ele in test_list if(ele in message_text)]
    if bool(res):
        return
    
    photo = updater.bot.getFile(update.message.photo[-1].file_id)
    
    cwd = os.getcwd()
    downloaded_photo = photo.download()
    print(downloaded_photo)

    photo_path = cwd + "/" + downloaded_photo

    # upload to google photos
    album_name = "2024 Commune July 4th"
    uploadPhotoToGoogleAlbum([photo_path], album_name)

    os.remove(photo_path)

def downloadImageAttachments(update: Update, context: CallbackContext):
    print("Function: downloadImages")
    message_text = str(update.message.caption).lower() + " " + str(update.message.text).lower()
    print("message: " + message_text)
    
    test_list = ['exclude', 'meme']
    res = [ele for ele in test_list if(ele in message_text)]
    if bool(res):
        return
    
    photo = updater.bot.getFile(update.message.effective_attachment.file_id)
    
    cwd = os.getcwd()
    downloaded_photo = photo.download()
    print(downloaded_photo)

    photo_path = cwd + "/" + downloaded_photo

    # upload to google photos
    album_name = "2024 Commune July 4th"
    uploadPhotoToGoogleAlbum([photo_path], album_name)

    os.remove(photo_path)

def downloadVideos(update: Update, context: CallbackContext):
    print("Function: downloadImages")
    message_text = str(update.message.caption).lower() + " " + str(update.message.text).lower() + str(update.message.video_note).lower()
    print("message: " + message_text)
    
    test_list = ['exclude', 'meme']
    res = [ele for ele in test_list if(ele in message_text)]
    if bool(res):
        return
    
    video = updater.bot.getFile(update.message.video.file_id)
    
    cwd = os.getcwd()
    downloaded_video = video.download()
    print(downloaded_video)

    video_path = cwd + "/" + downloaded_video

    # upload to google videos
    album_name = "2024 Commune July 4th"
    uploadPhotoToGoogleAlbum([video_path], album_name)

    os.remove(video_path)

#####################################################################################
# Helpers
#####################################################################################

def uploadPhotoToGoogleAlbum(photo_paths: list[str], albumName: str ):
    photo_uploader = GooglePhotosUploader()
    photo_uploader.upload_photos(photo_paths, albumName)


def sendTelegramMessage(update: Update, context: CallbackContext, message: str) -> Message:
    max_tries: int = 10
    for i in range(max_tries):
        try:
            time.sleep(0.3)
            return updater.bot.send_message(chat_id = update.message.chat_id, text = message, timeout = 60)
        except Exception:
            continue

def updateTelegramMessage(update: Update, context: CallbackContext, messageId: int, message: str) -> Message:
    max_tries: int = 10
    for i in range(max_tries):
        try:
            time.sleep(0.3)
            return updater.bot.edit_message_text(chat_id = update.message.chat_id, message_id=messageId, text=message, timeout = 60)
        except Exception:
            continue

def sendTelegramReplyMessage(update: Update, context: CallbackContext, text: str, reply_markup: ReplyMarkup) -> Message:
    max_tries: int = 10
    for i in range(max_tries):
        try:
            time.sleep(0.3)
            return updater.bot.send_message(chat_id = update.message.chat_id, text = text, reply_markup = reply_markup, timeout = 60)
        except Exception:
            continue

# command to stop the bot using /stop
def stopBot(update: Update, context: CallbackContext):
    print(f"stopped by {update.effective_user.first_name}")
    updater.bot.send_message(chat_id=update.message.chat_id, text="No longer logging images and videos. Until next time!")
    #sys.exit("exited!")
    updater.stop()

# a command filter to reply to all commands that were not recognized by the previous handlers.
def unknown(update: Update, context: CallbackContext):
    updater.bot.send_message(chat_id=update.message.chat_id, text="Sorry, I didn't understand that try using the /help command instead.")

def main():
    ################ Add your other handlers here... ##########################
    # /start command
    start_handler = CommandHandler('start', startMessage)
    dispatcher.add_handler(start_handler)

    # /help - help screen
    help_handler = CommandHandler('help', help)
    dispatcher.add_handler(help_handler)

    photo_download_handler = MessageHandler(filters=Filters.photo, callback=downloadImages)
    dispatcher.add_handler(photo_download_handler)

    uncompressed_photo_handler = MessageHandler(filters=Filters.attachment, callback=downloadImageAttachments)
    dispatcher.add_handler(uncompressed_photo_handler)

    video_download_handler = MessageHandler(filters=Filters.video, callback=downloadVideos)
    dispatcher.add_handler(video_download_handler)
    
    # /stop command
    stop_handler = CommandHandler('stop', stopBot, filters=Filters.user(username='@' + 'weldonla'))
    dispatcher.add_handler(stop_handler)

    #####################################################################################
    def stop_and_restart():
        """Gracefully stop the Updater and replace the current process with a new one"""
        updater.stop()
        os.execl(sys.executable, sys.executable, *sys.argv)

    def restart(update, context):
        Thread(target=stop_and_restart).start()

    dispatcher.add_handler(CommandHandler('restart', restart, filters=Filters.user(username='@' + 'weldonla')))
    #####################################################################################

   # IMPORTANT: must be added last!!!! unknown command
    unknown_handler = MessageHandler(Filters.command, unknown)
    dispatcher.add_handler(unknown_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()