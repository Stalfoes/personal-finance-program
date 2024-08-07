import argparse
import json

parser = argparse.ArgumentParser('Convert BMO CSV statement to JSON format')
parser.add_argument('-f', '--file', required=False, default='statement.csv')
parser.add_argument('-o', '--output', required=True)
parser.add_argument('-a', '--accounts', required=True)
parser.add_argument('-b', '--balances', required=True)

args = parser.parse_args()
account_names = args.accounts.split(',')
current_balances = {a:b for a,b in zip(account_names, args.balances.split(','))}

data_to_dump = {'accounts': []}
with open(args.file, 'r') as statement_file:
    input_data = statement_file.readlines()
input_data = [line.lstrip().rstrip().split(',') for line in input_data]

current_account_index = -1
columns = []
for row in input_data:
    if len(row) == 1 and row[0] == '':
        continue
    if 'Following data is valid as of' in row[0]:
        continue
    if row[0] == 'First Bank Card':
        columns = row
        current_account_index += 1
        data_to_dump['accounts'].append(
            {
                'name':account_names[current_account_index],
                'current_balance': float(current_balances[account_names[current_account_index]]),
                'transactions': []
            }
        )
        continue
    transaction = {}
    for col,val in zip(columns,row):
        col = col.lstrip().rstrip()
        if col != 'Date Posted':
            try:
                val = float(val)
            except:
                pass
        if col == 'First Bank Card':
            val = val[1:-1]
        transaction[col] = val
    data_to_dump['accounts'][-1]['transactions'].append(transaction)

with open(args.output, 'w') as file:
    s = json.dumps(data_to_dump)
    print(s, end='', file=file)

print('Complete.')