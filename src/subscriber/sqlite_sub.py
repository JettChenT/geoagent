from . import Subscriber
import sqlite3
import datetime


class SQLiteSubscriber(Subscriber):
    def __init__(self, db_path: str = "logs/analytics.db"):
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, type TEXT, message TEXT, timestamp TEXT)")
        conn.commit()
        self.db_path = db_path

    def push(self, msg_type, msg):
        timestamp = datetime.datetime.now().isoformat()
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("INSERT INTO messages (type, message, timestamp) VALUES (?, ?, ?)",
                         (msg_type, str(msg), timestamp))
        conn.commit()
