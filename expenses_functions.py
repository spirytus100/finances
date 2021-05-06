import csv
from datetime import datetime, timedelta, date
import matplotlib.pyplot as plt
import re
from sqlite3 import Error


categories = ("samochód", "ubrania", "uroczystości/prezenty", "rachunki", "wieś", "rower", "rozrywka", "kot",
              "nauka", "kosmetyki", "RTV/AGD", "jedzenie/picie", "leki", "Kościół", "alkohol", "zgubienie/utrata",
              "wierzytelność", "dom", "zdrowie", "darowizna", "sport", "komputer", "inne")

class DatabaseActions:

    def __init__(self, connection):
        self.connection = connection

    def show_transactions_by_date(self, parameter="all"):

        connection = self.connection

        try:
            int_value = int(parameter)
        except ValueError:
            if parameter == "all":
                sql_select_statement = "SELECT rowid, date, item, category, cost FROM expenses"
                cursor = connection.execute(sql_select_statement)
            else:
                return print("Błędny parametr.")
        else:
            date_limit = datetime.today() - timedelta(days=int_value)
            sql_select_statement = "SELECT rowid, date, item, category, cost FROM expenses WHERE date >= ?"
            cursor = connection.execute(sql_select_statement, (date_limit,))

        for row in cursor:
            space1 = (30 - len(row[2])) * " "
            space2 = (22 - len(row[3])) * " "
            print(row[0], row[1], row[2], space1, row[3], space2, row[4], "zł")

    def show_transactions_by_category(self, category):
        connection = self.connection
        sql_select_statement = "SELECT rowid, date, item, category, cost FROM expenses WHERE category = ?"
        cursor = connection.execute(sql_select_statement, (category,))
        for row in cursor:
            space1 = (30 - len(row[2])) * " "
            space2 = (22 - len(row[3])) * " "
            print(row[0], row[1], row[2], space1, row[3], space2, row[4], "zł")

    def update_transaction(self, idnum, parameter):
        try:
            idnum = int(idnum)
        except ValueError:
            return print("Błędny parametr.")

        new_value = ""
        if parameter in ("date", "item", "category", "cost"):
            if parameter == "date":
                new_value = input("Podaj nową datę: ")
                new_value_re = re.match("20\d\d-[01][0-2]-[0-3][0-9]", new_value)
                if not new_value_re:
                    return print("Błędny parametr.")
            elif parameter == "item":
                new_value = input("Wpisz przedmiot zakupu (max. 30 znaków): ")
                if len(new_value) > 30:
                    return print("Błędny parametr.")
            elif parameter == "category":
                new_value = input("Wpisz nową kategorię: ")
                if new_value not in categories:
                    return print("Błędny parametr.")
            elif parameter == "cost":
                new_value = input("Podaj nową cenę: ")
                try:
                    new_value = float(new_value)
                except ValueError:
                    return print("Błędny parametr.")
        else:
            return print("Błędny parametr.")

        if new_value != "":
            connection = self.connection
            sql_update_statement = "UPDATE expenses SET " + parameter + " = ? WHERE rowid = ?"
            try:
                connection.execute(sql_update_statement, (new_value, idnum))
                connection.commit()
            except Error:
                print("Błąd zapisu do bazy danych.")
            else:
                print("Dane wskazanej transakcji zostały zaktualizowane.")

    def delete_transaction(self, idnum):

        print("Transakcja zostanie usunięta z bazy danych.")
        answer = input("Czy jesteś pewien? ")
        if answer != "y":
            return print("Transakcja nie została usunięta z bazy danych.")

        connection = self.connection
        sql_select_statement = "SELECT item, category, cost FROM expenses WHERE rowid = ?"
        cursor = connection.execute(sql_select_statement, (idnum,))
        record = cursor.fetchone()
        if record is not None:
            item = record[0]
            category = record[1]
            cost = record[2]
        else:
            return print("Brak podanego numeru id w bazie danych.")

        sql_delete_statement = "DELETE FROM expenses WHERE rowid = ?"
        connection.execute(sql_delete_statement, (idnum,))
        connection.commit()
        budget_list = show_budget()
        for i, row in enumerate(budget_list):
            if row[0] == item and row[1] == category and row[3] == cost:
                msg = "Czy skasować pozycję " + item + ", " + category + ", " + str(
                    cost) + " z aktualnego budżetu? "
                question = input(msg)
                if question == "y":
                    budget_list.remove(i)
                    with open("budget.csv", "w", newline="") as fo:
                        fields = ["przedmiot", "kategoria", "budżet", "koszt", "zostało"]
                        csv_writer = csv.writer(fo, delimiter=";")
                        csv_writer.writerow(fields)
                        csv_writer.writerows(budget_list[1:])
                    break
                else:
                    print("Pozycja nie została usunięta z aktualnego budżetu.")
                    break

        print("Transakcja została usunięta z bazy danych.")

    def find_transaction_by_item(self, item):
        connection = self.connection
        sql_select_statement = '''SELECT rowid, date, item, category, cost FROM expenses WHERE item LIKE "%'''+item+'''%";'''
        cursor = connection.execute(sql_select_statement)
        for row in cursor:
            space1 = (30 - len(row[2])) * " "
            space2 = (22 - len(row[3])) * " "
            print(row[0], row[1], row[2], space1, row[3], space2, row[4], "zł")

    def find_transaction_by_id(self, idnum):
        connection = self.connection
        sql_select_statement = "SELECT rowid, date, item, category, cost FROM expenses WHERE rowid = ?"
        cursor = connection.execute(sql_select_statement, (idnum,))
        record = cursor.fetchone()
        if record is not None:
            print(record[0], record[1], record[2], record[3], record[4])
        else:
            print("Brak podanego numeru id w bazie danych.")

    def save_expense_to_db(self, item, category, price):
        connection = self.connection
        today = datetime.now()
        sql_insert_statement = "INSERT INTO expenses VALUES (?, ?, ?, ?)"
        connection.execute(sql_insert_statement, (today, item, category, price))
        connection.commit()

    def get_monthly_expenses_by_category(self, category):
        connection = self.connection
        sql_select_statement = "SELECT date, cost FROM expenses WHERE category = ?"
        cursor = connection.execute(sql_select_statement, (category,))
        cursor_rows = []
        for row in cursor:
            cursor_rows.append((row[0].month, row[0].year, row[1]))

        if cursor_rows == []:
            print("W bazie danych nie znaleziono wydatków o podanej kategorii.")
            return cursor_rows
        expenses_list = []
        prev_row_month = cursor_rows[0][0]
        prev_row_year = cursor_rows[0][1]
        cost = 0.0
        for i, row in enumerate(cursor_rows):

            if i == len(cursor_rows) - 1:
                expenses_list.append((row[0], row[1], round(cost + row[2], 2)))

            if row[0] != prev_row_month or row[1] != prev_row_year:
                expenses_list.append((prev_row_month, prev_row_year, round(cost, 2)))
                cost = 0.0
                cost += row[2]
            else:
                cost += row[2]

            prev_row_month = row[0]
            prev_row_year = row[1]

        min_year = 2019
        max_year = max(expenses_list, key=lambda x: x[1])[1]

        model_list = []
        for x in range(min_year, max_year + 1):
            for y in range(1, 13):
                if x > min_year or y > 4:
                    model_list.append((y, x, 0.0))
                if x == datetime.today().year and y == datetime.today().month:
                    break

        for el in expenses_list:
            for i, model in enumerate(model_list):
                if el[0] == model[0] and el[1] == model[1]:
                    model_list.remove(model)
                    model_list.insert(i, el)
                if model[0] == datetime.today().month and model[1] == datetime.today().year:
                    break

        final_list = []
        for el in model_list:
            final_list.append((str(el[0])+"."+str(el[1]), el[2]))

        return final_list

    def show_line_chart(self, expenses_list, category):
        if expenses_list == []:
            return
        input_list, output_list = map(list, zip(*expenses_list))

        plt.plot(input_list, output_list, linewidth=5)
        plt.title(category, fontsize=24)
        plt.ylabel("Suma wydatków", fontsize=14)
        plt.xticks(rotation=60)
        plt.tick_params(axis="both", labelsize=14)
        plt.show()

    def calculate_trendline(self, expenses_list):
        if expenses_list == []:
            return
        ti = len(expenses_list)
        yi = [x[1] for x in expenses_list]
        tavg = sum([x for x in range(1, ti + 1)]) / ti
        yavg = sum(yi) / len(yi)
        ti_min_tavg = [x - tavg for x in range(1, ti + 1)]
        yi_min_yavg = [x - yavg for x in yi]
        ti_min_tavg_pow = [x ** 2 for x in ti_min_tavg]
        ti_multip_yi = [x * y for x, y in zip(ti_min_tavg, yi_min_yavg)]
        a = sum(ti_multip_yi) / sum(ti_min_tavg_pow)
        b = yavg - a * tavg
        trendline = [b + x * a for x in range(0, ti + 1)]

        return trendline

    def show_scatter_trendline_chart(self, expenses_list, trendline, category):
        if expenses_list == []:
            return
        xvalues, yvalues = map(list, zip(*expenses_list))

        plt.scatter(xvalues, yvalues, s=15)
        plt.plot(trendline)
        plt.xticks(rotation=60)
        plt.title(category, fontsize=24)
        plt.ylabel("Suma wydatków", fontsize=14)
        plt.show()


