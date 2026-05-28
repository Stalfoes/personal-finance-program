from fastapi import FastAPI, Request, Response, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates # Jinja2 is an HTML templating library. Generates HTML nicely

import sqlite3

from typing import Optional, List
import json


app = FastAPI()
# 1. Mount the static directory so the browser can find app.js
app.mount("/static", StaticFiles(directory="static"), name="static")
# 2. Setup Jinja2 to look in the /templates folder
templates = Jinja2Templates(directory="templates")


# ============================= QUERIES =============================
def sankey_query():
    conn = sqlite3.connect('fake_data.db')
    c = conn.cursor()
    c.execute("""SELECT from_node_id, to_node_id, SUM(amount) * 1.0 / 100
                FROM Transactions 
                WHERE from_node_id <> 7
                GROUP BY from_node_id, to_node_id
              """)
    links_rows = c.fetchall()
    c.execute("""SELECT n.id, n.name, n.type, COALESCE((
                SELECT SUM(amount) * 1.0 / 100 FROM Transactions WHERE to_node_id = n.id
                ),0) - COALESCE((
                SELECT SUM(amount) * 1.0 / 100 FROM Transactions WHERE from_node_id = n.id
                ),0)
                FROM Nodes n
              """)
    nodes_rows = {node_id:{"id":node_id,"label":node_name,"type":node_type.lower(),"value":value} for (node_id,node_name,node_type,value) in c.fetchall()}
    conn.close()

    # Get the set of nodes, and establish the links
    # Also, calculate the columns the nodes should be in
    for id,node_dict in nodes_rows.items():
        nodes_rows[id]["col"] = 0 #{"income":0,"asset":1,"equity":0,"expense":3,"liability":2}[node_dict['type']]

    unique_nodes = set()
    links = []
    
    for row in links_rows:
        source, target, amount = row
        links.append({"source": str(source), "target": str(target), "value": int(amount)})
        unique_nodes.update([source, target])
        nodes_rows[target]['col'] = max(nodes_rows[target]['col'], nodes_rows[source]['col'] + 1)
    # Calculate the nodes' columns once again just to try to ensure we're propogating the values correctly
    for row in links_rows:
        source, target, amount = row
        nodes_rows[target]['col'] = max(nodes_rows[target]['col'], nodes_rows[source]['col'] + 1)

    nodes = [{"id": str(nodes_rows[node]["id"]),
              "label": nodes_rows[node]["label"],
              "value": int(abs(nodes_rows[node]["value"])),
              "type": nodes_rows[node]["type"],
              "col": nodes_rows[node]["col"]} for node in unique_nodes]
    return nodes, links


cached_networth_query_values = {
    'start_date': "1999-12-01 00:00:00",
    'end_date': "2027-01-01 00:00:00"
}
def networth_query(start_date:str=None, end_date:str=None, exclude_liabilities:bool=False, exclude_assets:bool=False, exclude_networth:bool=False):
    # update our cached values
    cached_networth_query_values['start_date'] = (start_date if start_date else cached_networth_query_values['start_date'])
    start_date = cached_networth_query_values['start_date']
    cached_networth_query_values['end_date'] = (end_date if end_date else cached_networth_query_values['end_date'])
    end_date = cached_networth_query_values['end_date']


    # perform the query
    conn = sqlite3.connect('fake_data.db')
    c = conn.cursor()
    c.execute("""SELECT time,value,asset_value,liability_value
                 FROM NetWorth
                 WHERE time >= ? AND time <= ?
                 ORDER BY time ASC
              """, (start_date, end_date))
    rows = c.fetchall()
    # c.execute("""SELECT COALESCE((
    #                 SELECT SUM(amount) FROM Transactions t WHERE t.to_node_id = n.id AND t.time <= ?
    #             ), 0) - COALESCE((
    #                 SELECT SUM(amount) FROM Transactions t WHERE t.from_node_id = n.id AND t.time <= ?
    #             ), 0) AS value
    #             FROM Nodes n
    #             WHERE type = 'Asset'
    #                 AND is_market_valued = 0
    #             UNION
    #             SELECT COALESCE((
    #                 SELECT market_value FROM NodeValuations v WHERE v.node_id = n.id AND v.time <= ? ORDER BY time DESC LIMIT 1
    #             ), 0) AS value
    #             FROM Nodes n
    #             WHERE type = 'Asset'
    #                 AND is_market_valued = 1
    #           """, (TIME, TIME, TIME))
    # total_asset_value = sum(value[0] for value in c.fetchall())
    # c.execute("""SELECT COALESCE((
    #                 SELECT SUM(amount) FROM Transactions t WHERE t.from_node_id = n.id AND t.time <= ?
    #             ), 0) - COALESCE((
    #                 SELECT SUM(amount) FROM Transactions t WHERE t.to_node_id = n.id AND t.time <= ?
    #             ), 0) AS value
    #             FROM Nodes n
    #             WHERE type = 'Liability'
    #           """, (TIME, TIME))
    # total_liability_value = sum(value[0] for value in c.fetchall())
    conn.close()

    # net_worth = total_asset_value - total_liability_value    

    # new_row = {"time": TIME, "asset_value": total_asset_value, "liability_value": total_liability_value, "net_worth": net_worth},

    keys = ['time'] + (['net_worth'] if exclude_networth == False else []) + \
                      (['asset_value'] if exclude_assets == False else []) + \
                      (['liability_value'] if exclude_liabilities == False else [])

    data = [{key:value for key,value in zip(keys, row)} for row in rows]
    # Essentially transpose the data because the example they use on the D3 example site has this format
    # I think it's stupid but whatever, it stays for now until I want to play with it more
    transposed_data = []
    if exclude_networth == False:
        transposed_data = [{'time':point['time'], 'value':point['net_worth'], 'line':'Net Worth'} for point in data]
    if exclude_assets == False:
        transposed_data += [{'time':point['time'], 'value':point['asset_value'], 'line':'Asset Value'} for point in data]
    if exclude_liabilities == False:
        transposed_data += [{'time':point['time'], 'value':point['liability_value'], 'line':'Liability Value'} for point in data]        
        
    return transposed_data


