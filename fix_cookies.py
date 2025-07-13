import json

def fix_cookies(input_file="cookies.json", output_file="cookies_fixed.json"):
    with open(input_file, "r", encoding="utf-8") as f:
        raw = json.load(f)

    fixed = []
    for cookie in raw:
        if not cookie.get("name") or not cookie.get("value"):
            continue  # skip invalid

        fixed_cookie = {
            "name": cookie["name"],
            "value": cookie["value"],
            "domain": cookie.get("domain", ".vaurioajoneuvo.fi").lstrip("."),  # remove leading dot
            "path": cookie.get("path", "/"),
            "secure": cookie.get("secure", False),
            "httpOnly": cookie.get("httpOnly", False),
            "sameSite": "Lax",  # fix here!
        }
        fixed.append(fixed_cookie)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(fixed, f, indent=2)

    print(f"[✓] Saved fixed cookies to: {output_file}")

if __name__ == "__main__":
    fix_cookies()
