from ofxparse import OfxParser
from typing import Union,Any
import csv


# print({
#     'account': ofx.account,
#     'accounts': None,
#     'headers': ofx.headers,
#     'signon': {
#         'code': ofx.signon.code,
#         'dtprofup': ofx.signon.dtprofup,
#         'dtserver': ofx.signon.dtserver,
#         'fi_fid': ofx.signon.fi_fid,
#         'fi_org': ofx.signon.fi_org,        # if this is included, it seems to be the printed name of the bank
#         'intu_bid': ofx.signon.intu_bid,
#         'language': ofx.signon.language,
#         'message': ofx.signon.message,
#         'severity': ofx.signon.severity,
#         'success': ofx.signon.success,
#     },
#     'status': ofx.status,
#     'trnuid': ofx.trnuid,
# })

# print('----------------')

# print([{
#     'account_id': account.account_id,
#     'account_type': account.account_type,
#     'branch_id': account.branch_id,
#     'curdef': account.curdef,                   # currency (CAD, USD)
#     'institution': account.institution,
#     'number': account.number,
#     'routing_number': account.routing_number,
#     'statement': account.statement,        # 'available_balance', 'available_balance_date', 'balance', 'balance_date', 'currency', 'discarded_entries', 'end_date', 'start_date', 'transactions', 'warnings
#     'type': account.type,
# } for account in ofx.accounts])

# print('----------------')

# print({
#     'available_balance': ofx.accounts[0].statement.available_balance,           # Decimal('xxx.xx')
#     'available_balance_date': ofx.accounts[0].statement.available_balance_date, # datetime.datetime
#     'balance': ofx.accounts[0].statement.balance,                               # Decimal('xxx.xx')
#     'balance_date': ofx.accounts[0].statement.balance_date,                     # datetime.datetime
#     'currency': ofx.accounts[0].statement.currency,                             # cad
#     'discarded_entries': ofx.accounts[0].statement.discarded_entries,
#     'end_date': ofx.accounts[0].statement.end_date,                             # datetime.datetime
#     'start_date': ofx.accounts[0].statement.start_date,                         # datetime.datetime
#     'transactions': ofx.accounts[0].statement.transactions,                     # a list of <Transaction units=xx.xx>
#     'warnings': ofx.accounts[0].statement.warnings,
# }) # 'available_balance', 'available_balance_date', 'balance', 'balance_date', 'currency', 'discarded_entries', 'end_date', 'start_date', 'transactions', 'warnings'

# print('----------------')

# print([{
#     'payee': transaction.payee,                 # NAME
#     'type': transaction.type,                   # debit, credit, other
#     'date': transaction.date,                   # datetime.datetime
#     'user_date': transaction.user_date,         # Optional[?]
#     'amount': transaction.amount,               # Decimal
#     'id': transaction.id,                       # some semi-unique identifier
#     'memo': transaction.memo,                   # a string, idk what though
#     'sic': transaction.sic,                     # Optional[?]
#     'mcc': transaction.mcc,                     # string, idk what though
#     'checknum': transaction.checknum,           # string, idk what though
# } for transaction in ofx.accounts[0].statement.transactions])

from dataclasses import dataclass
@dataclass
class Transaction:
    id: str
    name: str
    memo: str
    amount: int
    time: str
    @property
    def description(self):
        return self.name + self.memo
@dataclass
class Account:
    id: str
    balance: int
    time: str
    transactions: list[Transaction]
@dataclass
class Statement:
    institution: str
    accounts: list[Account]


def _clean(x:str) -> str:
    return ' '.join(x.split())


def get_institution_name(qfx:Any, intu_bid_lookup_filepath:str="D:/Documents/Home/Finance/new_try/ofx_parse_testing/intu_bid_lookup.tsv"):
    UNKNOWN_STRING = "Unknown Bank"
    intu = None
    if qfx.signon is not None:
        if qfx.signon.intu_bid is not None:
            intu = qfx.signon.intu_bid
        elif qfx.signon.fi_fid is not None:
            intu = qfx.signon.fi_fid
    if intu is None:
        return UNKNOWN_STRING
    with open(intu_bid_lookup_filepath, 'r', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter='\t')
        next(reader) # skip the file header
        for row in reader:
            if row[0] == intu:
                return row[1]
    return UNKNOWN_STRING


