import datetime
import uuid
from telebot import types
from gigachat import GigaChat
import storage
import menus
from config import supabase, OCR_API_KEY
import cv2
import re, datetime
import numpy as np
import pytesseract
import requests
import re

def register_handlers(bot):
    @bot.message_handler(commands=['start'])
    def start(message):
        menus.show_main_menu(bot, message.chat.id)

    @bot.callback_query_handler(func=lambda call: True)
    def handle_callback(call):
        user_id = str(call.message.chat.id)
        data = call.data

        if data == 'main_menu':
            menus.show_main_menu(bot, call.message.chat.id, call.message.message_id)

        elif data == 'add_product':
            msg = bot.send_message(user_id, "📝 Введите название продукта:")
            bot.register_next_step_handler(msg, process_product_name)

        elif data == 'delete_product':
            show_delete_menu(bot, user_id, call.message)

        elif data == 'list_products':
            show_product_list(bot, user_id, call.message)

        elif data == 'check_expired':
            check_expired_products(bot, user_id, call.message)

        elif data.startswith('delete_'):
            delete_product(bot, user_id, call)

        elif data.startswith('date_text') or data.startswith('date_photo'):
            choose_date_input(call)
        elif data == 'get_recipe':
            suggest_recipe(bot, user_id, call.message)

        elif data == 'support_programmer':

             markup = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("↩️ Назад", callback_data='main_menu')
    )
             bot.send_message(call.message.chat.id,
                 "💖 *Поддержать разработчика:*\n\n"
                 "Если бот вам помог, вы можете поддержать разработчика:\n\n"
                 "📱 СБП / по номеру: `+7-(985)-(309)-78-42`\n"
                 "💳 Карта: `2202-2061-6697-8994`\n"
                 "Спасибо за вашу поддержку! 🙏",
                 parse_mode='Markdown',
                 reply_markup=markup
             )


        bot.answer_callback_query(call.id)



    def suggest_recipe(bot, user_id, message):
        
        resp = supabase.table("products").select("name").eq("user_id", user_id).execute()
        items = resp.data or []
        
        if not items:
            bot.send_message(user_id, "📭 У вас нет продуктов для генерации рецепта.", reply_markup=menus.main_menu())
            return

        ingredients = [item["name"] for item in items]
        ingredient_list = ", ".join(ingredients)

        prompt = f"""Ты — помощник-повар. Пользователь указал следующие продукты: {ingredient_list}.
На основе этого, предложи один простой рецепт, включая название, шаги приготовления и необходимые дополнительные ингредиенты, если они нужны."""

        recipe_text = call_gigachat(prompt)

        markup = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("↩️ Назад", callback_data='main_menu')
    )
        bot.send_message(user_id, f"🍽️ *Рецепт:*\n\n{recipe_text}", parse_mode='Markdown', reply_markup=markup)

    def call_gigachat(prompt):
        my_secret_key = 'YOUR_API_KEY'
        giga = GigaChat(
        credentials=my_secret_key,
        verify_ssl_certs=False
      )
        response = giga.chat(prompt)
        
        return(response.choices[0].message.content)


    def process_product_name(message):
        product_name = message.text
        chat_id = message.chat.id
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton('⌨️ Ввести вручную', callback_data=f"date_text|{product_name}"),
            types.InlineKeyboardButton('📷 Загрузить фото', callback_data=f"date_photo|{product_name}")
        )

        bot.send_message(
            chat_id,
            f"📅 Выберите способ ввода срока годности для *{product_name}*:",
            parse_mode='Markdown',
            reply_markup=markup
        )

    def choose_date_input(call):
        mode, product_name = call.data.split('|', 1)
        chat_id = call.message.chat.id

        if mode == 'date_text':
            msg = bot.send_message(chat_id, f"⌨️ Введите дату для *{product_name}* в формате ДД.MM.YYYY:", parse_mode='Markdown')
            bot.register_next_step_handler(msg, lambda m: handle_date_text(m, product_name))
        else:  
            msg = bot.send_message(chat_id, f"📷 Пришлите фото с датой для *{product_name}*:", parse_mode='Markdown')
            bot.register_next_step_handler(msg, lambda m: handle_date_photo(m, product_name))

        bot.answer_callback_query(call.id)


    def handle_date_text(message, product_name):
        chat_id = message.chat.id
        try:
            exp_date = datetime.datetime.strptime(message.text, "%d.%m.%Y").date()
        except ValueError:
            msg = bot.send_message(chat_id, "❌ Неверный формат. Пожалуйста, введите ДД.MM.YYYY:")
            return bot.register_next_step_handler(msg, lambda m: handle_date_text(m, product_name))

        supabase.table("products").insert({
            "id": str(uuid.uuid4()),
            "user_id": str(chat_id),
            "name": product_name,
            "expiry": exp_date.isoformat()
        }).execute()

        bot.send_message(chat_id, f"✅ *{product_name}* до {exp_date.strftime('%d.%m.%Y')} добавлен!", parse_mode='Markdown', reply_markup=menus.main_menu())

    def handle_date_photo(message, product_name):
        chat_id = message.chat.id
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded = bot.download_file(file_info.file_path)

        url = 'https://api.ocr.space/parse/image'
        payload = {
            'apikey': OCR_API_KEY,
            'isOverlayRequired': False,
        }
        files = {
            'file': ('image.jpg', downloaded)
        }
        response = requests.post(url, data=payload, files=files)
        result = response.json()

        parsed_text = '\n'.join([r.get('ParsedText', '') for r in result.get('ParsedResults', [])])
        print(parsed_text)

        text = '\n'.join([r.get('ParsedText', '') for r in result.get('ParsedResults', [])])
        raw_matches = re.findall(r"(\d{2}[.\-/]\d{2}[.\-/][\dA-Za-z]{2,6})", text)
        dates = []

        print(raw_matches)
        
        for raw in raw_matches:
            cleaned = re.sub(r"[^0-9.]", "", raw)
            parts = cleaned.split('.')
            if len(parts) != 3:
                continue
            day, month, year = parts
            if len(year) == 2:
                year = '20' + year
            elif len(year) == 3:
                year = year[:2]
            try:
                dt = datetime.datetime.strptime(f"{day}.{month}.{year}", "%d.%m.%Y").date()
                dates.append(dt)
            except ValueError:
                continue
                
        if not dates:
            msg = bot.send_message(chat_id, "❌ Не удалось распознать дату. Попробуйте еще раз или введите вручную:")
            markup = types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton('⌨️ Ввести вручную', callback_data=f"date_text|{product_name}")
            )
            bot.send_message(chat_id, "Выберите альтернативный способ ввода:", reply_markup=markup)
            return

        exp_date = max(dates)

        save_product(chat_id, product_name, exp_date)
        bot.send_message(chat_id, f"✅ *{product_name}* до {exp_date.strftime('%d.%m.%Y')} добавлен!", parse_mode='Markdown', reply_markup=menus.main_menu())

    def save_product(chat_id, product_name, exp_date):
        supabase.table("products").insert({
            "id": str(uuid.uuid4()),
            "user_id": str(chat_id),
            "name": product_name,
            "expiry": exp_date.isoformat()
        }).execute()

    def show_delete_menu(bot, user_id, message):
        resp = supabase.table("products").select("*").eq("user_id", user_id).execute()
        items = resp.data or []
        if not items:
            bot.send_message(user_id, "📭 Список продуктов пуст", reply_markup=menus.main_menu())
            return
        markup = types.InlineKeyboardMarkup()
        for item in items:
            text = f"❌ {item['name']} ({item['expiry']})"
            markup.add(types.InlineKeyboardButton(text, callback_data=f"delete_{item['id']}"))
        markup.add(types.InlineKeyboardButton("↩️ Назад", callback_data='main_menu'))
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.message_id,
            text="🗑️ Выберите продукт для удаления:",
            reply_markup=markup
        )

    def delete_product(bot, user_id, call):
        product_id = call.data.split('_', 1)[1]
        original = storage.products.get(user_id, [])
        supabase.table("products").delete().eq("id", product_id).eq("user_id", user_id).execute()
        bot.answer_callback_query(call.id, "Продукт успешно удален!")
        show_delete_menu(bot, user_id, call.message)

    def show_product_list(bot, user_id, message):
        resp = supabase.table("products").select("name,expiry").eq("user_id", user_id).order("expiry", desc=False).execute()  # :contentReference[oaicite:6]{index=6}
        items = resp.data or []
        if items:
            lines = [f"• *{p['name']}* до {p['expiry']}" for p in items]
            text = "📦 *Ваши продукты:*\n" + "\n".join(lines)
        else:
            text = "📭 Список продуктов пуст"
        markup = types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("↩️ Назад", callback_data='main_menu')
        )
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.message_id,
            text=text,
            parse_mode='Markdown',
            reply_markup=markup
        )

    def check_expired_products(bot, user_id, message):
        today = datetime.date.today().isoformat()
        resp = supabase.table("products").select("name,expiry").eq("user_id", user_id).lt("expiry", today).execute()  # :contentReference[oaicite:7]{index=7}
        expired = [f"{i['name']} ({i['expiry']})" for i in (resp.data or [])]
        text = ("🚨 *Просроченные продукты:*\n" + "\n".join(expired)) if expired else "✅ Просроченных продуктов нет!"
        markup = types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("↩️ Назад", callback_data='main_menu')
        )
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.message_id,
            text=text,
            parse_mode='Markdown',
            reply_markup=markup
        )
