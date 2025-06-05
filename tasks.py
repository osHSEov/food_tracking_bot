
import time
import datetime
from threading import Thread
import storage
import menus
from config import supabase

def start_background(bot):
    def _check_loop():
        while True:
            today = datetime.date.today().isoformat()
            resp = supabase.table("products").select("user_id,name,expiry").lt("expiry", today).execute()
            for item in (resp.data or []):
                bot.send_message(
                    item["user_id"],
                    f"🚨 Просроченные продукты:\n• {item['name']} ({item['expiry']})",
                    reply_markup=menus.main_menu()
                )
            time.sleep(86400)

    Thread(target=_check_loop, daemon=True).start()
