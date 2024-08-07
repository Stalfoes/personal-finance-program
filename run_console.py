import swimming
import argparse

parser = argparse.ArgumentParser('Personal Finance Program', description="Used to manage personal finances", epilog="Developed by Luke Kapeluck")
parser.add_argument('-ds', '--data-source', required=True)

args = parser.parse_args()
data = {}
if args.data_source.endswith('.json'):
    from swimming.apis import from_json
    data = from_json.from_bmo_json(args.data_source)
else:
    raise NotImplementedError("Currently only JSON file inputs are supported.")

import matplotlib.pyplot as plt
for account in data['accounts']:
    transactions = [(trans['Time'],trans['Final Balance']) for trans in account['transactions']][::-1]
    x = [t[0] for t in transactions]; y = [t[1] for t in transactions]
    plt.step(x, y, where='post', label=account['name'])
plt.legend()
plt.ylabel('Balance ($)')
plt.xlabel('Time')
plt.show()

# with open('test2.json', 'w') as file:
#     import json
#     print(json.dumps(data), end='', file=file)