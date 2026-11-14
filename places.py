"""Find places related to an interest using the Google Places API (New).

Setup:
  1. Enable "Places API (New)" in Google Cloud and create an API key.
  2. Put it in a .env file (already gitignored) or your environment:
         GOOGLE_MAPS_API_KEY=your_key_here
"""
import json
import os
import urllib.error
import urllib.request

SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"

# Search phrasing for each interest (more specific than the bare keyword).
QUERIES = {
    "anime": "anime store or manga shop",
    "food": "restaurant",
    "gaming": "video game store or arcade",
    "sports": "sports center or stadium",
    "alcohol": "bar or pub",
    "museum": "museum",
    "culture": "cultural attraction or theater",
    "art": "art gallery",
}

FIELDS = [
    "places.displayName",
    "places.formattedAddress",
    "places.location",
    "places.rating",
    "places.userRatingCount",
    "places.googleMapsUri",
]


def _load_env(path=".env"):
    """Minimal .env loader so no extra dependency is needed."""
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip("'\""))


def find_places(interest, location=None, max_results=10, api_key=None):
    """Return a list of places for `interest`.

    interest:  a key of QUERIES (or any free-text search).
    location:  optional text like "Montreal" appended to the query,
               or a (lat, lng) tuple to bias results around that point.
    """
    _load_env()
    api_key = api_key or os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        raise RuntimeError("Set GOOGLE_MAPS_API_KEY in your environment or .env")

    query = QUERIES.get(interest, interest)
    body = {"pageSize": max_results}
    if isinstance(location, tuple):
        lat, lng = location
        body["locationBias"] = {
            "circle": {"center": {"latitude": lat, "longitude": lng}, "radius": 5000.0}
        }
    elif location:
        query = f"{query} in {location}"
    body["textQuery"] = query

    req = urllib.request.Request(
        SEARCH_URL,
        data=json.dumps(body).encode(),
        headers={
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": ",".join(FIELDS),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Places API error {e.code}: {e.read().decode()}") from e

    return [
        {
            "name": p.get("displayName", {}).get("text"),
            "address": p.get("formattedAddress"),
            "lat": p.get("location", {}).get("latitude"),
            "lng": p.get("location", {}).get("longitude"),
            "rating": p.get("rating"),
            "ratings_count": p.get("userRatingCount"),
            "maps_url": p.get("googleMapsUri"),
        }
        for p in data.get("places", [])
    ]


if __name__ == "__main__":
    import sys

    for place in find_places(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None):
        print(f"{place['name']} ({place['rating']}) - {place['address']}\n  {place['maps_url']}")
