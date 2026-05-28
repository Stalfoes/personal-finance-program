from __future__ import annotations
from typing import Optional, Any, TypeVar, Union
import sqlite3
from dataclasses import dataclass
from collections import defaultdict
import rapidfuzz
import json

from .parse import Statement, Account, Transaction


# CONSTANTS
FUZZY_MATCH_SIGNIFICANCE_THRESHOLD = 60 # how similar must the descriptions be for the FuzzyMatcher to report it at all


T = TypeVar('T')
@dataclass
class Column[T]:
    value:Optional[T]
    confidence:Optional[Union[int,dict[str,int]]]
    def query_node_name_and_type(self, database:str) -> str:
        if self.value is None:
            return ''
        conn = sqlite3.connect(database)
        c = conn.cursor()
        c.execute("""SELECT name,type
                    FROM Nodes
                    WHERE id = ?
                """, (self.value,))
        node_name,node_type = c.fetchone()
        conn.close()
        return f"{node_name} ({node_type})"
    def query_merchant_name(self, database:str) -> str:
        if self.value is None:
            return ''
        conn = sqlite3.connect(database)
        c = conn.cursor()
        c.execute("""SELECT pretty_name
                    FROM Merchants
                    WHERE id = ?
                """, (self.value,))
        row = c.fetchone()
        conn.close()
        return row[0]


@dataclass
class TableEntry:
    id: Column[int]
    fit_id: Column[int]
    time: Column[str]
    from_node_id: Column[int]
    to_node_id: Column[int]
    amount: Column[int]
    currency: Column[str]
    description: Column[str]
    merchant_id: Column[int]
    user_memo: Column[str]
    with_whom: Column[str]
    dimensions: Column[str]
    def update(self, values:Optional[Union[TableEntry,dict[str,Column[Any]]]]):
        """Update the entries corresponding to the keys in the dictionary if the provided confidence is higher than the one we have
        """
        if isinstance(values, TableEntry):
            self.update(values.as_dict())
        else:
            if values is None:
                return
            for key,col in values.items():
                our_column:Column = getattr(self, key)
                if our_column.confidence <= col.confidence:
                    setattr(self, key, col)
    def as_dict(self) -> dict[str,Column[Any]]:
        return {
            'id': self.id,
            'fit_id': self.fit_id,
            'time': self.time,
            'from_node_id': self.from_node_id,
            'to_node_id': self.to_node_id,
            'amount': self.amount,
            'currency': self.currency,
            'description': self.description,
            'merchant_id': self.merchant_id,
            'user_memo': self.user_memo,
            'with_whom': self.with_whom,
            'dimensions': self.dimensions
        }
    def as_ui_dict(self, database:str, iden:int) -> dict[str,Any]:
        return {
            "id": iden,
            "time": self.time.value if self.time.value else '',
            "amount": self.amount.value if self.amount.value else 0, # 85.50 * 100
            "currency": self.currency.value if self.currency.value else 'CAD',
            "description": self.description.value if self.description.value else '',
            "user_memo": self.user_memo.value if self.user_memo.value else '',
            "with_whom": json.loads(self.with_whom.value if self.with_whom.value else '[]'),
            "from_node": {
                "value": self.from_node_id.query_node_name_and_type(database),
                "confidence": self.from_node_id.confidence,
                "is_user": False
            },
            "to_node": {
                "value": self.to_node_id.query_node_name_and_type(database),
                "confidence": self.to_node_id.confidence,
                "is_user": False
            },
            "merchant": {
                "value": self.merchant_id.query_merchant_name(database),
                "confidence": self.merchant_id.confidence,
                "is_user": False
            },
            "dimensions": {
                dimension: {
                    "value": value,
                    "confidence": self.dimensions.confidence,
                    "is_user": False
                }
                for dimension,value in json.loads(self.dimensions.value if self.dimensions.value else '{}').items()
            }
        }
    @property
    def any_none(self) -> bool:
        """Whether or not there are any None values in the entry or not."""
        d = self.as_dict()
        for key,col in d.items():
            if col.value is None:
                return True
        return False
    @property
    def all_fully_confident(self) -> bool:
        """Whether or not every single value is associated with 100% confidence or not."""
        d = self.as_dict()
        for key,col in d.items():
            if col.confidence < 100:
                return False
        return True


def _construct_table_entry(values:dict[str,Column[Any]]) -> TableEntry:
    dvalues = defaultdict(lambda: Column(None,0))
    dvalues.update(values)
    return TableEntry(
        dvalues['id'], dvalues['fit_id'], dvalues['time'], dvalues['from_node_id'],
        dvalues['to_node_id'], dvalues['amount'], dvalues['currency'], dvalues['description'],
        dvalues['merchant_id'], dvalues['user_memo'], dvalues['with_whom'], dvalues['dimensions']
    )


