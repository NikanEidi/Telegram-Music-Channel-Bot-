import json
import re
from typing import Final
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, CallbackQueryHandler, filters
import mimetypes

TOKEN: Final = 'Your Token'
MUSIC_DB_FILE = 'music_database.json'
USER_DB_FILE = 'user_database.json'
CHANNEL_USERNAME = 'Your music chanel name'

# Custom filter to check if a document is an audio file
class AudioDocumentFilter(filters.BaseFilter):
    def filter(self, update: Update) -> bool:
        if update.message and update.message.document:
            mime_type = update.message.document.mime_type
            return mime_type and mime_type.startswith('audio/')
        return False

audio_document_filter = AudioDocumentFilter()

# Load the music database from a JSON file
def load_music_database():
    try:
        with open(MUSIC_DB_FILE, 'r', encoding='utf-8') as file:
            music_data = json.load(file)
            print("Loaded music database:", music_data)
            return music_data
    except FileNotFoundError:
        print(f"File {MUSIC_DB_FILE} not found.")
        return {}
    except IOError as e:
        print(f"Error reading file {MUSIC_DB_FILE}: {e}")
        return {}

# Save the music database to a JSON file
def save_music_database(database):
    try:
        with open(MUSIC_DB_FILE, 'w', encoding='utf-8') as file:
            json.dump(database, file, ensure_ascii=False, indent=4)
            print(f"Successfully wrote to file {MUSIC_DB_FILE}")
    except IOError as e:
        print(f"Error writing to file {MUSIC_DB_FILE}: {e}")

# Load the user database from a JSON file
def load_user_database():
    try:
        with open(USER_DB_FILE, 'r', encoding='utf-8') as file:
            user_data = json.load(file)
            print("Loaded user database:", user_data)
            return user_data
    except FileNotFoundError:
        print(f"File {USER_DB_FILE} not found.")
        return []
    except IOError as e:
        print(f"Error reading file {USER_DB_FILE}: {e}")
        return []

# Save the user database to a JSON file
def save_user_database(database):
    try:
        with open(USER_DB_FILE, 'w', encoding='utf-8') as file:
            json.dump(database, file, ensure_ascii=False, indent=4)
            print(f"Successfully wrote to file {USER_DB_FILE}")
    except IOError as e:
        print(f"Error writing to file {USER_DB_FILE}: {e}")

music_database = load_music_database()
user_database = load_user_database()

# List of accepted audio file extensions
ACCEPTED_AUDIO_EXTENSIONS = [
    '.3gp', '.aa', '.aac', '.aax', '.act', '.aiff', '.alac', '.amr', '.ape', '.au',
    '.awb', '.dss', '.dvf', '.flac', '.gsm', '.iklax', '.ivs', '.m4a', '.m4b', '.m4p',
    '.mmf', '.movpkg', '.mp3', '.mpc', '.msv', '.nmf', '.ogg', '.oga', '.mogg', '.opus',
    '.ra', '.rm', '.raw', '.rf64', '.sln', '.tta', '.voc', '.vox', '.wav', '.wma', '.wv',
    '.webm', '.8svx', '.cda'
]

# Function to check if a user is a member of the channel
async def is_member(update: Update, context: CallbackContext) -> bool:
    user_id = update.message.chat_id
    member_status = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
    return member_status.status in ['member', 'administrator', 'creator']

# Command handlers
async def start_command(update: Update, context: CallbackContext):
    if not await is_member(update, context):
        await update.message.reply_text(f'Please first join our Telegram channel and then restart the bot: {CHANNEL_USERNAME}')
        return
    user_id = update.message.chat_id
    if user_id not in user_database:
        user_database.append(user_id)
        save_user_database(user_database)
    await update.message.reply_text('Hello! How can I help you?')

async def help_command(update: Update, context: CallbackContext):
    if not await is_member(update, context):
        await update.message.reply_text(f'Please first join our Telegram channel and then restart the bot: {CHANNEL_USERNAME}')
        return
    await update.message.reply_text('If you have any issues with the bot, please message this ID: @Nikankuroko')

