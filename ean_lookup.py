import os
import requests
from openai import OpenAI
from dotenv import load_dotenv
from eansearch import EANSearch

load_dotenv()

COUNTRY = "DK"
JUSTWATCH_IMAGE_BASE = "https://images.justwatch.com"

openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

JUSTWATCH_HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Origin": "https://www.justwatch.com",
    "Referer": "https://www.justwatch.com/",
}

JUSTWATCH_QUERY = """
query SearchTitles($query: String!, $country: Country!) {
  popularTitles(country: $country, first: 1, filter: {searchQuery: $query}) {
    edges {
      node {
        content(country: $country, language: "en") {
          title
          fullPath
          originalTitle
          shortDescription
          runtime
          originalReleaseYear
          ageCertification
          genres { shortName }
          posterUrl
          scoring { imdbScore imdbVotes tmdbScore }
          externalIds { imdbId tmdbId }
          credits { role name }
        }
        offers(country: $country, platform: WEB) {
          monetizationType
          standardWebURL
          package { clearName icon }
        }
      }
    }
  }
}
"""

GENRE_NAMES = {
    "act": "Action", "ani": "Animation", "cmd": "Comedy", "crm": "Crime",
    "doc": "Documentary", "drm": "Drama", "fnt": "Fantasy", "hrr": "Horror",
    "msc": "Music", "rom": "Romance", "scf": "Sci-Fi", "spt": "Sport",
    "trl": "Thriller", "wsn": "Western", "fml": "Family", "his": "History",
    "war": "War", "bio": "Biography", "mys": "Mystery", "adv": "Adventure",
}


def normalize_title(raw: str) -> str:
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You convert messy DVD/Blu-ray product titles into clean canonical English movie or TV show titles. "
                    "Handle abbreviations, disc numbers, foreign language subtitles, and series numbering. "
                    "Reply with only the canonical title, nothing else."
                ),
            },
            {"role": "user", "content": raw},
        ],
        max_tokens=50,
        temperature=0,
    )
    return response.choices[0].message.content.strip()


def find_movie(title: str) -> dict | None:
    r = requests.post(
        "https://apis.justwatch.com/graphql",
        json={"query": JUSTWATCH_QUERY, "variables": {"query": title, "country": COUNTRY}},
        headers=JUSTWATCH_HEADERS,
        timeout=10,
    )
    edges = r.json().get("data", {}).get("popularTitles", {}).get("edges", [])
    if not edges:
        return None

    node = edges[0]["node"]
    c = node["content"]

    # Build poster URL
    poster = None
    if c.get("posterUrl"):
        poster = JUSTWATCH_IMAGE_BASE + c["posterUrl"].replace("{profile}", "s592").replace("{format}", "jpg")

    # Separate flatrate vs rent/buy, dedupe by service name
    streaming, rent_buy = {}, {}
    for offer in node.get("offers", []):
        name = offer["package"]["clearName"]
        icon = JUSTWATCH_IMAGE_BASE + offer["package"]["icon"].replace("{profile}", "s100").replace("{format}", "png")
        entry = {"name": name, "url": offer["standardWebURL"], "icon": icon}
        if offer["monetizationType"] == "FLATRATE":
            streaming.setdefault(name, entry)
        else:
            rent_buy.setdefault(name, entry)

    # Cast and directors
    cast = [cr["name"] for cr in c.get("credits", []) if cr["role"] == "ACTOR"][:10]
    directors = [cr["name"] for cr in c.get("credits", []) if cr["role"] == "DIRECTOR"]

    return {
        "title": c.get("title"),
        "original_title": c.get("originalTitle"),
        "year": c.get("originalReleaseYear"),
        "runtime_min": c.get("runtime"),
        "age_certification": c.get("ageCertification"),
        "description": c.get("shortDescription"),
        "genres": [GENRE_NAMES.get(g["shortName"], g["shortName"]) for g in c.get("genres", [])],
        "imdb_score": c.get("scoring", {}).get("imdbScore"),
        "imdb_votes": c.get("scoring", {}).get("imdbVotes"),
        "tmdb_score": c.get("scoring", {}).get("tmdbScore"),
        "imdb_id": c.get("externalIds", {}).get("imdbId"),
        "tmdb_id": c.get("externalIds", {}).get("tmdbId"),
        "justwatch_url": "https://www.justwatch.com" + c.get("fullPath", ""),
        "poster": poster,
        "cast": cast,
        "directors": directors,
        "streaming": list(streaming.values()),
        "rent_buy": list(rent_buy.values()),
    }


C_RESET  = "\033[0m"
C_BOLD   = "\033[1m"
C_DIM    = "\033[2m"
C_YELLOW = "\033[93m"
C_CYAN   = "\033[96m"
C_GREEN  = "\033[92m"
C_BLUE   = "\033[94m"
C_RED    = "\033[91m"
C_WHITE  = "\033[97m"


def fmt_runtime(minutes):
    if not minutes:
        return "?"
    h, m = divmod(minutes, 60)
    return f"{h}h {m:02d}m" if h else f"{m}m"


