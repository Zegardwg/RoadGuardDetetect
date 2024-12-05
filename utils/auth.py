import json
import os

USER_DATA_FILE = 'user_data.json'

def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_user_data(user_data):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(user_data, f)

def register_user(username, password):
    user_data = load_user_data()
    if username in user_data:
        return False  # Username already exists
    user_data[username] = password
    save_user_data(user_data)
    return True

def authenticate_user(username, password):
    user_data = load_user_data()
    return user_data.get(username) == password