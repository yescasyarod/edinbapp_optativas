import sqlite3
class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
    def run_query(self, query, params=(), fetch="none"):
        try:
            with self.conn:
                self.cursor.execute(query, params) 
                if query.strip().upper().startswith(("INSERT", "UPDATE", "DELETE")):
                    return self.cursor.rowcount
                if fetch == "one":
                    return self.cursor.fetchone()
                elif fetch == "all":
                    return self.cursor.fetchall()     
        except sqlite3.Error as e:
            print(f"Error en la consulta: {e}")
            return None
    def close(self):
        if self.conn:
            self.conn.close()