def print_movie(movie, ean):
    W = 60
    line = "─" * W

    cert = f"[{movie['age_certification']}]" if movie['age_certification'] else ""
    runtime = fmt_runtime(movie['runtime_min'])
    title_line = f"{movie['title']} ({movie['year']})"

    print(f"\n{C_YELLOW}{C_BOLD}┌{line}┐{C_RESET}")
    print(f"{C_YELLOW}{C_BOLD}│{C_WHITE}{C_BOLD}  {title_line:<{W-2}}{C_YELLOW}│{C_RESET}")
    if movie['original_title'] and movie['original_title'] != movie['title']:
        orig = f"  {movie['original_title']}"
        print(f"{C_YELLOW}│{C_DIM}{orig:<{W}}{C_YELLOW}│{C_RESET}")
    print(f"{C_YELLOW}│{C_CYAN}  {cert}  {runtime}{'':>{W - len(cert) - len(runtime) - 5}}{C_YELLOW}│{C_RESET}")
    print(f"{C_YELLOW}├{line}┤{C_RESET}")

    # Ratings
    imdb = f"IMDB {movie['imdb_score']} ({int(movie['imdb_votes'] or 0):,} votes)" if movie['imdb_score'] else "IMDB N/A"
    tmdb = f"TMDB {movie['tmdb_score']}" if movie['tmdb_score'] else "TMDB N/A"
    ratings = f"  {imdb}   {tmdb}"
    print(f"{C_YELLOW}│{C_GREEN}{ratings:<{W}}{C_YELLOW}│{C_RESET}")

    # Genres
    genres = "  " + ", ".join(movie['genres']) if movie['genres'] else "  —"
    print(f"{C_YELLOW}│{C_DIM}{genres:<{W}}{C_YELLOW}│{C_RESET}")
    print(f"{C_YELLOW}├{line}┤{C_RESET}")

    # Description (word-wrap)
    desc = movie['description'] or "No description available."
    words, current = desc.split(), ""
    for word in words:
        if len(current) + len(word) + 1 > W - 4:
            print(f"{C_YELLOW}│{C_RESET}  {current:<{W-2}}{C_YELLOW}│{C_RESET}")
            current = word
        else:
            current = f"{current} {word}".strip()
    if current:
        print(f"{C_YELLOW}│{C_RESET}  {current:<{W-2}}{C_YELLOW}│{C_RESET}")
    print(f"{C_YELLOW}├{line}┤{C_RESET}")

    # Cast & directors
    if movie['directors']:
        dirs = "  Dir: " + ", ".join(movie['directors'])
        print(f"{C_YELLOW}│{C_BLUE}{dirs:<{W}}{C_YELLOW}│{C_RESET}")
    if movie['cast']:
        cast = "  Cast: " + ", ".join(movie['cast'])
        # wrap if too long
        if len(cast) > W:
            cast = cast[:W-3] + "..."
        print(f"{C_YELLOW}│{C_RESET}{cast:<{W}}{C_YELLOW}│{C_RESET}")
    print(f"{C_YELLOW}├{line}┤{C_RESET}")

    # Streaming
    if movie['streaming']:
        print(f"{C_YELLOW}│{C_GREEN}  ▶ Streaming:{C_RESET}")
        for s in movie['streaming']:
            print(f"{C_GREEN}    {s['name']}: {s['url']}{C_RESET}")
    else:
        print(f"{C_YELLOW}│{C_DIM}  Not streaming in DK{C_RESET}")
    if movie['rent_buy']:
        print(f"{C_YELLOW}│{C_RESET}  Rent/Buy:")
        for s in movie['rent_buy']:
            print(f"    {s['name']}: {s['url']}")

    # EAN + poster + JustWatch
    print(f"{C_YELLOW}├{line}┤{C_RESET}")
    ean_line = f"  EAN: {ean}"
    print(f"{C_YELLOW}│{C_DIM}{ean_line:<{W}}{C_YELLOW}│{C_RESET}")
    if movie['poster']:
        print(f"{C_YELLOW}│{C_DIM}  Poster: {movie['poster']}{C_RESET}")
    print(f"{C_DIM}  JustWatch: {movie['justwatch_url']}{C_RESET}")
    print(f"{C_YELLOW}{C_BOLD}└{line}┘{C_RESET}\n")


def main():
    lookup = EANSearch(os.environ["EAN_API_TOKEN"])
    print(f"\n{C_CYAN}{C_BOLD}  DVD Orama Scanner  {C_RESET}")
    print(f"{C_DIM}  Press Ctrl+C to quit\n{C_RESET}")
    try:
        while True:
            ean = input(f"{C_YELLOW}Scan ▶ {C_RESET}").strip()
            if not ean:
                continue
            raw_name = lookup.barcodeLookup(ean)
            if not raw_name:
                print(f"{C_RED}  Barcode not found{C_RESET}\n")
                continue

            clean_name = normalize_title(raw_name)
            print(f"{C_DIM}  Looking up: {clean_name}…{C_RESET}")
            movie = find_movie(clean_name)

            if not movie:
                print(f'{C_RED}  No data found for "{clean_name}"{C_RESET}\n')
                continue

            print_movie(movie, ean)
    except KeyboardInterrupt:
        print(f"\n{C_DIM}  Done.{C_RESET}\n")


if __name__ == "__main__":
    main()
