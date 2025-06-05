
from telebot import types

def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton('➕ Добавить продукт', callback_data='add_product'),
        types.InlineKeyboardButton('🗑️ Удалить продукт', callback_data='delete_product'),
        types.InlineKeyboardButton('📃 Список продуктов', callback_data='list_products'),
        types.InlineKeyboardButton('🕵️ Проверить просрочку', callback_data='check_expired'),
        types.InlineKeyboardButton("🍳 Найти рецепт", callback_data='get_recipe'),
        types.InlineKeyboardButton("💖 Поддержать разработчика", callback_data='support_programmer')
    )
    return markup

def show_main_menu(bot, chat_id, message_id=None):
    text = "🏠 *Главное меню*\nВыберите действие:"
    if message_id:
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            parse_mode='Markdown',
            reply_markup=main_menu()
        )
    else:
        bot.send_message(
            chat_id,
            text,
            parse_mode='Markdown',
            reply_markup=main_menu()
        )
