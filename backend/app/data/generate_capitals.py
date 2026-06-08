import json
import urllib.request


REST_COUNTRIES_URL = (
    "https://restcountries.com/v3.1/all"
    "?fields=name,capital,capitalInfo,region,cca2"
)


# 193 państwa członkowskie ONZ, kody ISO 3166-1 alpha-2.
# Celowo NIE ma tutaj m.in. VA/Holy See i PS/Palestine,
# bo są państwami-obserwatorami ONZ, a nie Member States.
UN_MEMBER_CODES = {
    "AF", "AL", "DZ", "AD", "AO", "AG", "AR", "AM", "AU", "AT",
    "AZ", "BS", "BH", "BD", "BB", "BY", "BE", "BZ", "BJ", "BT",
    "BO", "BA", "BW", "BR", "BN", "BG", "BF", "BI", "CV", "KH",
    "CM", "CA", "CF", "TD", "CL", "CN", "CO", "KM", "CG", "CR",
    "CI", "HR", "CU", "CY", "CZ", "CD", "DK", "DJ", "DM", "DO",
    "EC", "EG", "SV", "GQ", "ER", "EE", "SZ", "ET", "FJ", "FI",
    "FR", "GA", "GM", "GE", "DE", "GH", "GR", "GD", "GT", "GN",
    "GW", "GY", "HT", "HN", "HU", "IS", "IN", "ID", "IR", "IQ",
    "IE", "IL", "IT", "JM", "JP", "JO", "KZ", "KE", "KI", "KW",
    "KG", "LA", "LV", "LB", "LS", "LR", "LY", "LI", "LT", "LU",
    "MG", "MW", "MY", "MV", "ML", "MT", "MH", "MR", "MU", "MX",
    "FM", "MD", "MC", "MN", "ME", "MA", "MZ", "MM", "NA", "NR",
    "NP", "NL", "NZ", "NI", "NE", "NG", "KP", "MK", "NO", "OM",
    "PK", "PW", "PA", "PG", "PY", "PE", "PH", "PL", "PT", "QA",
    "RO", "RU", "RW", "KN", "LC", "VC", "WS", "SM", "ST", "SA",
    "SN", "RS", "SC", "SL", "SG", "SK", "SI", "SB", "SO", "ZA",
    "KR", "SS", "ES", "LK", "SD", "SR", "SE", "CH", "SY", "TJ",
    "TH", "TL", "TG", "TO", "TT", "TN", "TR", "TM", "TV", "UG",
    "UA", "AE", "GB", "TZ", "US", "UY", "UZ", "VU", "VE", "VN",
    "YE", "ZM", "ZW",
}


REGION_TO_CONTINENT = {
    "Europe": "Europe",
    "Asia": "Asia",
    "Africa": "Africa",
    "Oceania": "Oceania",
    "Americas": "North America",
}


SOUTH_AMERICA_COUNTRY_CODES = {
    "AR", "BO", "BR", "CL", "CO", "EC", "GY",
    "PY", "PE", "SR", "UY", "VE",
}


def map_continent(region, cca2):
    if region == "Americas":
        if cca2 in SOUTH_AMERICA_COUNTRY_CODES:
            return "South America"
        return "North America"

    return REGION_TO_CONTINENT.get(region, region or "Unknown")


def main():
    with urllib.request.urlopen(REST_COUNTRIES_URL, timeout=30) as response:
        countries = json.loads(response.read().decode("utf-8"))

    capitals = []

    for country in countries:
        cca2 = country.get("cca2")

        if cca2 not in UN_MEMBER_CODES:
            continue

        name = country.get("name", {}).get("common")
        official_name = country.get("name", {}).get("official")
        region = country.get("region")
        capital_list = country.get("capital") or []
        capital_info = country.get("capitalInfo") or {}
        latlng = capital_info.get("latlng")

        if not name or not capital_list or not latlng or len(latlng) < 2:
            print(f"Skipped {cca2}: missing capital data")
            continue

        capital_name = capital_list[0]

        capitals.append(
            {
                "name": capital_name,
                "country": name,
                "country_code": cca2,
                "official_country_name": official_name,
                "continent": map_continent(region, cca2),
                "latitude": latlng[0],
                "longitude": latlng[1],
            }
        )

    capitals.sort(key=lambda item: (item["continent"], item["country"], item["name"]))

    output_path = "backend/app/data/capitals.json"

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(capitals, file, ensure_ascii=False, indent=2)

    generated_codes = {item["country_code"] for item in capitals}
    missing_codes = sorted(UN_MEMBER_CODES - generated_codes)

    print(f"Saved {len(capitals)} capitals to {output_path}")

    if missing_codes:
        print("Missing UN member codes:")
        print(", ".join(missing_codes))


if __name__ == "__main__":
    main()
