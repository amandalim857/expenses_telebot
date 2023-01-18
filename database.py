import sqlite3

class DatabaseManager():
    def __init__(self, db):
        self.db = db
        
    def create_databases(self):
        conn = sqlite3.connect(self.db)
        cur = conn.cursor()
        # dont needa commit aft every execute, just do at end

        cur.execute("""CREATE TABLE IF NOT EXISTS expenses(
            expenseid INTEGER PRIMARY KEY,
            userid TEXT NOT NULL,
            title TEXT NOT NULL,
            amount REAL NOT NULL,
            paymentmode TEXT NOT NULL,
            date TEXT,
            remarks TEXT,
            FOREIGN KEY(userid) REFERENCES users(userid)
            );
            """)
        conn.commit()

    def insert_userid(self, conn, cur, userid):
        cur.execute("INSERT OR IGNORE INTO users VALUES (?);", (userid,))
        conn.commit()

    def insert_expense(self, conn, cur, expense):
        cur.execute("INSERT INTO expenses VALUES(NULL, ?, ?, ?, ?, ?, ?);", (expense))
        conn.commit()
    
    def retrieve_topten_data(self, cur, userid):
        cur.execute("""SELECT * FROM expenses 
                    WHERE userid == ? 
                    LIMIT 10""", (userid,))
        data = cur.fetchall()
        return data
    
    def retrieve_user_data(self, cur, userid):
        # cur.execute("SELECT * FROM expenses")
        cur.execute("SELECT * FROM expenses WHERE userid == ?", (userid,))
        data = cur.fetchall()
        return data
    
    def has_entries(self, cur):
            cur.execute("SELECT COUNT(*) FROM expenses")
            result = cur.fetchall()
            if result[0][0] > 0:
                return True
            return False

    def delete_last_expense(self, conn, cur):
        if self.has_entries(cur):
            cur.execute("DELETE FROM expenses WHERE expenseid = (SELECT MAX(expenseid) FROM expenses);")
            conn.commit()

    # def retrieve_expense(self, conn, cur, expenseid):
    #     if self.has_entries(cur):
    #         cur.execute("SELECT expenseid, FROM expenses WHERE expenseid == ? AND userid == ",(expenseid,))
    #         conn.commit()

    # def delete_expense(self, conn, cur, expenseid):
    #     if self.has_entries(cur):
    #         cur.execute("DELETE FROM expenses WHERE expenseid == ?",(expenseid,))
    #         conn.commit()

    def drop(self, cur):
        cur.execute("DROP TABLE IF EXISTS users;")
        cur.execute("DROP TABLE IF EXISTS expenses;")
    
    def close(self, conn):
        conn.close()
