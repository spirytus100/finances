from datetime import datetime
from sqlite3 import Error

class Claim:

    def __init__(self, connection):
        self.connection = connection

    def add_claim(self, item, cost):
        connection = self.connection
        date = datetime.now()
        sql_insert = "INSERT INTO claims VALUES (?, ?, ?)"
        connection.execute(sql_insert, (date, item, cost))
        connection.commit()
        print("Pozycja została dodana.")

    def show_claims(self):
        connection = self.connection
        sql_select = "SELECT rowid, date, item, cost FROM claims"
        cursor = connection.execute(sql_select)
        for row in cursor:
            print(row[0], row[1], row[2], row[3], "zł")

    def delete_claim(self, idnum):
        question = input("Czy na pewno usunąć pozycję o numerze id "+idnum+" ? ")
        if question != "y":
            return print("Pozycja nie została usunięta.")
        connection = self.connection
        sql_delete = "DELETE FROM claims WHERE rowid = ?"
        connection.execute(sql_delete, (idnum,))
        connection.commit()
        print("Pozycja została usunięta.")

    def update_claim(self, idnum, column):
        if column not in ("item", "cost"):
            return print("Nie ma takiej kolumny.")

        elif column == "item":
            new_value = input("Podaj nową wartość: ")
        elif column == "cost":
            new_value = input("Podaj nową wartość: ")
            try:
                new_value = float(new_value)
            except ValueError:
                return print("Błędna wartość.")

        connection = self.connection
        sql_update = "UPDATE claims SET " + column + " = ? WHERE rowid = ?"
        try:
            connection.execute(sql_update, (new_value, idnum))
            connection.commit()
        except Error:
            print("Błąd zapisu do bazy danych.")
        else:
            print("Pozycja została zaktualizowana.")

    def count_balance(self):
        connection = self.connection
        sql_select = "SELECT cost FROM claims"
        cursor = connection.execute(sql_select)
        balance = 0.0
        for row in cursor:
            balance = balance + row[0]

        print("Aktualne saldo wynosi", round(balance, 2), "zł.")






