def categorize_ofx_file(file:UploadFile):
    from ofx_parse_testing import parse as parse_ofx
    from ofx_parse_testing import category_engine
    statement_obj = parse_ofx.get_information(file.file)
    categorized_transactions:list[category_engine.TableEntry] = category_engine.categorize(statement_obj, 'fake_data.db')
    # TODO -- Maybe I move the conversion of TableEntry -> dict here instead of in the class
    #         Since technically it's kinda UI logic and not back end stuff 
    return [
        trans.as_ui_dict('fake_data.db', idx+1)
        for idx,trans in enumerate(categorized_transactions)
    ]


def query_global_values():
    conn = sqlite3.connect('fake_data.db')
    c = conn.cursor()
    c.execute("""WITH RECURSIVE PathBuilder AS (
                    SELECT id, name AS full_path
                    FROM DimensionValues
                    WHERE parent_id IS NULL
                    UNION ALL
                    SELECT child.id, parent.full_path || ':' || child.name AS full_path
                    FROM DimensionValues child
                    JOIN PathBuilder parent ON child.parent_id = parent.id
                )
                SELECT full_path
                FROM PathBuilder pb
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM DimensionValues dv
                    WHERE dv.parent_id = pb.id
                )
              """)
    global_dimension_leafs:list[tuple[str]] = c.fetchall()
    c.execute("SELECT pretty_name FROM Merchants")
    global_merchants:list[str] = [row[0] for row in c.fetchall()]
    c.execute("SELECT name || ' (' || type || ')' FROM Nodes")
    global_nodes:list[str] = [row[0] for row in c.fetchall()]
    conn.close()
    global_dimensions:dict[str,list[str]] = dict()
    for full_path in global_dimension_leafs:
        split_path = full_path[0].split(':')
        root = split_path[0]
        if root not in global_dimensions:
            global_dimensions[root] = []
        rest_of_path = ':'.join(split_path[1:])
        global_dimensions[root].append(rest_of_path)
    return global_nodes, global_merchants, global_dimensions


# ============================= ROUTES =============================
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # This renders the initial page structure
    return templates.TemplateResponse("index.html", {"request": request})


# The HTMX Tab Routes
@app.get("/tab/home", response_class=HTMLResponse)
async def tab_home():
    return "<h2>Home</h2><p>Welcome to your personal finance dashboard.</p>"


@app.get("/tab/sankey", response_class=HTMLResponse)
async def tab_sankey(request: Request, response: Response):
    nodes, links = sankey_query()
    chart_data = json.dumps({"nodes": nodes, "links": links})
    return templates.TemplateResponse(
        "sankey_tab.html",
        {
            "request": request,
            "chart_data": chart_data
        },
        headers={"HX-Trigger-After-Swap":"drawSankey"}
    )


@app.get("/tab/networth", response_class=HTMLResponse)
async def tab_networth(request: Request, response: Response):
    # START_DATE_DEFAULT = "1999-12-01"
    # END_DATE_DEFAULT = "2027-01-01"
    # data = networth_query(f"{START_DATE_DEFAULT} 00:00:00", f"{END_DATE_DEFAULT} 00:00:00")
    data = networth_query(None, None)
    chart_data = json.dumps({"data": data})
    return templates.TemplateResponse(
        "networth_tab.html",
        {
            "request": request,
            "chart_data": chart_data,
            "start_date": cached_networth_query_values['start_date'].split()[0],
            "end_date": cached_networth_query_values['end_date'].split()[0]
        },
        headers={"HX-Trigger-After-Swap":"drawNetworth"}
    )


# ============================= API =============================
@app.get("/api/sankey-data", response_class=HTMLResponse)
async def get_sankey_data(request: Request):
    nodes, links = sankey_query()
    ret = '<script id="chart-data" type="application/json">' + json.dumps({"nodes": nodes, "links": links}) + '</script>'
    return HTMLResponse(ret, headers={"HX-Trigger-After-Swap":"drawSankey"})


