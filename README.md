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