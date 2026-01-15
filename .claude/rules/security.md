# Security

## API Credentials
- Never hardcode APP_KEY, APP_SECRET
- Use .env file, must be in .gitignore
- Pass credentials via environment variables only

## Token Management
- Store access token in memory only
- Never save token to filesystem
- Implement auto-refresh on expiry

## Logging
- Never log credentials
- Mask sensitive info in request/response logs
  - APP_KEY: `PSXX****`
  - Account: `1234****-01`

## WebSocket
- Treat approval_key same as credentials
- Be careful with AES decryption key exposure

## Code Review Checklist
- [ ] No .env file in commit?
- [ ] No hardcoded credentials?
- [ ] No sensitive info in logs?
- [ ] No real credentials in test code?

## Dependencies
- Regular vulnerability scanning
- Use `pip-audit` or `safety`