def adjust_budget(item, category, price):
    with open("budget.csv", "r") as fo:
        csv_reader = csv.reader(fo, delimiter=";")
        expenses_list = []
        expected = []
        unexpected = []
        count = 100
        for i, row in enumerate(csv_reader):
            if row[0] == "":
                count = i

            if i > count:
                unexpected.append(row)
            else:
                expenses_list.append(row[0])
                expected.append(row)

    if item not in expenses_list:
        unexpected_expense = True
    else:
        unexpected_expense = False
        for row in expected:
            if row[0] == item:
                row[3] = float(row[3]) + float(price)
                row[4] = float(row[2]) - float(row[3])

    with open("budget.csv", "w", newline="") as fo:
        fields = ["przedmiot", "kategoria", "budżet", "koszt", "zostało"]
        if unexpected_expense == True:
            budget_list = expected + unexpected + [[item, category, "0.0", float(price), 0.0 - float(price)]]
        else:
            budget_list = expected + unexpected
        csv_writer = csv.writer(fo, delimiter=";")
        csv_writer.writerow(fields)
        csv_writer.writerows(budget_list[1:])

def show_budget():
    with open("budget.csv", "r") as fo:
        csv_reader = csv.reader(fo, delimiter=";")
        budget_list = list(csv_reader)
        budget_sum = 0.0
        cost_sum = 0.0
        remains_sum = 0.0
        for i, row in enumerate(budget_list):

            if row[0] not in ("przedmiot", ""):
                budget_sum = budget_sum + float(row[2])
                cost_sum = cost_sum + float(row[3])
                remains_sum = remains_sum + float(row[4])

            space1 = (30 - len(row[0])) * " "
            space2 = (22 - len(row[1])) * " "
            space3 = (8 - len(row[2])) * " "
            space4 = (8 - len(row[3])) * " "
            if i == 0:
                print(row[0], space1, row[1], space2, row[2], space3, row[3], space4, row[4])
                print(83 * "-")
            elif row[0] == "":
                print("\nWydatki nieprzewidziane:")
            else:
                print(row[0], space1, row[1], space2, row[2], space3, row[3], space4, row[4])

        print(83 * "-")
        print(31 * " ", "suma", (22 - 4) * " ", str(round(budget_sum, 2)), (8 - len(str(round(budget_sum, 2)))) * " ", str(round(cost_sum, 2)),
              (8 - len(str(round(cost_sum, 2)))) * " ", str(round(remains_sum, 2)))

        return budget_list

