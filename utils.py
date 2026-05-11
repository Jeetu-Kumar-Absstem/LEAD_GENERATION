def extract_domain(url):
    if not url:
        return None

    url = url.replace("http://", "").replace("https://", "")
    url = url.replace("www.", "")

    return url.split("/")[0]


def flatten_emails(company, domain, emails, location=""):
    flattened = []

    for e in emails:
        flattened.append({
            "company": company,
            "domain": domain,
            "email": e.get("value"),
            "confidence": e.get("confidence"),
            "first_name": e.get("first_name"),
            "last_name": e.get("last_name"),
            "position": e.get("position") or "Unknown",
            "location": location
        })

    return flattened