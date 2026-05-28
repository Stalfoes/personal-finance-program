# How to run the app
1. Navigate to the `new_try/` directory.
1. Run `uvicorn main:app --reload`
1. Open `http://127.0.0.1:8000` in a web browser.
1. Done.

# Dependencies
1. `pip install uvicorn==0.41.0`
1. `pip install fastapi=0.129.0`
1. `pip install RapidFuzz==3.14.5`
1. `pip install ofxparse==0.21`
1. `pip install python-multipart==0.0.26`

# How it works
`uvicorn` runs the app: This is the web server listening for traffic.

FastAPI is the glue: It takes incoming web traffic and routes it to the correct Python function.

HTML is the frontend: It defines what the user sees.
This is within in the `templates/index.html` file.

When a request comes in from the HTML (like `"/api/test-htmx"`), FastAPI knows how to handle it because of the decorators (`@app.get("/api/test-htmx")`) within the Python code, `main.py`.

HTMX is another addition onto HTML that allows elements to write HTML to empty `div`s and things. Allows for more flexibility. These are seen with the `hx-get` and `hx-target` attributes. The HTMX library scans for the `hx-` attributes and turns them into background network requests.

The D3 library is usable because of the `<script src="https://d3js.org/d3.v7.min.js"></script>` line we have at the top of `templates/index.html`. Then in `static/app.js` we can use those D3 functions.

## In summary:
1. When you open `http://127.0.0.1:8000` in the web broser, it asks FastAPI for the HTML and it sends it.
1. When the browser reads HTML, it sees `<script src="/static/app.js"></script>` and asks FastAPI for the file, and FastAPI knows how to send it because of the `app.mount` line in `main.py`.
1. When I click the D3 button, the HTML triggers `drawCircles()` in the browser, because the browser has that file now.
1. Inside `drawCircles()`, the `fetch('/api/test-d3-data')` command tells the browser to ask "Hello server at 127.0.0.1, do you have anything at the `/api/test-d3-data` address for me?"
1. FastAPI listens to the request, and knows where to route it because of the `app.get()` decorator, calls it and sends it back.

# TODO:
## Completed:
1. Hook up back-end to front-end to display actual transactions and categories from the QFX sheet and Category Engine.
## To be completed:
1. Hook up front-end to back-end to save it to the database.
1. Reactively update drop-downs and figure out any Forms that have to be added to ask the user for additional information when they add something new to a dropdown.
1. Make the Description column wider so we can see the entire description rather than having to scroll it. Important for the user to be able to read it entirely.
1. Re-do the "with whom" column to allow the user to have a set of pills they can add or remove, rather than it being a list of comma-separated strings.
1. Add a "net worth statement" tab, where I can just list all the user's assets and liabilities and their sums and the net worth and their ratio.
1. Add control to my Sankey diagram that now aggregates Expenses and Incomes based on what the user selects. The categories for these are points in an N-dimensional space, so we can just take hyperplanes/hypercubes to group and aggregate data (e.g. GROUP BY for_whom,what).
1. Maybe add a section where the user can update the values of any market-valued nodes in the database. It would be probably a simple form of time, then a drop-down of the nodes, then ask the user the amount and then just save to the database.
1. Display a pop-up of a graph of a node's value over time when clicked. Maybe it just adds it to a window or tab and we can view multiple values on this graph
1. Display regressions of values in the Net Worth tab and the graph of selected values from the user
1. Allow the user to ask "what if" questions and work backwards by editing values and seeing the regressions / future predictions. This likely happens by creating a `Modifiers` table in SQL that allows us to create a "Scenario" by a name, and then specify the dimension/value that's being edited and specify its new value over some period. Like: `(ScenarioName: "2026 Dream", Dimension: "Income", NewValue: 15000000, Period: "Yearly")` or `(ScenarioName: "2026 Dream", Dimension: "Groceries", NewValue: 100000, Period: "Monthly")`. This then takes the normal baseline value and then applies the Modifiers table overtop of it and uses that instead.