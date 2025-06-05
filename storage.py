# storage.py

import json
import uuid
from config import DATA_FILE

products = {}

def load_data():
    global products
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            old = json.load(f)
        for user_id, user_data in old.items():
            if isinstance(user_data, dict):
                lst = []
                for name, expiry in user_data.items():
                    lst.append({
                        'id': str(uuid.uuid4()),
                        'name': name,
                        'expiry': expiry
                    })
                products[user_id] = lst
            else:
                products[user_id] = user_data
    except FileNotFoundError:
        products = {}
    except Exception as e:
        print(f"Ошибка при загрузке данных: {e}")
        products = {}

def save_data():
    """Сохраняет текущий словарь products в DATA_FILE."""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

load_data()
