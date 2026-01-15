# Lint

Run ruff to check and fix code style issues.

## Steps

1. Run ruff check with auto-fix:
```bash
uv run ruff check --fix .
```

2. Run ruff format:
```bash
uv run ruff format .
```

3. If there are remaining issues, show them and suggest fixes.

## Notes
- Always run both check and format
- Report summary of changes made
- If no issues found, confirm code is clean