@app.get("/api/networth-data", response_class=HTMLResponse)
async def get_net_worth(request: Request,
                        start_date:Optional[str] = None, end_date:Optional[str] = None,
                        disable_networth:Optional[bool] = None, disable_assets:Optional[bool] = None, disable_liabilities:Optional[bool] = None):
    if start_date is not None:
        start_date += ' 00:00:00'
    if end_date is not None:
        end_date += ' 00:00:00'
    if disable_networth is None:
        disable_networth = False
    if disable_assets is None:
        disable_assets = False
    if disable_liabilities is None:
        disable_liabilities = False

    data = networth_query(start_date, end_date, disable_liabilities, disable_assets, disable_networth)

    ret = '<script id="chart-data" type="application/json">' + json.dumps({"data": data}) + '</script>'
    return HTMLResponse(ret, headers={"HX-Trigger-After-Swap":"drawNetworth"})


@app.post("/api/upload-ofx", response_class=HTMLResponse)
async def process_ofx_upload(request:Request, file:UploadFile = File(...)):
    global_nodes, global_merchants, global_dimensions = query_global_values()

    # The global choices available for the dropdowns
    # global_nodes = ["Chequing (Asset)", "Savings (Asset)", "Credit Card (Liability)", "Expense (Expense)", "UAlberta Pay (Income)"]
    # global_merchants = ["Walmart", "Edo Japan", "Spotify", "Steam"]
    # global_dimensions = {
    #     "WHAT": ["Food:Groceries", "Food:Dining", "Entertainment:Video Games"],
    #     'FOR_WHOM': ['Myself', 'Eric', 'Rony', 'Mackenzie', 'Dad', 'Mom'],
    #     "HOW": ["Delivery", "In-person", "Digital"],
    #     'FREQUENCY': ['One-Time', 'Subscription', 'Installment'],
    #     "WHERE": ["Canada:Alberta:Edmonton", "Japan:Honshu:Tokyo"],
    #     'PROJECT': ['JapanMarch2026'], 
    #     'FLEXIBILITY': ['Fixed', 'Variable'],
    #     'TAX_STATUS': ['Personal', 'Business Deductible', 'Medical', 'Charity'],
    #     'LIFESPAN': ['Consumable', 'Durable'],
    #     'IMPORTANCE': ['Vital', 'Important', 'Luxury', 'Waste'],
    #     'REGRET': ['None', 'Small', 'Somewhat', 'Mostly', 'Fully']
    # }

    transactions = categorize_ofx_file(file)

    return templates.TemplateResponse("components/review_table.html", {
        "request": request,
        "transactions": transactions,
        "global_nodes": global_nodes,
        "global_merchants": global_merchants,
        "global_dimensions": global_dimensions
    })


@app.post("/api/save-transactions")
async def save_reviewed_transactions(request: Request):
    # 1. Await the raw form data from the HTMX request
    form_data = await request.form()
    
    # 2. Extract the list of transaction IDs we sent in the hidden inputs
    # The name in the HTML is "tx_id[]"
    tx_ids = form_data.getlist("tx_id[]")
    
    transactions_to_save = []
    
    # 3. Loop through the IDs and pluck out their specific fields
    for tx_id in tx_ids:
        
        # Reconstruct the amount back to integer cents (e.g. "85.50" -> 8550)
        raw_amount = form_data.get(f"amount_{tx_id}", "0")
        amount_cents = int(float(raw_amount) * 100)

        # Handle the N-dimensional fields
        dimensions = {}
        for dim_key in ['WHAT', 'FOR_WHOM', 'HOW', 'FREQUENCY', 'WHERE', 'PROJECT', 'FLEXIBILITY', 'TAX_STATUS', 'LIFESPAN', 'IMPORTANCE', 'REGRET']:
            # The HTML name was dim_{id}_{dim_key}
            dimensions[dim_key] = form_data.get(f"dim_{tx_id}_{dim_key}")

        # Build the clean dictionary for this specific transaction
        tx_data = {
            "id": tx_id,
            "time": form_data.get(f"time_{tx_id}"),
            "amount": amount_cents,
            "description": form_data.get(f"desc_{tx_id}"),
            "user_memo": form_data.get(f"memo_{tx_id}"),
            "from_node": form_data.get(f"from_node_{tx_id}"),
            "to_node": form_data.get(f"to_node_{tx_id}"),
            "merchant": form_data.get(f"merchant_{tx_id}"),
            "with_whom": form_data.get(f"with_whom_{tx_id}"),
            "dimensions": dimensions
        }
        
        transactions_to_save.append(tx_data)
        
    # 4. Loop through transactions_to_save and INSERT/UPDATE into your database
    # for tx in transactions_to_save:
    #     cursor.execute(...)
    
    # Return a success message to the UI
    return HTMLResponse(
        "<div class='p-4 bg-green-100 text-green-800 rounded shadow'>"
        "✅ Successfully saved to database and updated AI training data."
        "</div>"
        "<div class='p-4 bg-green-100 text-green-800 rounded shadow'>"
        f"{repr(transactions_to_save[0])}"
        "</div>"
    )