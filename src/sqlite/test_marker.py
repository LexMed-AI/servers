import json
import sys
import time

# Initialize request
init_request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "0.1.0",
        "capabilities": {},
        "clientInfo": {
            "name": "test-client",
            "version": "1.0.0"
        }
    }
}

# Send initialization request
print(json.dumps(init_request))
sys.stdout.flush()

# Read initialization response
response = sys.stdin.readline()
if not response:
    sys.exit("No response received from server")

# Tool request
tool_request = {
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
        "name": "generate_job_report",
        "arguments": {
            "title": "marker"
        }
    }
}

# Send tool request
print(json.dumps(tool_request))
sys.stdout.flush()

# Read tool response
response = sys.stdin.readline()
if response:
    print("Response:", response, file=sys.stderr) 