import json
import sys

def send_request(method, params=None):
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params or {}
    }
    json_request = json.dumps(request)
    print(json_request, flush=True)
    response = sys.stdin.readline()
    return json.loads(response)

# Initialize connection
init_request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {}
}
print(json.dumps(init_request), flush=True)
response = sys.stdin.readline()

# Test generate_job_report
test_params = {
    "title": "marker"
}

result = send_request("generate_job_report", test_params)
print("Response:", json.dumps(result, indent=2)) 