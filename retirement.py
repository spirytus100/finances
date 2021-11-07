from datetime import datetime
import texttable

class Retirement:

    def __init__(self, connection):
        self.connection = connection

    def add_position(self):
        item = input("Nazwa: ")
        cost = input("Kwota: ")

        try:
            cost = float(cost)
        except ValueError:
            print("Błędny format liczby.")
            return False

        date = datetime.now()

        connection = self.connection
        sql_insert = "INSERT INTO retirement VALUES (?, ?, ?)"
        connection.execute(sql_insert, (date, item, cost))
        connection.commit()

    def update_position(self, idnum, column):
        if column not in ("item", "cost"):
            print("Nie ma takiej kolumny.")
            return False

        idnum = self.verify_id(idnum, "retirement")
        if idnum:
            new_value = input("Podaj nową wartość: ")
            if column == "cost":
                try:
                    new_value = float(new_value)
                except ValueError:
                    print("Błędny format liczby.")
                    return False

            connection = self.connection
            sql_update = "UPDATE retirement SET " + column + " = ?"
            connection.execute(sql_update, (new_value,))
            connection.commit()
            print("Pozycja została zaktualizowana.")

    def delete_position(self, idnum):
        idnum = self.verify_id(idnum, "retirement")
        if not idnum:
            return False
        question = input("Czy na pewno usunąć pozycję o numerze id "+str(idnum)+" ? ")
        if question != "y":
            return print("Pozycja nie została usunięta.")
        connection = self.connection
        sql_delete = "DELETE FROM retirement WHERE rowid = ?"
        connection.execute(sql_delete, (idnum,))
        connection.commit()
        print("Pozycja została usunięta.")

    def format_row(self, row, space1, space2, space3):
        s1, s2, s3 = (space1-len(str(row[0])))*" ", (space2-len(str(row[1])))*" ", (space3-len(str(row[2])))*" "
        return print(row[0], s1, row[1], s2, row[2], s3, row[3])

    def show_positions(self):
        connection = self.connection
        sql_select = "SELECT rowid, date, item, cost FROM retirement"
        cursor = connection.execute(sql_select)
        for row in cursor:
            self.format_row(row, 4, 27, 40)

    def verify_id(self, idnum, table):
        try:
            idnum = int(idnum)
        except ValueError:
            return False
        else:
            connection = self.connection
            sql_select = "SELECT rowid FROM " + table + " WHERE rowid = ?"
            cursor = connection.execute(sql_select, (idnum,))
            record = cursor.fetchone()
            if not record:
                print("Podany numer id nie istnieje.")
                return False
            return idnum

    def notify_investment(self, date, item, cost, transaction):
        if transaction == "buy":
            cost = 0 - cost

        connection = self.connection
        sql_insert = "INSERT INTO retirement VALUES (?, ?, ?)"
        connection.execute(sql_insert, (date, item, cost))
        connection.commit()

    def show_investments(self, over=False):
        connection = self.connection
        if over:
            sql_select = """SELECT inv.name, inv.buy_date, inv.amount * inv.buy_price, inv.profit + SUM(inter.interest) 
                            FROM investments as inv JOIN interest as inter ON inv.investment_id = inter.investment_id 
                            WHERE inv.retirement = 1 AND inv.is_over = 1 
                            GROUP BY inter.name"""
            headers = [["nazwa", "data kupna", "kwota", "zysk"]]
        else:
            sql_select = "SELECT name, buy_date, amount * buy_price FROM investments WHERE retirement = 1 AND is_over = 0"
            headers = [["nazwa", "data kupna", "kwota"]]

        cursor = connection.execute(sql_select)
        
        retirement_list = headers + list(cursor)
        retirement_table = texttable.Texttable(max_width=0)
        retirement_table.add_rows(retirement_list)
        print(retirement_table.draw())


    def count_balance(self):
        connection = self.connection
        inflow = []
        cursor = connection.execute("SELECT cost FROM retirement")
        for row in cursor:
            inflow.append(row[0])

        cursor = connection.execute("SELECT amount * buy_price FROM investments WHERE retirement = 1 AND is_over = 0")
        current_investments = []
        for row in cursor:
            current_investments.append(row[0])

        cursor = connection.execute("SELECT amount * buy_price, profit FROM investments WHERE retirement = 1 AND is_over = 1")
        profit = []
        finished = []
        for row in cursor:
            finished.append(row[0])
            profit.append(row[1])

        cursor = connection.execute("SELECT name FROM investments WHERE category LIKE 'obligacje%' AND retirement = 1")
        interest_sum = 0.0
        for row in cursor:
            bond_name = row[0]
            cursor = connection.execute("SELECT interest FROM interest WHERE name = ?", (bond_name,))
            bond_interest = sum([row[0] for row in cursor])
            interest_sum += bond_interest

        retirement_all = sum(inflow) + sum(profit) + sum(current_investments)
        retirement_all = round(retirement_all, 2)

        cash = sum(inflow) + sum(profit) - sum(current_investments)
        cash = round(cash, 2)

        table_list = [
                        ["gotówka", str(cash)], 
                        ["trwające inwestycje", str(sum(current_investments))],
                        ["wszystkie inwestycje", str(sum(finished) + sum(current_investments))],
                        ["całkowity zysk kapitałowy", str(sum(profit) + interest_sum)],
                        ["suma", str(retirement_all)],
                    ]

        table_list = [["kategoria", "suma"]] + table_list
        table_obj = texttable.Texttable(max_width=0)
        table_obj.add_rows(table_list)
        print(table_obj.draw())



        




