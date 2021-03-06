import datetime
from sqlite3 import Error
import retirement


class Investment:

    def __init__(self, name, investment_id, category, financial_institution, buy_date, amount, buy_price, buy_comission,
                 retirement, sell_date, sell_price, sell_commission, profit, is_over):
        self.name = name
        self.investment_id = investment_id
        self.category = category
        self.financial_institution = financial_institution
        self.buy_date = buy_date
        self.amount = amount
        self.buy_price = buy_price
        self.buy_commision = buy_comission
        self.retirement = retirement
        self.sell_date = sell_date
        self.sell_price = sell_price
        self.sell_comission = sell_commission
        self.profit = profit
        self.is_over = is_over

    def validate_new_investment(self):
        ok = True

        if len(self.name) > 200:
            ok = False
            print("Zbyt długa nazwa instrumentu.")

        categories = ("akcje polskie", "akcje zagraniczne", "obligacje skarbowe polskie", "obligacje korporacyjne polskie",
                    "obligacje zagraniczne", "kryptowaluty", "surowce", "depozyty")

        if self.category not in categories:
            ok = False
            print("Błędna kategoria inwestycji.")

        try:
            dt_buy_date = datetime.datetime.strptime(self.buy_date, "%d-%m-%Y")
        except ValueError:
            ok = False
            print("Błędny format daty.")

        floats = []
        for column in (self.buy_price, self.buy_commision, self.amount):
            try:
                x = float(column)
            except ValueError:
                ok = False
                print("Błędny format liczby.")
            else:
                floats.append(x)

        if not ok:
            return ok
        else:
            return (self.name, self.investment_id, self.category, self.financial_institution, dt_buy_date, floats[2],
                    floats[0], floats[1], self.retirement, self.sell_date, self.sell_price, self.sell_comission,
                    self.profit, self.is_over)

    def buy_asset(self, connection, values):
        if not values:
            return print("Błąd zapisu. Proszę podać poprawne dane.")

        if input("Czy zapisać inwestycję? ") != "y":
            return print("Inwestycja nie została zapisana.")

        sql_insert = "INSERT INTO investments VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        connection.execute(sql_insert, values)
        connection.commit()
        print("Inwestycja została zapisana.")

        if values[8]:
            total_cost = values[5] * values[6]
            retirement_position = retirement.Retirement(connection)
            retirement_position.notify_investment(datetime.datetime.now(), values[0], total_cost, "buy")


    def sell_asset(self, connection, idnum, sell_date, amount, sell_price, sell_comission):
        floats = []
        for el in (amount, sell_price, sell_comission):
            try:
                x = float(el)
            except ValueError:
                return print("Błędny format liczby.")
            else:
                floats.append(x)

        amount = floats[0]

        try:
            dt_sell_date = datetime.datetime.strptime(sell_date, "%d-%m-%Y")
        except ValueError:
            return print("Błędny format daty.")
        else:
            if dt_sell_date < self.buy_date:
                return print("Data sprzedaży nie może być wcześniejsza niż data kupna.")

        if amount < self.amount:
            #sprzedawana jest ilość mniejsza od ilości całkowitej instrumentu
            amount_remains = self.amount - amount
            profit = (amount * floats[1]) - (amount * self.buy_price) - floats[2]
            sql_update = "UPDATE investments SET amount = ? WHERE rowid = ?"
            sql_insert = "INSERT INTO investments VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
            sold_values = (self.name, self.investment_id, self.category, self.financial_institution, self.buy_date,
                           floats[3], self.buy_price, self.buy_commision, self.retirement, dt_sell_date, floats[0],
                           floats[1], profit, True)
            answer = input("Czy zapisać transakcję sprzedaży (y/n): ")
            if answer != "y":
                return

            connection.execute(sql_update, (amount_remains, idnum))
            connection.commit()
            connection.execute(sql_insert, sold_values)
            connection.commit()

            if sold_values[8]:
                total_return = sold_values[5] * sold_values[6] + sold_values[12]
                retirement_position = retirement.Retirement(connection)
                retirement_position.notify_investment(datetime.datetime.now(), sold_values[0], total_return, "sell")

            print("Transakcja została zapisana.")
            print("Sprzedałeś", amount, self.category, self.name, "za cenę", sell_price, ". Twój zysk to", profit, "zł.")

        elif amount == self.amount:
            profit = (amount * floats[1]) - (self.amount * self.buy_price + self.buy_commision) - floats[2]
            sql_update = "UPDATE investments SET sell_date = ?, sell_price = ?, sell_comission = ?, profit = ?, is_over = ? WHERE rowid = ?"
            sold_values = (dt_sell_date, floats[1], floats[2], float(profit), True, idnum)
            answer = input("Czy zapisać transakcję sprzedaży (y/n): ")
            if answer != "y":
                return

            connection.execute(sql_update, sold_values)
            connection.commit()

            if self.retirement:
                total_return = float(self.amount) * floats[0] + profit
                retirement_position = retirement.Retirement(connection)
                retirement_position.notify_investment(datetime.datetime.now(), self.name, total_return, "sell")

            print("Transakcja została zapisana.")
            print("Sprzedałeś", amount, self.category, self.name, "za cenę", sell_price, ". Twój zysk to", profit, ".")

        else:
            print("Nie możesz sprzedać ilości większej od posiadanej.")


def get_user_input_buy(connection):
    name = input("Nazwa instrumentu: ")

    cursor = connection.execute("SELECT name, investment_id FROM investments")
    investment_ids = []
    for row in cursor:
        if name == row[0]:
            inv_id = row[1]
            break
        else:
            investment_ids.append(row[1])

    last_id = max(investment_ids)
    inv_id = last_id + 1

    category = input("Kategoria inwestycyjna: ")
    financial_institution = input("Instytucja finansowa: ")
    buy_date = input("Data kupna w formacie DD-MM-YYYY: ")
    amount = input("Ilość: ")
    buy_price = input("Cena kupna: ")
    buy_comission = input("Prowizja: ")
    retirement = input("Emerytura (y/n): ")
    if retirement == "y":
        retirement = True
    else:
        retirement = False
    investment_data = (name, inv_id, category, financial_institution, buy_date, amount, buy_price, buy_comission, retirement)

    return investment_data


def get_user_input_sell():
    idnum = input("Numer id: ")
    sell_date = input("Data sprzedaży w formacie DD-MM-YYYY: ")
    amount = input("Ilość: ")
    sell_price = input("Cena sprzedaży: ")
    sell_comission = input("Prowizja: ")
    sell_data = (idnum, sell_date, float(amount), sell_price, sell_comission)

    return sell_data


def add_interest(connection, data_tuple):
    if not data_tuple:
        return
    name = data_tuple[0]
    investment_id = data_tuple[1]
    category = data_tuple[2]
    date = datetime.datetime.now()

    interest = input("Podaj kwotę odsetek: ")
    try:
        interest = float(interest)
    except ValueError:
        return print("Błędny format liczby.")

    sql_insert = "INSERT INTO interest VALUES (?, ?, ?, ?, ?)"
    values = (name, investment_id, category, date, interest)

    sql_cashflow_insert = "INSERT INTO cashflow VALUES (?, ?, ?, ?)"
    cashflow_values = (date, "odsetki " + name, "zysk kapitałowy", interest)
    try:
        connection.execute(sql_insert, values)
        connection.commit()
        connection.execute(sql_cashflow_insert, cashflow_values)
        connection.commit()
    except Error:
        print("Błąd zapisu do bazy danych.")
    else:
        print("Odsetki zostały dodane.")




