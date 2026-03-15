Run the test suite for the specified area. Usage: /test [backend|frontend|all]

If backend: `cd backend && uv run pytest -x -v`
If frontend: `cd frontend && npm test`
If all or no argument: run both sequentially.

Report results clearly: passed, failed, errors. If failures, show the failing test name and error message.
