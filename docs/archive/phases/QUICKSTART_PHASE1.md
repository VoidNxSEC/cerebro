# Quick Start Guide - Phase 1 Testing

## Prerequisites

Ensure you have the dependencies installed:

```bash
poetry install
```

---

## Test 1: TUI Launch (Interactive Terminal)

**Simulated Test** (TUI requires interactive terminal):

```bash
# This will launch the TUI in an interactive terminal
poetry run cerebro
```

**Expected Result**:
- ASCII art logo displays
- Main menu with 6 options (1-6)
- Can navigate with number keys
- Q to quit, ESC to go back

**Note**: In non-interactive mode (piped), it automatically switches to CLI.

---

## Test 2: CLI Mode

```bash
# Force CLI with help
poetry run cerebro --help

# Existing commands should work
poetry run cerebro knowledge analyze .
poetry run cerebro ops status
```

**Expected Result**:
- Help text displays
- Existing CLI commands work normally

---

## Test 3: Environment Detection

```bash
# Test detection in different modes
python -c "from phantom.launcher import detect_environment; import sys; print(f'Mode: {detect_environment()}')"

# Test with GUI env var
CEREBRO_GUI=1 python -c "from phantom.launcher import detect_environment; print(f'Mode: {detect_environment()}')"
```

**Expected Results**:
- First command: `Mode: cli` (non-interactive)
- Second command: `Mode: gui` (env var set)

---

## Test 4: Backend API

```bash
# Start the backend server
poetry run uvicorn phantom.api.server:app --reload &
SERVER_PID=$!

# Wait for startup
sleep 3

# Test endpoints
echo "Testing /health..."
curl -s http://localhost:8000/health | jq

echo -e "\nTesting /status..."
curl -s http://localhost:8000/status | jq

echo -e "\nTesting /intelligence/query..."
curl -s -X POST http://localhost:8000/intelligence/query \
  -H "Content-Type: application/json" \
  -d '{"query":"test","limit":5}' | jq

echo -e "\nTesting /graph/dependencies..."
curl -s http://localhost:8000/graph/dependencies | jq

# Stop server
kill $SERVER_PID
```

**Expected Results**:
- All endpoints return 200 OK
- No 404 errors
- JSON responses with proper structure

---

## Test 5: WebSocket Subscription

Create a test script `test_websocket.py`:

```python
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws"

    async with websockets.connect(uri) as websocket:
        # Receive initial status
        message = await websocket.recv()
        print(f"Received: {message}")

        # Subscribe to projects topic
        await websocket.send(json.dumps({
            "type": "subscribe",
            "topic": "projects"
        }))

        # Wait for subscription confirmation
        message = await websocket.recv()
        print(f"Subscription: {message}")

        # Send ping
        await websocket.send(json.dumps({"type": "ping"}))
        pong = await websocket.recv()
        print(f"Pong: {pong}")

if __name__ == "__main__":
    asyncio.run(test_websocket())
```

Run it:

```bash
# Start server first
poetry run uvicorn phantom.api.server:app &
sleep 3

# Run WebSocket test
poetry run python test_websocket.py

# Cleanup
pkill -f uvicorn
```

**Expected Output**:
```
Received: {"type": "status", "data": {...}}
Subscription: {"type": "subscribed", "topic": "projects"}
Pong: {"type": "pong"}
```

---

## Test 6: Dashboard Integration

```bash
# Install dashboard dependencies
cd dashboard
npm install

# Start both backend and frontend
cd ..
poetry run cerebro gui
```

**Expected Result**:
- Backend starts on port 8000
- Frontend starts on port 5173
- Browser opens to dashboard
- No API 404 errors in browser console

---

## Test 7: Import Tests

```bash
# Test all imports work
poetry run python -c "
from phantom.tui.app import CerebroApp
from phantom.launcher import main, detect_environment
from phantom.tui.commands.router import CommandRouter
print('✅ All imports successful')
"
```

**Expected Output**:
```
✅ All imports successful
```

---

## Test 8: Entry Points

```bash
# Test that entry points are properly configured
which cerebro
which phantom

# Should both point to launcher
poetry run which cerebro
poetry run which phantom
```

---

## Troubleshooting

### Issue: TUI doesn't launch

**Solution**: TUI requires an interactive terminal. Test with:
```bash
poetry run python -c "import sys; print(f'stdin.isatty: {sys.stdin.isatty()}, stdout.isatty: {sys.stdout.isatty()}')"
```

Both should be `True` for TUI to launch automatically.

### Issue: Import errors

**Solution**: Ensure all dependencies installed:
```bash
poetry install
poetry show textual  # Should show 0.47.1
```

### Issue: Backend 404 errors

**Solution**: Verify paths are updated:
```bash
grep -n "intelligence/query\|graph/dependencies\|actions/scan" src/phantom/api/server.py
```

Should show lines: 312, 470, 426

### Issue: WebSocket connection fails

**Solution**: Check if backend is running:
```bash
curl http://localhost:8000/health
```

---

## Next Steps

Once Phase 1 tests pass, proceed to **Phase 2: CLI Integration** to migrate the 15 standalone scripts into unified CLI commands.

See `PHASE1_IMPLEMENTATION.md` for implementation details.
