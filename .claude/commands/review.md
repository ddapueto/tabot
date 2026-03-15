Review code changes for quality, security, and correctness. Usage: /review [branch|PR-number]

Check:
1. **Security**: HMAC validation, SQL injection, XSS, hardcoded secrets, tenant isolation
2. **Quality**: type hints, error handling, edge cases, code duplication
3. **Tests**: adequate coverage, meaningful assertions, no mocked DB
4. **Architecture**: follows CLAUDE.md conventions, proper separation of concerns
5. **Performance**: N+1 queries, missing indexes, unnecessary API calls

Output a structured review with severity levels: critical, warning, suggestion.
