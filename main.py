import telebot
from config import BOT_TOKEN
from handlers import register_handlers
from tasks import start_background

bot = telebot.TeleBot(BOT_TOKEN)
register_handlers(bot)
start_background(bot)
bot.polling(non_stop=True)