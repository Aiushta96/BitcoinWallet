import sqlite3
from dataclasses import dataclass
from uuid import UUID

from core.constants import COMMISSION
from core.errors import DoesNotExistError, EqualityError, BalanceError
from core.transactions import Transaction
from core.users import User
from infra.in_database.wallet_sqlite import WalletInDatabase


@dataclass
class TransactionInDatabase:
    def __init__(self, db_path: str = "./database.db") -> None:
        self.db_path = db_path
        self.create_table()

    def create_table(self) -> None:
        create_table_query = """
            CREATE TABLE IF NOT EXISTS wallet_transactions (
                wallet_from TEXT NOT NULL,
                wallet_to TEXT NOT NULL,
                amount_in_satoshis INT NOT NULL
            );
        """
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.cursor()
            cursor.execute(create_table_query)
            connection.commit()

    def clear_tables(self) -> None:
        delete_table_query = """
              DELETE FROM wallet_transactions;
        """
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.cursor()
            cursor.execute(delete_table_query)

    def create(self, transaction: Transaction, _: User, __: User) -> int:
        wallet_from = WalletInDatabase().get(transaction.wallet_from)
        wallet_to = WalletInDatabase().get(transaction.wallet_to)

        if wallet_from is None or wallet_to is None:
            raise DoesNotExistError("wallet does not exists.")

        if transaction.wallet_from == transaction.wallet_to:
            raise EqualityError("Can not send money on the same wallet.")

        if wallet_from.balance < transaction.amount_in_satoshis:
            raise BalanceError("Not enough money.")

        WalletInDatabase().change_balance(transaction.wallet_from,
                                          round(wallet_from.balance - transaction.amount_in_satoshis))
        WalletInDatabase().change_balance(transaction.wallet_to,
                                          wallet_to.balance + transaction.amount_in_satoshis * (1 - COMMISSION))

        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO wallet_transactions (wallet_from, wallet_to, amount_in_satoshis)
                VALUES (?, ?, ?);
                """,
                (str(transaction.wallet_from), str(transaction.wallet_to), transaction.amount_in_satoshis)
            )
            connection.commit()

        commission = (
            round(transaction.amount_in_satoshis * COMMISSION)
            if wallet_from.API_key != wallet_to.API_key
            else 0
        )
        return commission

    def get_transactions(self, address: UUID) -> list[Transaction]:
        transactions = []

        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT wallet_from, wallet_to, amount_in_satoshis
                FROM wallet_transactions
                WHERE wallet_from = ? OR wallet_to = ?;
                """,
                (str(address), str(address))
            )

            results = cursor.fetchall()

            for result in results:
                transaction = Transaction(
                    wallet_from=result[0],
                    wallet_to=result[1],
                    amount_in_satoshis=result[2]
                )
                transactions.append(transaction)

        return transactions