def read_budget_results(parameter=None):
    if parameter is not None and parameter not in ("budżet", "wydane", "przekroczenie", "niezaplanowane"):
        return print("Błędny parametr.")
    else:
        chart_list = []

    with open("monthly_budget_results.csv", "r") as fo:
        fieldnames = ["data", "budżet", "wydane", "przekroczenie", "niezaplanowane"]
        csv_reader = csv.DictReader(fo, fieldnames=fieldnames, delimiter=";")
        budget_sum = 0.0
        cost_sum = 0.0
        exceeded = 0.0
        unplanned = 0.0
        i = 0
        for row in csv_reader:
            if parameter is not None:
                chart_list.append((row["data"], row[parameter]))
            if row["data"] != "data":
                i += 1
                budget_sum = budget_sum + float(row["budżet"])
                cost_sum = cost_sum + float(row["wydane"])
                exceeded = exceeded + float(row["przekroczenie"])
                unplanned = unplanned + float(row["niezaplanowane"])
            print(row["data"], row["budżet"], row["wydane"], row["przekroczenie"], row["niezaplanowane"])

    print("\n")
    print("Średni budżet:", round(budget_sum/i, 2))
    print("Średnie wydatki:", round(cost_sum / i, 2))
    print("Średnie przekroczenie budżetu:", round(exceeded / i, 2))
    print("Średnie nieplanowane wydatki:", round(unplanned / i, 2))

    if parameter is not None:
        input_list, output_list = map(list, zip(*chart_list))
        output_list = list(map(lambda x: float(x), output_list))

        plt.plot(input_list, output_list, linewidth=5)
        plt.title(parameter.title(), fontsize=24)
        plt.ylabel("Suma wydatków", fontsize=14)
        plt.xticks(rotation=60)
        plt.tick_params(axis="both", labelsize=14)
        plt.show()

