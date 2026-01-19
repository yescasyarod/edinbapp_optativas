import sqlite3

class Database:
    def __init__(self, db_path):
        self.db_path = db_path

        # timeout ayuda a esperar locks si el otro proceso está escribiendo
        self.conn = sqlite3.connect(db_path, check_same_thread=False, timeout=3.0)
        self.cursor = self.conn.cursor()

        # ✅ Mejor convivencia multi-proceso (una app escribe, otra lee)
        try:
            self.conn.execute("PRAGMA journal_mode=WAL;")
            self.conn.execute("PRAGMA synchronous=NORMAL;")
            self.conn.execute("PRAGMA busy_timeout=3000;")  # ms
        except Exception as e:
            print(f"[WARN] PRAGMAs fallaron: {e}")

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