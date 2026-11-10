import json
import urllib.request
import urllib.error

url = "http://127.0.0.1:8000/api/roast"
payload = {
    "repo_url": "https://github.com/DsSrujan/Major_project.git",
    "mode": "nuclear",
}

req = urllib.request.Request(
    url,
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST"
)

print("🔥 Sending test request to your local server...")
try:
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode("utf-8"))
        print("\n--- ROAST RESULT ---")
        print(f"Commits analyzed: {result['commits_analyzed']}")
        print(result['story'])
        print("--------------------")
except urllib.error.HTTPError as e:
    error_body = e.read().decode("utf-8")
    print(f"❌ HTTP Error {e.code}: {error_body}")
except Exception as e:
    print(f"❌ Error: {e}")