import requests
from bs4 import BeautifulSoup

url = "https://www.vaurioajoneuvo.fi/tuote/volkswagen-4d-polo-hatchback-1-2-9n-245-jfx-141/"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.vaurioajoneuvo.fi/"
}

cookies = {
    "cf_clearance": "4XlLSG7gBl2JOr9sRNjLmHx0nzqP9r2IQTGOYqdZgxc-1752117022-1.2.1.1-E7Bb3s.XdJ2UdgJX6rZSm56KChRu8ATUnQVRkmfQzND6rMvBq5pa2Y8_cVow8uG4c0cnOdUUe0hjl8_43yADB4HsjyBO5IcxD3e038k98JH9u6_rsD.Zz8DlG89SRhjIeDKO1xOeVrVxsGmn3SZ_SQH8wYEjJNc_afxeEBnztNUWXzXcXf8JdkRnRXsW4VE.yHy8yauK1KQD7FSq2HmKzR.vIh7AZrBYjLBwAHaZQ0o",
    "_ga": "GA1.2.411728901.1752117019",
    "_gid": "GA1.2.1234059516.1752117019",
    "_gat": "1",
    "svt-buyers": "2abdad73cde7ef7f8619af83963a908efecaad80",
    "CookieConsent": "{stamp:'4xtVMt3lrjYK22nJi+9XGlRaq7VmEfirYWjBiVwabf8gWvwvTCdWRA==',necessary:true,preferences:false,statistics:false,marketing:false,method:'explicit',ver:1,utc:1752117024919,region:'ee'}"
}

response = requests.get(url, headers=headers, cookies=cookies)

soup = BeautifulSoup(response.text, "html.parser")
price_tag = soup.find("p", class_="price")

if price_tag:
    print("Price found:", price_tag.get_text(strip=True))
else:
    print("⚠️ Price not found.")