def categorize(statement:Statement, database:str) -> list[TableEntry]:
    """Want to output the nodes and their IDs.
    Want to output the merchant id (will come from the table in the database).
    Want to output our confidence on any output we throw out too.
    Stages:
        Regex / rule-based matching,
        Fuzzy matching with existing pairs of inputs and outputs,
        Naive Bayes (or some other ML classifier).
    """
    transactions = []
    for account in statement.accounts:
        for transaction in account.transactions:
            # 1. Check for duplicates and don't output them to our list if we already have it in our database
            if is_duplicate(statement, transaction, database):
                continue
            # 2. Label the transactions with the things we absolutely know about it
            categorized = _construct_table_entry({
                'description': Column(transaction.description, 100),
                'amount': Column(transaction.amount, 100),
                'time': Column(transaction.time, 100),
                'fit_id': Column(transaction.id, 100)
            })
            # 3. Check if an exact match within the database and categorize it accordingly
            exact_match = categorize_exact_match(statement, transaction, database)
            categorized.update(exact_match)
            if categorized.all_fully_confident:
                transactions.append(categorized)
                continue
            # 4. Use Fuzzy Matching to find for almost perfect matches
            fuzzy_matched = categorize_fuzzy(statement, transaction, database)
            categorized.update(fuzzy_matched)
            # NOTE -- I don't think we need to stop here if we're fully confident. We can't be, really
            # 5. Use Machine Learning (Naive Bayes) to try to categorize it otherwise
            transactions.append(categorized)
    return transactions


def is_duplicate(statement:Statement, transaction:Transaction, database:str) -> bool:
    """Return with a `True` if we find that this is a duplicate transaction within our database.
    """
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute("""SELECT *
                 FROM Transactions
                 WHERE fit_id = ? AND amount = ?
              """, (transaction.id, transaction.amount))
    row = c.fetchone()
    conn.close()
    if row is None:
        return False
    else:
        return True


def categorize_exact_match(statement:Statement, transaction:Transaction, database:str) -> Optional[TableEntry]:
    """'No match found' is returned as a None. The check is case insensitive.
    """
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute("""SELECT from_node_id, to_node_id, currency, merchant_id, user_memo, with_whom, dimensions
                 FROM Transactions
                 WHERE description = ? COLLATE NOCASE
                 ORDER BY time DESC
                 LIMIT 5
              """, (transaction.description,))
    row = c.fetchone()
    conn.close()
    if row is None:
        # no match
        return None
    else:
        # we found a match
        return _construct_table_entry({
            d[0]: Column(v, 100) for d,v in zip(c.description, row)
        })


def categorize_fuzzy(statement:Statement, transaction:Transaction, database:str) -> Optional[TableEntry]:
    """'No match found' is returned as a None. The check is case insensitive. Returns a match if there's similarity above a certain threshold and reports confidences.

    ### Implementation details:
    1. In the query, we ORDER BY time ASC so that when we build the `rows` dictionary, the newest rows with that description overwrite the older ones.
    1. We use the `rapidfuzz.fuzz.WRatio` (weighted ratio) score to score similarity against all these descriptions in the database
    1. `rapidfuzz.process.extractOne` finds the best match and reports that score
    1. We compare the score against a threshold and report if we find it significant
    """
    # 1. Get a list of rows and their corresponding information sorted by time ASC
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute("""SELECT description, from_node_id, to_node_id, currency, merchant_id, user_memo, with_whom, dimensions
                 FROM Transactions
                 ORDER BY time ASC
              """)
    # 2. Construct a dictionary mapping description -> the other information. The oldest rows are overwritten if we find one with the same description but newer
    rows:dict[str,tuple[Any]] = {row[0].upper(): row[1:] for row in c.fetchall()}
    conn.close()
    # 3. Find the best match according to our FuzzyMatcher (WRatio)
    best_matching_description, score, _ = rapidfuzz.process.extractOne(
        transaction.description.upper(),
        rows.keys(),
        scorer=rapidfuzz.fuzz.WRatio
    )
    # 4. If its score is >= our threshold, we report it
    if score >= FUZZY_MATCH_SIGNIFICANCE_THRESHOLD:
        score = int(score) # we want the confidence to be an integer
        # construct a TableEntry and report our confidence on the rows that we grabbed from the database MINUS the description
        return _construct_table_entry({
            d[0]: Column(v, score) for d,v in zip(c.description[1:], rows[best_matching_description])
        })
    else:
        # not confident enough to even take a guess at it
        return None
