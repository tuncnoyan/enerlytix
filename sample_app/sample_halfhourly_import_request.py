import os
import requests

account_id = os.getenv("ETAINABL_ACCOUNT_ID", "<account-id>")
api_key = os.getenv("ETAINABL_API_KEY", "<insert-api-key>")

url = (
    "https://api.etainabl.com/2.0/consumption"
    f"?startDate=2025-12-01&endDate=2025-12-31&granularity=halfhourly&accountId={account_id}"
)

headers = {
    "accept": "application/json",
    "x-api-key": api_key,
}

response = requests.get(url, headers=headers, timeout=30)

print(response.text)