def get_information(file:Union[str,Any]) -> Statement:
    """Parse the information from a QFX (.qfx) or OFX (.ofx) file into a `Statement` object.
    """
    # 1. Open the file and get the ofx object from OfxParser.parse()
    if isinstance(file, str):
        with open(file, 'rb') as file_obj:
            ofx = OfxParser.parse(file_obj)
    else:
        ofx = OfxParser.parse(file)
    # 2. Construct the Statement object and its internal Account and Transaction objects
    accounts = []
    for account in ofx.accounts:
        account_obj = Account(account.account_id, int(account.statement.balance * 100), account.statement.balance_date.strftime("%Y-%m-%d %H:%M:%S"), [])
        for tx in account.statement.transactions:
            account_obj.transactions.append(Transaction(
                tx.id,
                _clean(tx.payee),
                _clean(tx.memo),
                int(abs(tx.amount) * 100), # -55.253 => 5525 (positives and x100 and rounded)
                tx.date.strftime("%Y-%m-%d %H:%M:%S")
            ))
        accounts.append(account_obj)
    return Statement(get_institution_name(ofx), accounts)


def pretty_print_information(statement_information: Statement):
    memo_color_code = '\033[0;34m'
    print('===============================================================================')
    print(f'INSTITUTION = {statement_information.institution}')
    for account in statement_information.accounts:
        print('===============================================================================')
        print(f'Account with id={account.id} has balance={account.balance} at time={account.time}')
        if len(account.transactions) > 0:
            print('-----------------')
        for tx in account.transactions:
            name = _clean(tx.name)
            memo = _clean(tx.memo)
            amount = tx.amount / 100
            date = tx.time
            tx_id = tx.id
            if amount < 0:
                print(f"{tx_id:<35}| {date} | ${abs(amount):.2f} to {name}{memo_color_code}{memo}\033[0m")
            elif amount > 0:
                print(f"{tx_id:<35}| {date} | ${abs(amount):.2f} from {name}{memo_color_code}{memo}\033[0m")
            else:
                print(f"{tx_id:<35}| {date} | ** zero dollar transaction? ${abs(amount)} with name={name}{memo_color_code}{memo}\033[0m")
    print('===============================================================================')


if __name__ == '__main__':
    BMO = "D:/Documents/Home/Finance/new_try/ofx_parse_testing/bmo.ofx"
    BMO_CC = "D:/Documents/Home/Finance/new_try/ofx_parse_testing/bmo_cc.ofx"
    TANGERINE = "D:/Documents/Home/Finance/new_try/ofx_parse_testing/tangerine.QFX"
    BMO_QFX = "D:/Documents/Home/Finance/new_try/ofx_parse_testing/bmo.qfx"

    pretty_print_information(get_information(BMO))
    pretty_print_information(get_information(BMO_CC))
    pretty_print_information(get_information(TANGERINE))
    pretty_print_information(get_information(BMO_QFX))

    """
    payee(payee+memo) has to match a node or create a new node. We ideally want to match it to already existing nodes that exist.
    Maybe expenses aren't necessarily nodes but rather just a series of tags that we can create nodes from depending on how we want to see things?
        Yes, probably best. "Global Expenses" and "Global Incomes" seems like the way to go
        The only data needed to classify an Expense or Income is its location (point) within the N-dimensional space of labels/categories
    Because the tags are somewhat like an n-dimensional venn-diagram of sorts where they can overlap in any number of ways.
    Would it be a right move to display them mostly as nodes rather than just a series of tags themselves?
        I think we let the user say how we want them to be GROUPED BY
        For example, the user wants to see Expenses split along the WHO axis, then we only see money come out like "Asset -> {Myself, Dad, Mom, Rony, Mackenzie...}"
        Or if the user wants Expenses split along the WHAT axis then they see money move like "Asset -> {Food, Entertainment, Travel, ...}"
        Maybe if they want to split along both then we get stuff like: "Asset -> {Food+Rony, Food+Myself, Entertainment+Myself, Entertainment+Rony, Gifts+Dad, Gifts+Mom, ...}"
        If the user does not want it split at all, then it's a black hole of "Global Expenses" enveloping it all.
    """