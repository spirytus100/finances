from sqlite3 import Error
import csv
import datetime

# todo funkcja formatująca wyniki z bazy danych wyświetlane w oknie wiersza poleceń


class DBQueries:

    def __init__(self, connection):
        self.connection = connection
        self.columns = {"name": ("nazwa instrumentu", str), "category": ("kategoria inwestycyjna", str),
                        "financial_institution": ("instytucja finansowa", str), "buy_date": ("data kupna", None),
                        "amount": ("ilość", float), "buy_price": ("cena kupna", float), "buy_comission": ("prowizja za kupno", float),
                        "retirement": ("emerytura", None), "sell_date": ("data sprzedaży", None), "sell_price": ("cena sprzedaży", float),
                        "sell_commission": ("prowizja za sprzedaż", float), "profit": ("zysk", float),
                        "is_over": ("zakończona", None)}

        self.asset_categories = ("akcje polskie", "akcje zagraniczne", "obligacje skarbowe polskie",
                                 "obligacje korporacyjne polskie", "obligacje zagraniczne", "kryptowaluty", "surowce",
                                 "depozyty")

        self.financial_institutions = ("DM mBank", "BM PKO Bank Polski", "BM Santander", "Degiro", "XTB", "mBank",
                                       "Getin Bank", "Idea Bank")

    def find_investment_by_id(self, idnum):
        connection = self.connection
        sql_select = "SELECT * FROM investments WHERE rowid = ?"
        cursor = connection.execute(sql_select, (idnum,))
        record = cursor.fetchone()
        if record == []:
            print("Podany numer id nie istnieje.")
        else:
            self.print_investment_details(record)
            return record

    def find_investment_by_name(self, input_name, show=True):
        connection = self.connection
        sql_select = "SELECT * FROM investments WHERE name = ?"
        sql_select_like = '''SELECT name FROM investments WHERE name LIKE "%'''+input_name+'''%";'''
        cursor = connection.execute(sql_select, (input_name,))
        investment = cursor.fetchone()

        name, investment_id, category = None, None, None
        if investment:
            name = investment[0]
            investment_id = investment[1]
            category = investment[2]
            if show:
                self.print_investment_details(investment)
        else:
            printed = False
            cursor = connection.execute(sql_select_like)
            for row in cursor:
                if not printed:
                    print("Znaleziono podobne nazwy inwestycji:")
                print(row[0])
                printed = True

            if not printed:
                print("Nie znaleziono inwestycji.")
                return name, investment_id, category

            input_name = input("Podaj nazwę inwestycji: ")
            self.find_investment_by_name(input_name, show=True)

        return name, investment_id, category

    def print_investment_details(self, record):
        bools = []
        for el in (record[8], record[13]):
            if el == 1:
                bools.append("Tak")
            elif el == 0:
                bools.append("Nie")
            else:
                bools.append(el)

        invested = record[5] * record[6] + record[7] + record[11]
        print("\n")
        print("Nazwa instrumentu:", record[0])
        print("Kategoria inwestycyjna:", record[2])
        print("Instytucja finansowa:", record[3])
        print("Data kupna:", record[4])
        print("Ilość:", record[5])
        print("Cena kupna:", record[6])
        print("Prowizja za kupno:", record[7])
        print("Emerytura:", bools[0])
        print("Data sprzedaży:", record[9])
        print("Cena sprzedaży:", record[10])
        print("Prowizja za sprzedaż:", record[11])
        if "obligacje" in record[0]:
            interest = self.count_bond_interest(record[0])
            print("Odsetki:", interest)
        if bools[1] == "Tak":
            print("Zysk:", record[12])
            print("Zysk %:", round((record[12] / invested) * 100, 2))
            td = record[9] - record[4]
            print("Zysk w skali roku:", round(record[12] / (td.days / 365), 2))
            print("Zysk % z uwzględnieniem inflacji:", round(self.count_inflation(record[4], record[9], record[12])/invested*100, 2))
        print("Zakończona:", bools[1])
        print(record[12])

    def find_investments_by_category(self, category, all=False):
        connection = self.connection
        if not all:
            sql_select = "SELECT rowid, name FROM investments WHERE category = ?"
            values = (category,)
        else:
            sql_select = "SELECT rowid, name FROM investments WHERE category = ? AND is_over = ?"
            values = (category, 1)
        cursor = connection.execute(sql_select, values)
        #if cursor:
        for row in cursor:
            print(row[0], row[1])
        #else:
            #print("Dla podanej kategorii brak rekordów w bazie danych.")

    def update_record(self, idnum):
        column = input("Podaj kolumnę, która ma być aktualizowana: ")
        found = False

        for key, val in self.columns.items():
            if column == key or column == val[0]:
                if key == "retirement" or key == "is_over":
                    new_value = input("Podaj nową wartość (y/n): ")
                else:
                    new_value = input("Podaj nową wartość: ")
                column = key
                found = True
                if val[1] is not None:
                    try:
                        new_value = val[1](new_value)
                    except ValueError:
                        return print("Błędny format liczby w polu", val[0])
                    else:
                        if key == "category" and new_value not in self.asset_categories:
                            return print("Błędna kategoria inwestycyjna.")
                        elif key == "financial_institution" and new_value not in self.financial_institutions:
                            return print("Błędna instytucja finansowa.")
                else:
                    if key == "buy_date" or key == "sell_date":
                        try:
                            new_value = datetime.datetime.strptime(new_value, "%d-%m-%Y")
                        except ValueError:
                            return print("Błędny format daty w polu", val[0])
                    else:
                        if key == "retirement" or key == "is_over":
                            if new_value == "y":
                                new_value = True
                            elif new_value == "n":
                                new_value = False
                            else:
                                return print("Błędna wartość logiczna w polu", val[0])
        if not found:
            return print("Błędna nazwa kolumny.")

        sql_update = "UPDATE investments SET " + column + " = ? WHERE rowid = ?"
        try:
            connection = self.connection
            cursor = connection.execute("SELECT name FROM investments WHERE rowid = ?", (idnum,))
            record = cursor.fetchone()
            if record:
                connection.execute(sql_update, (new_value, idnum))
                connection.commit()
            else:
                return print("Podany numer id nie istnieje.")
        except Error:
            print("Błąd zapisu do bazy danych.")
        else:
            print("Rekord bazy danych został zaktualizowany.")
            self.find_investment_by_id(idnum)

    def delete_record(self, idnum):
        print("Inwestycja zostanie usunięta z bazy danych.")
        answer = input("Czy jesteś pewien (y/n)? ")
        if answer != "y":
            return print("Inwestycja nie została usunięta z bazy danych.")

        connection = self.connection
        sql_select_statement = "SELECT name FROM investments WHERE rowid = ?"
        cursor = connection.execute(sql_select_statement, (idnum,))
        record = cursor.fetchone()
        if not record:
            return print("Brak podanego numeru id w bazie danych.")

        sql_delete_statement = "DELETE FROM investments WHERE rowid = ?"
        connection.execute(sql_delete_statement, (idnum,))
        connection.commit()
        print("Inwestycja została usunięta z bazy danych.")

    def count_bond_interest(self, instrument_name):
        connection = self.connection
        sql_select = "SELECT date, interest FROM interest WHERE name = ?"
        cursor = connection.execute(sql_select, (instrument_name,))
        if cursor != []:
            interest_sum = 0.0
            for row in cursor:
                print(row[0], row[1])
                interest_sum += row[1]
            return interest_sum
        else:
            print("Dla podanego instrumentu nie znaleziono odsetek w bazie danych.")
            return False

    def count_average_absolute_profit_by_category(self, category):
        connection = self.connection
        sql_select = "SELECT profit FROM investments WHERE category = ? AND is_over = 1"
        cursor = connection.execute(sql_select, (category,))
        profit_sum = 0.0
        i = 0
        for row in cursor:
            i += 1
            profit_sum += row[0]
        if i > 0:
            profit_avg = round(profit_sum / i, 2)
            print("Średni absolutny zysk dla kategorii", category, "wynosi", profit_avg, "zł.")
        else:
            print("Brak zakończonych inwestycji dla podanej kategorii.")

    def count_average_percentage_profit_by_category(self, category):
        connection = self.connection
        sql_select = "SELECT amount, buy_price, buy_comission, sell_comission, profit FROM investments WHERE category = ? AND is_over = 1"
        cursor = connection.execute(sql_select, (category,))
        profits_perc = []
        for row in cursor:
            profit_percentage = row[4] / (row[0] * row[1] + row[2] + row[3]) * 100
            profits_perc.append(profit_percentage)

        if profits_perc != []:
            profit_avg = round(sum(profits_perc) / len(profits_perc), 2)
            print("Średni procentowy zysk dla kategorii", category, "wynosi", str(profit_avg) + "%.")
        else:
            print("Brak zakończonych inwestycji dla podanej kategorii.")

    def count_average_profit(self, parameter):
        connection = self.connection

        if parameter == "retirement":
            sql_select = "SELECT amount, buy_date, buy_price, buy_comission, sell_date, sell_comission, interest, profit " \
                         "FROM investments WHERE retirement = 1 AND is_over = 1"
        elif parameter == "non-retirement":
            sql_select = "SELECT amount, buy_date, buy_price, buy_comission, sell_date, sell_comission, interest, profit " \
                         "FROM investments WHERE retirement = 0 AND is_over = 1"
        elif parameter == "all":
            sql_select = "SELECT amount, buy_date, buy_price, buy_comission, sell_date, sell_comission, interest, profit " \
                         "FROM investments WHERE is_over = 1"
        else:
            return print("Błędny parametr.")

        cursor = connection.execute(sql_select)
        if cursor is not None:
            profit_sum = 0.0
            y_profit_sum = []
            perc_profit_sum = []
            i = 0
            for row in cursor:
                i += 1
                profit = row[6] + row[7]
                perc_profit = profit / (row[0] * row[2] + row[3] + row[5])
                perc_profit_sum.append(perc_profit)
                td = row[4] - row[1]
                y_profit = (profit / (row[0] * row[2] + row[3] + row[5])) / td.days
                y_profit_sum.append(y_profit)
                profit_sum += row[6] + row[7]

            print("Średni zysk:", round(profit_sum / i, 2))
            print("Średni zysk %:", round(sum(perc_profit_sum) / i, 2))
            print("Średni zysk roczny:", round(sum(y_profit_sum) / i, 2))
        else:
            print("Brak zakończonych inwestycji.")

    def count_inflation(self, buy_date, sell_date, profit):

        with open("inflacja_gus.csv", "r") as fo:
            csv_reader = csv.reader(fo, delimiter=";")
            year_inflation = []
            remain_inflation = []
            for i, row in enumerate(csv_reader):
                if i > 0:
                    if sell_date.month < buy_date.month:
                        if sell_date.year > int(row[0]) > buy_date.year and int(row[1]) == buy_date.month:
                            year_inflation.append(float(row[2].replace(",", ".")))
                        if int(row[0]) == sell_date.year and buy_date.month >= int(row[1]) > sell_date.month:
                            remain_inflation.append(float(row[2].replace(",", ".")))
                    else:
                        if sell_date.year >= int(row[0]) > buy_date.year and int(row[1]) == buy_date.month:
                            year_inflation.append(float(row[2].replace(",", ".")))

        total_y = 1
        for i in range(0, len(year_inflation)):
            total_y = total_y * year_inflation[i]
        total_y = (total_y / 10000 - 100) / 100

        total_r = 0
        sum_weight = 0
        print(remain_inflation)
        for i in range(1, len(remain_inflation)+1):
            total_r = total_r + remain_inflation[i-1] * i
            sum_weight = sum_weight + i
        exp_avg = (total_r / sum_weight - 100) * len(remain_inflation) / 12 / 100

        profit_after_inflation = profit - total_y * profit - (exp_avg * (profit - total_y * profit))
        profit_after_inflation = round(profit_after_inflation, 2)
        return profit_after_inflation






















