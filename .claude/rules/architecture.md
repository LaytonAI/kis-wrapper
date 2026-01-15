# Architecture

## Module Structure
```
kis/
├── __init__.py      # Public API exports
├── auth.py          # Authentication (token issue/refresh)
├── client.py        # REST API client
├── ws.py            # WebSocket client
├── domestic.py      # Domestic stock API
├── overseas.py      # Overseas stock API
├── types.py         # Type definitions
└── utils.py         # Utilities
```

## Dependency Direction
```
client.py ← domestic.py, overseas.py
    ↑
 auth.py
    ↑
 types.py, utils.py
```

## Client Pattern
- Single KISClient class for all features
- Delegate to domain modules internally

```python
client = KISClient(app_key, app_secret, account)
client.domestic.get_balance()
client.overseas.get_balance()
```

## Error Handling
- Wrap all KIS API errors in KISError
- Separate HTTP errors from business errors

```python
class KISError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
```

## Response Handling
- Use TypedDict or dataclass instead of raw dict
- Consider Pydantic models if needed

## WebSocket
- Callback-based event handling
- Auto-reconnect logic included
- Subscription management
