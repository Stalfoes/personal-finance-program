import json
from swimming.core import helper

def from_bmo_json(filename):
    data: dict
    with open(filename, 'r') as file:
        data = json.loads(file.read())
    for account in data['accounts']:
        account_current_balance = account['current_balance']
        transactions = []
        old_transactions = account['transactions']
        old_transactions = [old_transactions[i] for i in sorted(range(len(old_transactions)), key=lambda i:(old_transactions[i]['Date Posted'],i), reverse=True)]
        for trans in old_transactions:
            change = trans['Transaction Amount']
            final_balance = account_current_balance if len(transactions) == 0 else transactions[-1]['Starting Balance']
            starting_balance = final_balance - change
            transactions.append({
                # "First Bank Card": trans['First Bank Card'],
                # "Transaction Type": trans['Transaction Type'],
                "Time": helper.from_yyyymmdd_to_time(trans['Date Posted']),
                "Change": change,
                "Description": trans['Description'],
                'Final Balance': final_balance,
                'Starting Balance': starting_balance
            })
        account['transactions'] = transactions
    return data