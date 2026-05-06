import os
from dotenv import load_dotenv
from eansearch import EANSearch

load_dotenv()


def main():
    lookup = EANSearch(os.environ["EAN_API_TOKEN"])
    print("Ready to scan. Press Ctrl+C to quit.")
    try:
        while True:
            ean = input("Scan: ").strip()
            if not ean:
                continue
            name = lookup.barcodeLookup(ean)
            print(name if name else "Not found")
    except KeyboardInterrupt:
        print("\nDone.")


if __name__ == "__main__":
    main()
