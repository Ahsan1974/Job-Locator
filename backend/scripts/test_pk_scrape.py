import json
import re

from curl_cffi import requests

r = requests.get(
    "https://www.naukrigulf.com/java-jobs-in-pakistan",
    impersonate="chrome120",
    timeout=30,
)
print("status", r.status_code, len(r.text))
for pat in ["__NEXT_DATA__", "__INITIAL_STATE__", "jobList", "srp"]:
    print(pat, pat in r.text)

m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text, re.DOTALL)
if m:
    data = json.loads(m.group(1))
    print("next keys", data.keys())
    props = data.get("props", {}).get("pageProps", {})
    print("pageProps keys", list(props.keys())[:20])

# Indeed PK embedded data pattern
r2 = requests.get(
    "https://pk.indeed.com/jobs?q=java&l=Karachi",
    impersonate="chrome120",
    timeout=30,
)
print("indeed", r2.status_code)
if r2.status_code == 200:
    if "mosaic.Provider" in r2.text or "_initialData" in r2.text:
        print("indeed has embedded data")