def append_to_budget_results():
    with open("budget.csv", "r") as fo:
        csv_reader = csv.reader(fo, delimiter=";")
        budget_sum = 0.0
        cost_sum = 0.0
        remains_sum = 0.0
        exceeds = False
        exceeded_cost = 0.0
        for row in csv_reader:
            if row[0] not in ("przedmiot", ""):
                budget_sum = budget_sum + float(row[2])
                cost_sum = cost_sum + float(row[3])
                if exceeds == True:
                    exceeded_cost = exceeded_cost + float(row[3])
                remains_sum = remains_sum + float(row[4])
            if row[0] == "":
                exceeds = True

    budget_sum = round(budget_sum, 2)
    cost_sum = round(cost_sum, 2)
    exceeded = round(budget_sum - cost_sum, 2)
    exceeded_cost = round(exceeded_cost, 2)

    print("Wyniki miesiąca:")
    print("Budżet:", budget_sum)
    print("Wydano:", cost_sum)
    print("Przekroczenie:", exceeded)
    print("Niezaplanowane:", exceeded_cost)

    question = input("Czy na pewno rozliczyć budżet? ")
    if question != "y":
        return print("Budżet nie został rozliczony.")

    if date.today().month == 1:
        budget_date = "12."+str(date.today().year-1)
    else:
        budget_date = str(date.today().month-1)+"."+str(date.today().year)

    append_list = [budget_date, str(budget_sum), str(cost_sum), str(exceeded), str(exceeded_cost)]

    with open("monthly_budget_results.csv", "a+", newline="") as fo:
        csv_writer = csv.writer(fo, delimiter=";")
        csv_writer.writerow(append_list)

    print("Budżet został rozliczony.")



