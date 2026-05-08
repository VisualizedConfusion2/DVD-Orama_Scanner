# DVD Orama Scanner

A CLI tool that scans DVD/Blu-ray barcodes and automatically looks up movie metadata, streaming availability, ratings, and sends the data to the DVD Orama backend.

## How it works

1. You scan (or type) a barcode EAN number
2. The EAN is looked up via the [EAN-Search](https://www.ean-search.org/) API to get the raw product title
3. OpenAI GPT-4o-mini cleans and normalizes the title (handles abbreviations, foreign subtitles, disc numbers, etc.)
4. [JustWatch](https://www.justwatch.com/) is queried for full movie metadata: ratings, genres, cast, streaming services in Denmark
5. The result is printed to the terminal and posted to the backend API

## Requirements

- Python 3.10+
- A virtual environment (recommended)

## Setup

### 1. Clone the repo and create a virtual environment

```bash
git clone <repo-url>
cd DVD-Orama_Scanner

python -m venv venv
source venv/bin/activate       # Linux/macOS
# or
venv\Scripts\activate          # Windows
```

### 2. Install dependencies

```bash
pip install openai eansearch python-dotenv requests
```

### 3. Configure the `.env` file

Create a `.env` file in the project root:

```
OPENAI_API_KEY=your_openai_api_key_here
EAN_API_TOKEN=your_ean_search_token_here
BACKEND_URL=http://localhost:5178
```

| Variable         | Description                                                                 | Required |
|------------------|-----------------------------------------------------------------------------|----------|
| `OPENAI_API_KEY` | OpenAI API key — get one at [platform.openai.com](https://platform.openai.com/api-keys) | Yes |
| `EAN_API_TOKEN`  | EAN-Search API token — get one at [ean-search.org](https://www.ean-search.org/)       | Yes |
| `BACKEND_URL`    | URL where the [DVD Orama REST backend](https://github.com/VisualizedConfusion2/DVD-Orama_Services-rest/) is hosted (e.g. `http://localhost:5178` when running locally) | No  |

> **Note:** Never commit your `.env` file. It is already listed in `.gitignore`.

## Running the scanner

```bash
source venv/bin/activate   # if not already active
python ean_lookup.py
```

You will see:

```
  DVD Orama Scanner
  Press Ctrl+C to quit

Scan ▶ 
```

Type or scan a barcode EAN and press Enter. The movie info will be printed and saved to the backend. Press `Ctrl+C` to quit.
