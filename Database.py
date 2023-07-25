import sqlite3

class Database:
    def __init__(self):
        self.con = sqlite3.connect("data.db")
        self.cur = self.con.cursor()
        self.cur.execute("CREATE TABLE IF NOT EXISTS data(id INTEGER PRIMARY KEY AUTOINCREMENT, match STRING, unix_time INTEGER UNIQUE)")

    def insert_match(self, time, match):
        self.cur.execute("INSERT INTO data ( match, unix_time ) VALUES( ?, ? )", (match, time, ))
        self.con.commit()

    def check_existing(self, time):
        res = self.cur.execute("SELECT match, unix_time FROM data WHERE unix_time = ?", (time, ))
        return res.fetchall()