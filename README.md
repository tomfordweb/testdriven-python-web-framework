# Routing

Routes can be defined in your main app file. You can either use a function or a class for routing.

## Function routing

```python
app = API()

@app.route('/home')
def home(request, response):
    response.text = "Hello from the HOME page"
```

## Class based routing

```python
@app.route("/book")
class BooksResource:
    def get(self, req, resp):
        resp.text = "Books Page"

    def post(self, req, resp):
        resp.text = "Endpoint to create a book"
```

# Tests
To run the tests with coverage reports...

```
pytest test_api.py
pytest --cov=. test_api.py
```
