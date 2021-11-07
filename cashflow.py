import datetime
import texttable


class Cashflow:

    def __init__(self, connection):
        self.connection = connection

    def get_input(self):
        title = input("Podaj tytuł pozycji: ")
        category = input("Podaj kategorię: ")
        if category not in ("oszczędności", "wycofanie", "zysk kapitałowy"):
            print("Błędna kategoria.")
            return False
        value = input("Podaj kwotę: ")
        try:
            value = float(value)
        except ValueError:
            print("Błędny format liczby.")
            return False

        return title, category, value

    def save_position(self, data_tuple):
        title = data_tuple[0]
        category = data_tuple[1]
        value = data_tuple[2]

        connection = self.connection
        sql_insert = "INSERT INTO cashflow VALUES (?, ?, ?, ?)"
        values = (datetime.datetime.now(), title, category, value)
        connection.execute(sql_insert, values)
        connection.commit()
        print("Pozycja została zapisana.")

    def verify_id(self, idnum):
        try:
            idnum = int(idnum)
        except ValueError:
            print("Błędny parametr.")
            return False
        else:
            connection = self.connection
            cursor = connection.execute("SELECT rowid FROM cashflow")
            id_set = set(map(lambda x: x[0], list(cursor)))
            if idnum not in id_set:
                print("Błędny parametr.")
                return False
            return idnum

    def update_position(self, idnum):
        idnum = self.verify_id(idnum)
        if not idnum:
            return

        column = input("Podaj kolumnę, której wartość ma być zaktualizowana: ")

        columns = {"title": "tytuł", "category": "kategoria", "value": "wartość"}
        found = False
        for key, val in columns.items():
            if key == column or val == column:
                column = key
                found = True
                break
        if not found:
            return print("Błędna kolumna.")

        new_value = input("Podaj nową wartość: ")

        if column == "category" and new_value not in ("oszczędności", "wycofanie", "zysk kapitałowy"):
            return print("Błędna kategoria.")

        if column == "value":
            try:
                new_value = int(new_value)
            except ValueError:
                return print("Błędny format liczby.")

        sql_update = "UPDATE cashflow SET " + column + " = ? WHERE rowid = ?"
        connection = self.connection
        connection.execute(sql_update, (new_value, idnum))
        connection.commit()
        print("Pozycja została zaktualizowana.")

    def delete_position(self, idnum):
        idnum = self.verify_id(idnum)
        if not idnum:
            return

        answer = input("Czy na pewno chcesz usunąć pozycję o numerze id " + str(idnum) + " (y/n)? ")
        if answer != "y":
            return

        sql_delete = "DELETE FROM cashflow WHERE rowid = ?"
        connection = self.connection
        connection.execute(sql_delete, (idnum,))
        connection.commit()
        print("Pozycja została usunięta.")

    def print_positions(self, parameter=None):
        connection = self.connection
        if parameter is None:
            sql_select = "SELECT rowid, date, title, category, value FROM cashflow"
            cursor = connection.execute(sql_select)
        else:
            try:
                parameter = int(parameter)
            except ValueError:
                return print("Błędny parametr.")
            else:
                datefrom = datetime.datetime(year=parameter, month=1, day=1)
                sql_select = "SELECT rowid, date, title, category, value FROM cashflow WHERE date >= ?"
                cursor = connection.execute(sql_select, (datefrom,))

        for row in cursor:
            print(row[0], row[1], row[2], (40-len(row[2]))*" ", row[3], (20-len(row[3]))*" ", row[4])

    def count_balance(self):
        connection = self.connection
        sql_select = "SELECT value FROM cashflow"
        cursor = connection.execute(sql_select)
        values = set(map(lambda x: x[0], list(cursor)))
        saldo = round(sum(values) + 53598.24, 2)
        return saldo

    def count_cash(self):
        connection = self.connection
        sql_inv_select = "SELECT amount * buy_price + buy_comission FROM investments WHERE is_over = 0"
        cursor = connection.execute(sql_inv_select)
        sum_investment = sum(map(lambda x: x[0], list(cursor)))
        cash = self.count_balance() - sum_investment
        print("Wolna gotówka:", round(cash, 2), "zł")
        return cash

    def analyze_cashflow(self):
        connection = self.connection
        sql_select = "SELECT date, category, value FROM cashflow ORDER BY date ASC"
        cursor = connection.execute(sql_select)
        cashflow_dict = {}
        for row in cursor:
            if row[0].year not in cashflow_dict.keys():
                months = {row[0].month: row[2]}
                cashflow_dict[row[0].year] = months
            else:
                if row[0].month not in cashflow_dict[row[0].year]:
                    cashflow_dict[row[0].year][row[0].month] = row[2]
                else:
                    cashflow_dict[row[0].year][row[0].month] += row[2]

        year_dict = {}
        for year, months in cashflow_dict.items():
            for i in range(1, 13):
                if i not in months.keys():
                    cashflow_dict[year][i] = 0.0
                if year == datetime.datetime.now().year and i == datetime.datetime.now().month:
                    break
            months_list = list(map(lambda x: x[1], sorted(months.items())))
            growth_abs = [months_list[i]-months_list[i-1] for i in range(0, len(months_list)) if i > 0]
            avg_growth_abs = round(sum(growth_abs) / len(growth_abs), 2)

            zeromonths = [i for i in months_list if i > 0]
            growth_perc = [(zeromonths[i]-zeromonths[i-1])/zeromonths[i-1]*100 for i in range(0, len(zeromonths)) if i > 0]
            if growth_perc != []:
                avg_growth_perc = round(sum(growth_perc) / len(growth_perc), 2)
            else:
                avg_growth_perc = 0.0
            year_dict[year] = (round(sum(months_list), 2), avg_growth_abs, avg_growth_perc)

        year_tuples = sorted(year_dict.items())
        table_list = [["rok", "suma", "śr. wzrost abs.", "śr. wzrost %"]]
        for t in year_tuples:
            table_list.append([t[0], t[1][0], t[1][1], t[1][2]])

        year_table = texttable.Texttable(max_width=0)
        year_table.add_rows(table_list)
        print(year_table.draw())









