import requests

url = "https://sbp.enterprisedb.com/get/db/postgresql-16.3-1-windows-x64-binaries.zip"
try:
    r = requests.head(url)
    print("Status code:", r.status_code)
    print("Headers:", r.headers)
except Exception as e:
    print("Error:", e)
