import sqlite3


def get_values(upper_time:str) -> tuple[float,float,float]:
    conn = sqlite3.connect('fake_data.db')
    c = conn.cursor()
    c.execute("""SELECT COALESCE((
                    SELECT SUM(amount) FROM Transactions t WHERE t.to_node_id = n.id AND t.time <= ?
                ), 0) - COALESCE((
                    SELECT SUM(amount) FROM Transactions t WHERE t.from_node_id = n.id AND t.time <= ?
                ), 0) AS value
                FROM Nodes n
                WHERE type = 'Asset'
                    AND is_market_valued = 0
                UNION
                SELECT COALESCE((
                    SELECT market_value FROM NodeValuations v WHERE v.node_id = n.id AND v.time <= ? ORDER BY time DESC LIMIT 1
                ), 0) AS value
                FROM Nodes n
                WHERE type = 'Asset'
                    AND is_market_valued = 1
                """, (upper_time, upper_time, upper_time))
    total_asset_value = sum(value[0] for value in c.fetchall())
    c.execute("""SELECT COALESCE((
                    SELECT SUM(amount) FROM Transactions t WHERE t.from_node_id = n.id AND t.time <= ?
                ), 0) - COALESCE((
                    SELECT SUM(amount) FROM Transactions t WHERE t.to_node_id = n.id AND t.time <= ?
                ), 0) AS value
                FROM Nodes n
                WHERE type = 'Liability'
                """, (upper_time, upper_time))
    total_liability_value = sum(value[0] for value in c.fetchall())
    conn.close()
    net_worth = total_asset_value - total_liability_value
    return net_worth, total_asset_value, total_liability_value


def log_values(time:str, net_worth:float, assets:float, liabilities:float) -> None:
    conn = sqlite3.connect('fake_data.db')
    c = conn.cursor()
    try:
        c.execute("""INSERT INTO NetWorth VALUES (?,?,?,?)""", (time, net_worth, assets, liabilities))
        conn.commit()
    except sqlite3.IntegrityError as e:
        print(f"WARNING: {e} FOR TIME: {time}")
    conn.close()


import datetime

for year in [2025]:
    for month in range(1,13):
        for day in [1,15]:
            dt = datetime.datetime(year, month, day, 0, 0, 0)
            time_string = dt.strftime("%Y-%m-%d %H:%M:%S")
            nw,a,l = get_values(time_string)
            log_values(time_string, nw, a, l)
for year in [2026]:
    for month in range(1,6):
        for day in [1,15]:
            dt = datetime.datetime(year, month, day, 0, 0, 0)
            time_string = dt.strftime("%Y-%m-%d %H:%M:%S")
            nw,a,l = get_values(time_string)
            log_values(time_string, nw, a, l)