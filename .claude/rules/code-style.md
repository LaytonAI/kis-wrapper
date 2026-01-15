# Code Style

## Philosophy
- Short code is good code
- Remove unnecessary things
- Simplest working code is best

## Python Stack
- **Python 3.11+**
- **uv** - package manager (not pip/poetry)
- **ruff** - lint + format (not black/isort/flake8)
- **httpx** - HTTP client (not requests)
- **pytest** - testing

## Basics
- Line length: 100
- Type hints: function signatures only
- Docstrings: public API only, keep brief

## One-liners
```python
# Bad
if condition:
    return True
else:
    return False

# Good
return condition

# Bad
result = []
for item in items:
    result.append(item.upper())

# Good
result = [item.upper() for item in items]
```

## Remove Unnecessary Variables
```python
# Bad
response = requests.get(url)
data = response.json()
return data

# Good
return requests.get(url).json()
```

## Early Return
```python
# Bad
def process(data):
    if data:
        # long logic
        ...
    else:
        return None

# Good
def process(data):
    if not data: return None
    # long logic
    ...
```

## Use Assert
```python
def divide(a: int, b: int) -> float:
    assert b != 0, "divisor cannot be zero"
    return a / b
```

## Functions Over Classes
```python
# Unnecessary class
class Calculator:
    def add(self, a, b): return a + b

# Just use function
def add(a, b): return a + b
```

## Composition Over Inheritance
```python
# Bad - complex inheritance
class BaseClient: ...
class AuthMixin: ...
class HTTPClient(BaseClient, AuthMixin): ...

# Good - composition
class Client:
    def __init__(self):
        self.auth = Auth()
        self.http = HTTP()
```

## Modern Python
```python
# f-string
f"Hello {name}!"

# Walrus operator
if (n := len(items)) > 10:
    print(f"too many: {n}")

# Dict/List unpacking
merged = {**defaults, **config}
combined = [*list1, *list2]
```

## Dependencies
- Use stdlib if possible, avoid external packages
- One dependency = one tech debt

## Naming
- Short and clear
- `get_user_account_balance_from_database` → `get_balance`

## Error Handling
- No bare except
- Use if/else for normal branching
```python
# Bad
try:
    value = data["key"]
except:
    value = None

# Good
value = data.get("key")
```
