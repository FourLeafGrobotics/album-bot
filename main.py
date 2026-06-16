
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
import gspread
import pandas as pd
import dataframe_image as dfi
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
# album bot username `@mnemosyne_album_bot`
chat_id = "5500670805"

#####################################################################################
# Commands
#####################################################################################
# /start command
# start() is a function that should process a specific type of update
# sendMessage() - use this method to send messages
def startMessage(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id

    print("Function: startMessage")
    updater.bot.send_message(chat_id=update.message.chat_id, text="Hi, I'm Dionysus. I'll keep track of your images that get dumped to the chat. I also have other useful commands you can see with the /help command")
    updater.bot.send_message(chat_id=update.message.chat_id, text="If you wish to post an image or video without adding it to the google photos album, add 'exclude' or 'meme' to the message")
    sent_message = updater.bot.send_message(chat_id=update.message.chat_id, text="Here is this google photos album for this chat: https://photos.app.goo.gl/9qjnbP8h7KifWk4B8")
    
    updater.bot.pin_chat_message(chat_id, sent_message.message_id)

# /help command
def help(update: Update, context: CallbackContext):
    text = "Available commands:\n/start - Initialize bot\n/dietary - Get dietary restrictions.\n/dietary attendance - Get the days people with dietary restrictions are present.\n/dietary day - Get the current day's dietary restrictions.\n/dietary <day> - Get the dietary restrictions for a specific day of the party.\n/chores <day> - Get chores table for a day.\n/help - Show this message"
    sendTelegramMessage(update, context, text)

from enum import Enum

class PartyDays(Enum):
    JULY_2 = "Thursday, July 2nd"
    JULY_3 = "Friday, July 3rd"
    JULY_4 = "Saturday, July 4th"
    JULY_5 = "Sunday, July 5th"

# /dietary command
def dietary(update: Update, context: CallbackContext):
    client = gspread.service_account(filename='credentials.json')
    spreadsheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1sHFsWpAOaYdZ4kESqyN31m0Kl3UB2z1E3zj8JCpi8c8/edit?usp=sharing')
    worksheet = spreadsheet.sheet1
    df = pd.DataFrame(worksheet.get_all_records())
    
    # Filter for the relevant column
    dietary_info = df[['What is your name?', 'Do you have any allergies or dietary restrictions?', 'Days Attending']].dropna(subset=['What is your name?', 'Do you have any allergies or dietary restrictions?'])
    
    arg = context.args[0].lower() if context.args else None
    
    if arg == 'attendance':
        message = "Dietary Restrictions & Attendance:\n"
        for index, row in dietary_info.iterrows():
            restriction = row['Do you have any allergies or dietary restrictions?']
            if restriction.lower() == 'none' or not restriction:
                continue
            message += f"{row['What is your name?']} - {row['Days Attending']}\n"
            
    elif arg in ['2', '3', '4', '5'] or arg == 'day':
        # Mapping input arg to PartyDays
        day_map = {'2': PartyDays.JULY_2.value, '3': PartyDays.JULY_3.value, '4': PartyDays.JULY_4.value, '5': PartyDays.JULY_5.value}
        
        if arg == 'day':
            # Today's date logic
            current_day = datetime.now().day
            target_day_str = day_map.get(str(current_day))
        else:
            target_day_str = day_map.get(arg)
            
        if not target_day_str:
            message = "Invalid day. Please use 2, 3, 4, or 5."
        else:
            # Filter by day
            filtered_df = dietary_info[dietary_info['Days Attending'].str.contains(target_day_str, na=False)]
            
            restrictions = {}
            for index, row in filtered_df.iterrows():
                restriction = row['Do you have any allergies or dietary restrictions?']
                if restriction.lower() == 'none' or not restriction:
                    continue
                res_list = [r.strip() for r in restriction.split(',')]
                for r in res_list:
                    restrictions[r] = restrictions.get(r, 0) + 1
                    
            message = f"Dietary Restrictions {target_day_str}\n"
            for res, count in restrictions.items():
                message += f"{res} - {count}\n"
                
    else:
        # Default behavior: list by restriction and names
        restrictions = {}
        for index, row in dietary_info.iterrows():
            handle = row['What is your name?']
            restriction = row['Do you have any allergies or dietary restrictions?']
            
            if restriction.lower() == 'none' or not restriction:
                continue
                
            res_list = [r.strip() for r in restriction.split(',')]
            
            for r in res_list:
                if r not in restrictions:
                    restrictions[r] = []
                restrictions[r].append(handle)
                
        message = "Dietary Restrictions:\n"
        for res, handles in restrictions.items():
            message += f"{res} - {', '.join(handles)}\n"
        
    sendTelegramMessage(update, context, message)

# /chores command
def chores(update: Update, context: CallbackContext):
    day = int(context.args[0]) if context.args else None
    if not day:
        sendTelegramMessage(update, context, "Please specify a numbered day (e.g., /chores 2)")
        return
        
    day_map = {
        2: 'Thursday, July 2nd',
        3: 'Friday, July 3rd',
        4: 'Saturday, July 4th',
        5: 'Sunday, July 5th'
    }
    
    target_sheet_name = day_map.get(day)

    if not target_sheet_name:
        sendTelegramMessage(update, context, "Invalid day. Please use Thursday, Friday, Saturday, or Sunday.")
        return
        
    client = gspread.service_account(filename='credentials.json')
    spreadsheet = client.open_by_url('https://docs.google.com/spreadsheets/d/18cRirNi1sXnPhPE6NZJeQzn9AC8kcKBSbi655sGE0ds/edit?gid=234464649')
    
    try:
        worksheet = spreadsheet.worksheet(target_sheet_name)
    except:
        sendTelegramMessage(update, context, "Could not find chore list for that day.")
        return
        
    df = pd.DataFrame(worksheet.get_all_records())
    df_subset = df[['Time', 'Chore', 'Person']]
    
    # Save as image
    image_path = 'chores.png'
    dfi.export(df_subset, image_path)
    
    # Send image
    chat_id = update.message.chat_id
    message = updater.bot.send_photo(chat_id=chat_id, photo=open(image_path, 'rb'), caption="Chores for " + day_map.get(day))
    updater.bot.pin_chat_message(chat_id, message.message_id)
    
    os.remove(image_path)


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
    album_name = "2026 July 4th Party"
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
    album_name = "2026 July 4th Party"
    uploadPhotoToGoogleAlbum([photo_path], album_name)

    os.remove(photo_path)

def downloadVideos(update: Update, context: CallbackContext):
    print("Function: downloadVideos")
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
    album_name = "2026 July 4th Party"
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

    # /dietary - dietary info
    dietary_handler = CommandHandler('dietary', dietary)
    dispatcher.add_handler(dietary_handler)

    # /chores - chores table
    chores_handler = CommandHandler('chores', chores)
    dispatcher.add_handler(chores_handler)

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