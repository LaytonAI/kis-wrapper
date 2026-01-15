# Testing

## Framework
- pytest + pytest-asyncio

## Structure
```
tests/
├── fixtures/          # Test data
│   └── responses/     # Mock API responses
├── test_auth.py
├── test_client.py
├── test_domestic.py
├── test_overseas.py
└── test_ws.py
```

## Naming
- Files: `test_*.py`
- Functions: `test_<feature>_<scenario>_<expected>`

```python
def test_get_balance_with_valid_account_returns_balance():
    ...

def test_place_order_without_token_raises_auth_error():
    ...
```

## Fixtures
- Common fixtures in conftest.py
- Save API responses as JSON in `tests/fixtures/`

## Mocking
- Never call real API (including paper trading)
- Mock httpx responses
- Use websockets.mock for WebSocket

## Coverage
- Target: 80%+
- Core logic (auth, orders): 100%

## Commands
```bash
uv run pytest                    # all tests
uv run pytest tests/test_auth.py # specific
uv run pytest --cov=kis          # with coverage
```
