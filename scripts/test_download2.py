import requests

urls = [
    "https://get.enterprisedb.com/postgresql/postgresql-16.3-1-windows-x64-binaries.zip",
    "https://get.enterprisedb.com/postgresql/postgresql-15.7-1-windows-x64-binaries.zip",
    "https://get.enterprisedb.com/postgresql/postgresql-15.8-1-windows-x64-binaries.zip",
    "https://get.enterprisedb.com/postgresql/postgresql-16.4-1-windows-x64-binaries.zip"
]

for url in urls:
    try:
        r = requests.head(url)
        print(f"URL: {url} -> Status: {r.status_code}")
    except Exception as e:
        print(f"Error {url}: {e}")
