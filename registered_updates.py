import pandas as pd
import sqlite3
from sqlite3 import Error
from flask import Flask, request, jsonify, abort
import threading
from telegram import ParseMode

CLIENT_DB = "registeredClients.db"
app = Flask(__name__)

@app.route('/api/update/<token>', methods=['POST'])
def update(token):
    try:
        content = request.get_json(silent=True)
        msg = content["update_message"]
        user_updater.send_update_message(token, msg)
    except Exception as e:
        abort(500, e)
    
    return "ok"

def flaskthread():
    app.run(host='0.0.0.0', threaded=True)

class UserUpdates(object):
    def register(self, telegram_id, device_token):
        conn, cur = self.get_db_conn()
        with conn:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS registered (
                    device_token INTEGER PRIMARY KEY,
                    telegram_id TEXT NOT NULL
                );
            """)
            # The first command will insert the record. If the record exists, it will ignore the error caused by the conflict with an existing primary key.
            cur.execute("INSERT OR IGNORE INTO registered (device_token, telegram_id) VALUES ({}, '{}');".format(device_token, telegram_id))
            cur.execute("UPDATE registered SET telegram_id='{}' WHERE device_token={};".format(telegram_id, device_token))

    def unregister(self, telegram_id, device_token):
        conn, cur = self.get_db_conn()
        cur.execute("DELETE FROM registered WHERE device_token={} AND telegram_id='{}';".format(device_token, telegram_id))

    def get_telegram_id(self, device_token):
        conn, cur = self.get_db_conn()
        result = pd.read_sql('select * from registered where device_token={}'.format(device_token), conn)
        if not result.empty:
            return result.telegram_id[0]
        else:
            return None

    def get_db_conn(self):
        conn = sqlite3.connect(CLIENT_DB)
        cur = conn.cursor()
        return conn, cur

    def send_update_message(self, device_token, msg):
        chat_id = self.get_telegram_id(device_token)
        if chat_id is not None:
            self.bot.send_message(chat_id=chat_id, text=msg, parse_mode=ParseMode.MARKDOWN)


    def start_api_server(self, bot):
        self.bot = bot
        threading.Thread(target=flaskthread).start()

user_updater = UserUpdates()