async def search_command(update: Update, context: CallbackContext):
    if not await is_member(update, context):
        await update.message.reply_text(f'Please first join our Telegram channel and then restart the bot: {CHANNEL_USERNAME}')
        return
    await update.message.reply_text('Please enter the name of the music or artist.')

async def handle_response(update: Update, context: CallbackContext):
    if not await is_member(update, context):
        await update.message.reply_text(f'Please first join our Telegram channel and then restart the bot: {CHANNEL_USERNAME}')
        return
    query = update.message.text.lower()
    results = []

    for artist_name, musics in music_database.items():
        for music_name, music_info in musics.items():
            artists = re.split(r' & | x | X | ft\. | Ft\. | ft | Ft | \, ', artist_name.lower())
            song = music_name.lower()

            if query in artists or query == song or any(query in artist for artist in artists):
                results.append((artist_name, music_name))

    if results:
        keyboard = [
            [InlineKeyboardButton(f'{music_name} by {artist_name}', callback_data=f'{artist_name}|{music_name}')]
            for artist_name, music_name in results
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('Search Results:', reply_markup=reply_markup)
    else:
        await update.message.reply_text('No music found with this name.')

async def send_music(update: Update, context: CallbackContext, artist_name: str, music_name: str):
    file_id = music_database[artist_name][music_name]['file_id']
    caption = f" {CHANNEL_USERNAME} ."
    await context.bot.send_audio(chat_id=update.callback_query.message.chat_id, audio=file_id, caption=caption)
    print(f"Sent music {music_name} by {artist_name} with file_id {file_id} and caption {caption}.")

async def button_click(update: Update, context: CallbackContext):
    query = update.callback_query
    artist_name, music_name = query.data.split('|')
    await send_music(update, context, artist_name, music_name)

async def save_new_music(update: Update, context: CallbackContext):
    if not await is_member(update, context):
        await update.message.reply_text(f'Please first join our Telegram channel and then restart the bot: {CHANNEL_USERNAME}')
        return
    if update.message.document:
        file = update.message.document
    elif update.message.audio:
        file = update.message.audio
    elif update.message.voice:
        file = update.message.voice
    else:
        await update.message.reply_text('Please send a valid audio file.')
        print("Error: No valid audio file received.")
        return

    file_extension = '.' + file.file_name.split('.')[-1].lower() if update.message.document else '.ogg'

    if file.mime_type.startswith('audio/') or file_extension in ACCEPTED_AUDIO_EXTENSIONS:
        file_id = file.file_id
        artists_raw = file.performer if file.performer else "Unknown"
        artists = [a.strip() for a in re.split(r' & | x | X | ft\. | Ft\. | ft | Ft | \, ', artists_raw)]
        music_name = file.title if file.title else "Untitled"

        for artist in artists:
            if artist not in music_database:
                music_database[artist] = {}
            music_database[artist][music_name] = {
                'file_id': file_id,
                'artists': artists
            }
        save_music_database(music_database)
        await update.message.reply_text(f'Music {music_name} by {", ".join(artists)} successfully added to the database.')
        print(f"Added music {music_name} by {', '.join(artists)} with file_id {file_id} to database.")

        # Send message to all users
        for user_id in user_database:
            try:
                await context.bot.send_message(chat_id=user_id, text=f'New music "{music_name}" by "{", ".join(artists)}" has been added to the bot and channel.')
            except Exception as e:
                print(f"Error sending message to user {user_id}: {e}")
    else:
        await update.message.reply_text('Please send only valid audio files.')
        print("Error: File is not a valid audio format.")

def main():
    application = Application.builder().token(TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('search', search_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_response))
    application.add_handler(MessageHandler(filters.AUDIO | filters.VOICE | audio_document_filter, save_new_music))
    application.add_handler(CallbackQueryHandler(button_click))

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
