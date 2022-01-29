import sqlite3
import time


class DataBase:
    def __init__(self, database):
        self.connection = sqlite3.connect(database)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()

    def register(self, symbol, value, dollar, leverage, stop_counter, percent_counter):
        with self.connection as con:
            con.execute("INSERT INTO symbols (symbol, price, dollar, leverage, stop_counter, percent_counter) ""VALUES (?, ?, ?, ?, ?, ?)",
                        (symbol, value, dollar, leverage, stop_counter, percent_counter))

    def new_value(self, symbol, value, dollar, leverage, stop_counter, percent_counter):
        with self.connection:
            self.cursor.execute("UPDATE symbols SET price=? WHERE symbol=?", (value, symbol,))
            self.cursor.execute("UPDATE symbols SET dollar=? WHERE symbol=?", (dollar, symbol,))
            self.cursor.execute("UPDATE symbols SET counter=? WHERE symbol=?", (0, symbol,))
            self.cursor.execute("UPDATE symbols SET leverage=? WHERE symbol=?", (leverage, symbol,))
            self.cursor.execute("UPDATE symbols SET stop_counter=? WHERE symbol=?", (stop_counter, symbol,))
            self.cursor.execute("UPDATE symbols SET percent_counter=? WHERE symbol=?", (percent_counter, symbol,))

    def null_counter(self, symbol):
        with self.connection:
            self.cursor.execute("UPDATE symbols SET counter=? WHERE symbol=?", (0, symbol,))

    def new_price(self, symbol, value):
        with self.connection:
            self.cursor.execute("UPDATE symbols SET price=? WHERE symbol=?", (value, symbol,))

    def new_counter(self, symbol, counter_value):
        with self.connection:
            self.cursor.execute("UPDATE symbols SET counter=? WHERE symbol=?", (counter_value, symbol,))

    def delete(self, symbol):
        with self.connection:
            self.cursor.execute("DELETE FROM symbols WHERE symbol=?", (symbol,))

    def get_symbols(self):
        final_dict = {}
        with self.connection:
            row_list = self.cursor.execute("SELECT * FROM symbols").fetchall()
            for i in row_list:
                final_dict[list(i)[1]] = [list(i)[2], list(i)[3], list(i)[4], list(i)[5], list(i)[6], list(i)[7]]
            return final_dict

    def check_symbol(self, symbol):
        with self.connection:
            result = self.cursor.execute("SELECT id FROM symbols WHERE symbol=?", (symbol,)).fetchone()

            if result is not None:
                return True
            else:
                return False


if __name__ == '__main__':
    timer = time.time()
    db = DataBase('db.db')

    print(db.get_symbols())
    print(f"Прошло - {time.time() - timer} секунд")
