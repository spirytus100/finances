import sqlite3
import expenses_functions as ef
from claims import Claim
import investments
import investments_dbqueries as invdb
from cashflow import Cashflow
from sys import argv
import finances_downloads
from retirement import Retirement


# todo funkcja sprawdzająca upływający termin inwestycji (obligacji)

def read_help(filename):
    with open(filename, "r") as fo:
        lines = fo.readlines()
        for line in lines:
            print(line.strip())

if len(argv) == 1 or len(argv) == 2 and argv[1] == "expenses":
    budget_list = ef.show_budget()

categories = ("samochód", "ubrania", "uroczystości/prezenty", "rachunki", "wieś", "rower", "rozrywka", "kot",
              "nauka", "kosmetyki", "RTV/AGD", "jedzenie/picie", "leki", "Kościół", "alkohol", "zgubienie/utrata",
              "wierzytelność", "dom", "zdrowie", "darowizna", "sport", "komputer", "inne")

connection = sqlite3.connect("finances.db", detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
db_actions = ef.DatabaseActions(connection)

while True:
    if len(argv) == 1 or len(argv) == 2 and argv[1] == "expenses":
        user_input = input("Co chcesz zrobić? ")
        user_input = user_input.split()

        if user_input[0] == "q":
            print("Dziękuję za skorzystanie z programu.")
            break

        if user_input[0] == "add":
            item = 35*"x"
            while len(item) > 30:
                item = input("Przedmiot zakupu: ")
                if len(item) > 30:
                    print("Zbyt długa nazwa.")

            category = ""
            for row in budget_list:
                if item in row:
                    category = row[1]
                    print("Kategoria:", category)

            if category == "":
                while category not in categories:
                    category = input("Kategoria: ")
                    if category not in categories:
                        print("Nie ma takiej kategorii.")
                    if category == "q":
                        break

            price = input("Cena: ")
            try:
                float_price = float(price)
            except ValueError:
                print("Niewłaściwy format ceny.")
            else:
                db_actions.save_expense_to_db(item, category, float_price)
                ef.adjust_budget(item, category, str(float_price))

        elif user_input[0] == "budget":
            if len(user_input) == 1:
                ef.show_budget()
            elif len(user_input) == 2:
                if user_input[1] == "results":
                    ef.read_budget_results()
            elif len(user_input) == 3:
                parameter = user_input[2]
                ef.read_budget_results(parameter)
            else:
                print("Błędna liczba parametrów.")

        elif user_input[0] == "categories":
            for category in categories:
                print(category)

        elif user_input[0] == "transactions":
            if len(user_input) == 2:
                parameter = user_input[1]
                db_actions.show_transactions_by_date(parameter)
            elif len(user_input) == 1:
                db_actions.show_transactions_by_date()
            else:
                print("Błędna liczba parametrów.")

        elif user_input[0] == "update":
            if len(user_input) == 3:
                idnum = user_input[1]
                parameter = user_input[2]
                db_actions.update_transaction(idnum, parameter)

        elif user_input[0] == "delete":
            if len(user_input) == 2:
                idnum = user_input[1]
                db_actions.delete_transaction(idnum)

        elif user_input[0] in categories:
            if len(user_input) == 1:
                category = user_input[0]
                db_actions.show_transactions_by_category(category)

        elif user_input[0] == "backup":
            if len(user_input) == 1:
                backup_connection = sqlite3.connect("/home/j/backup/backup_finances.db")
                with backup_connection:
                    connection.backup(backup_connection)
                backup_connection.close()
                print("Kopia zapasowa bazy danych została zapisana.")

        elif user_input[0] == "find":
            if len(user_input) == 2:
                idnum = user_input[1]
                db_actions.find_transaction_by_id(idnum)
            elif len(user_input) == 1:
                item = input("Wpisz szukany przedmiot: ")
                db_actions.find_transaction_by_item(item)

        elif user_input[0] == "clear" and user_input[1] == "budget":
            if len(user_input) == 2:
                ef.append_to_budget_results()

        elif user_input[0] == "reset" and user_input[1] == "budget":
            ef.reset_budget()

        elif user_input[0] == "chart":
            if len(user_input) == 2:
                if user_input[1] in categories:
                    category = user_input[1]
                    category_list = db_actions.get_monthly_expenses_by_category(category)
                    db_actions.show_line_chart(category_list, category)
                else:
                    print("Błędny argument.")

            elif len(user_input) == 3:
                if user_input[2] == "scatter":
                    if user_input[1] in categories:
                        category = user_input[1]
                        category_list = db_actions.get_monthly_expenses_by_category(category)
                        trendline = db_actions.calculate_trendline(category_list)
                        db_actions.show_scatter_trendline_chart(category_list, trendline, category)

        elif user_input[0] == "help" and len(user_input) == 1:
            read_help("expenses_help.txt")

        else:
            print("Błędne polecenie.")

    elif len(argv) == 2 and argv[1] == "claims":
        claim = Claim(connection)
        mode = input("Wpisz polecenie: ")
        if mode == "q":
            print("Dziękuję za skorzystanie z programu.")
            break
        elif mode == "add":
            item = input("Podaj przedmiot: ")
            cost = input("Podaj koszt: ")
            claim.add_claim(item, cost)
            claim.count_balance()
        elif mode == "update":
            idnum = input("Podaj numer id: ")
            column = input("Podaj kolumnę, która ma być zaktualizowana: ")
            claim.update_claim(idnum, column)
            claim.count_balance()
        elif mode == "delete":
            idnum = input("Podaj numer id: ")
            claim.delete_claim(idnum)
            claim.count_balance()
        elif mode == "show":
            claim.show_claims()
        elif mode == "saldo":
            claim.count_balance()
        elif mode == "help":
            read_help("claims_help.txt")
        else:
            print("Błędne polecenie.")

    elif len(argv) == 2 and argv[1] == "investments":
        #finances_downloads.get_inflation_stats()
        db_queries = invdb.DBQueries(connection)
        mode = input("Wpisz polecenie: ")

        if mode == "q":
            print("Dziękuję za skorzystanie z programu.")
            break
        elif mode in db_queries.asset_categories:
            category = mode
            db_queries.find_investments_by_category(category, all=False)
            continue

        split_mode = mode.split()

        if len(split_mode) == 1:
            if split_mode[0] == "interest":
                idnum = input("Podaj numer id obligacji: ")
                data_tuple = db_queries.find_investment_by_id(idnum)
                investments.add_interest(connection, data_tuple)

            elif split_mode[0] == "buy":
                buy_data = investments.get_user_input_buy(connection)
                investment = investments.Investment(name=buy_data[0],
                                                    investment_id=buy_data[1],
                                                    category=buy_data[2],
                                                    financial_institution=buy_data[3],
                                                    buy_date=buy_data[4],
                                                    amount=buy_data[5],
                                                    buy_price=buy_data[6],
                                                    buy_comission=buy_data[7],
                                                    retirement=buy_data[8],
                                                    sell_date=None,
                                                    sell_price=0.0,
                                                    sell_commission=0.0,
                                                    profit=0.0,
                                                    is_over=False)

                verified_data = investment.validate_new_investment()
                investment.buy_asset(connection, verified_data)

            elif split_mode[0] == "sell":
                sell_data = investments.get_user_input_sell()
                db_data = db_queries.find_investment_by_id(sell_data[0])
                investment_to_sell = investments.Investment(name=db_data[0],
                                                            investment_id=db_data[1],
                                                            category=db_data[2],
                                                            financial_institution=db_data[3],
                                                            buy_date=db_data[4],
                                                            amount=db_data[5],
                                                            buy_price=db_data[6],
                                                            buy_comission=db_data[7],
                                                            retirement=db_data[8],
                                                            sell_date=db_data[9],
                                                            sell_price=db_data[10],
                                                            sell_commission=db_data[11],
                                                            profit=db_data[12],
                                                            is_over=db_data[13])

                investment_to_sell.sell_asset(connection, sell_data[0], sell_data[1], sell_data[2], sell_data[3],
                                              sell_data[4])

            elif split_mode[0] == "help":
                read_help("investments_help.txt")

            elif split_mode[0] == "involvement":
                db_queries.count_categories_involvement(chart=False)

            elif split_mode[0] == "quotes":
                finances_downloads.get_quotes()

            else:
                db_queries.show_investment_records(mode)

        elif len(split_mode) == 2:
            if split_mode[0] == "id":
                idnum = split_mode[1]
                db_queries.find_investment_by_id(idnum)

            elif split_mode[0] == "find":
                name = " ".join(split_mode[1:])
                db_queries.find_investment_by_name(name)

            elif split_mode[0] == "update":
                idnum = split_mode[1]
                db_queries.update_record(idnum)

            elif split_mode[0] == "delete":
                idnum = split_mode[1]
                db_queries.delete_record(idnum)

            elif split_mode[0] == "involvement" and split_mode[1] == "chart":
                db_queries.count_categories_involvement(chart=True)
            else:
                db_queries.show_investment_records(mode)

        elif split_mode[0] == "count" and split_mode[1] == "interest":
            bond_name = " ".join(split_mode[2:])
            interest = db_queries.count_bond_interest(bond_name)
            if interest:
                print("Dla instrumentu", bond_name, "suma wpłaconych odsetek wynosi", interest, "zł.")

        elif split_mode[0] == "delete" and split_mode[1] == "interest":
            idnum = input("Podaj numer id rekordu: ")
            db_queries.delete_interest(idnum)

        elif split_mode[0] == "absolute" and split_mode[1] == "profit":
            category = " ".join(split_mode[2:])
            db_queries.count_average_absolute_profit_by_category(category)

        elif split_mode[0] == "percentage" and split_mode[1] == "profit":
            category = " ".join(split_mode[2:])
            profit = db_queries.count_average_percentage_profit_by_category(category)

        elif split_mode[0] == "average" and split_mode[1] == "profit":
            parameter = " ".join(split_mode[2:])
            db_queries.count_average_profit(parameter)
        else:
            db_queries.show_investment_records(mode)

    elif len(argv) == 2 and argv[1] == "cashflow":
        savings = Cashflow(connection)
        mode = input("Wpisz polecenie: ")
        if mode == "q":
            print("Dziękuję za skorzystanie z programu.")
            break

        mode = mode.split()
        if len(mode) == 1:
            if mode[0] == "add":
                values = savings.get_input()
                if values:
                    savings.save_position(values)
            elif mode[0] == "show":
                savings.print_positions(parameter=None)
            elif mode[0] == "saldo":
                saldo = savings.count_balance()
                print("Saldo wynosi", saldo, "zł.")
            elif mode[0] == "analyze":
                savings.analyze_cashflow()
            elif mode[0] == "cash":
                savings.count_cash()
            elif mode[0] == "help":
                read_help("cashflow_help.txt")
        elif len(mode) == 2:
            if mode[0] == "update":
                idnum = mode[1]
                savings.update_position(idnum)
            elif mode[0] == "delete":
                idnum = mode[1]
                savings.delete_position(idnum)
            elif mode[0] == "show":
                parameter = mode[1]
                savings.print_positions(parameter=parameter)

    elif len(argv) == 2 and argv[1] == "retirement":
        retire = Retirement(connection)
        mode = input("Wpisz polecenie: ")
        if mode == "q":
            print("Dziękuję za skorzystanie z programu.")
            break

        mode = mode.split()
        if len(mode) == 1:
            if mode[0] == "add":
                retire.add_position()
            elif mode[0] == "show":
                retire.show_positions()
            elif mode[0] == "count":
                retire.count_balance()
            elif mode[0] == "investments":
                retire.show_investments(over=False)
        elif len(mode) == 2:
            if mode[0] == "delete":
                idnum = mode[1]
                retire.delete_position(idnum)
            elif mode[0] == "investments" and mode[1] == "over":
                retire.show_investments(over=True)
        elif len(mode) == 3:
            if mode[0] == "update":
                idnum = mode[1]
                column = mode[2]
                retire.update_position(idnum, column)

    else:
        print("Błędne polecenie.")


