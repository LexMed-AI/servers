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

# Test generate_job_report for Call-Out Operator
test_params = {
    "title": "Call-Out Operator"
}

result = send_request("generate_job_report", test_params)
print("Response:", json.dumps(result, indent=2)) 