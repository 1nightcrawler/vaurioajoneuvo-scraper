
# Vaurioajoneuvo Scraper

A price checker/scraper for [vaurioajoneuvo.fi](https://www.vaurioajoneuvo.fi), including a simple text-based UI and Telegram notifications for price drops.

Currently it notifies the user, when the products price is under the target price.


## Features

- Bypasses Cloudflare protection using [FlareSolverr](https://github.com/FlareSolverr/FlareSolverr)
- Watchlist-based price tracking
- Set fixed or random polling intervals
- Terminal user interface for adding/removing/editing products and polling intervals
- Sends Telegram alerts when prices drop below your target
- Should work on Windows, Linux and macOS

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/1nightcrawler/vaurioajoneuvo-scraper.git
cd vaurioajoneuvo-scraper
````

### 2. Create and activate virtual environment

**Windows**:

```bash
python -m venv .venv
.venv\Scripts\activate
```

**Linux/macOS**:

```bash
python3 -m venv .venv
source .venv/bin/activate
```
for fish use
```bash
source .venv/bin/activate.fish
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```



## Running the Program

### Launch with interactive menu:

```bash
python watcher.py
```

### Launch in watch-only mode:

```bash
python watcher.py watch
```



## Configuration

### `config.json`

You can create a `config.json` file in the project root to override defaults:

```json
{
  "interval": "random:300-600",
  "telegram_token": "123456789:ABCdefGhiJKlmNOpQRstUvWxyZ",
  "telegram_chat_id": 123456789
}
```

* `interval`: seconds (e.g. `"300"`), minutes (`"5m"`), or random (`"random:60-300"`)
* `telegram_token` and `telegram_chat_id`: to enable Telegram alerts

### How to Get Your Telegram Chat ID

To receive Telegram notifications, you'll need:

- A **Telegram Bot Token** (from [@BotFather](https://t.me/BotFather))
- Your **Chat ID**

The bot token will be given to you by [@BotFather](https://t.me/BotFather)

#### Steps to get your chat ID:

1. **Start a conversation with your bot**:
   - Go to Telegram and search for your bot using the name you set with BotFather.
   - Send any message (e.g., "Hello").

2. **Get your Chat ID using this link**:
  ```https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates```
  - Replace `<YOUR_BOT_TOKEN>` with your actual token.

3. **Look for this in the JSON response**:
  ```json
  {
    "message": {
      "chat": {
        "id": 123456789,
        ...
      }
    }
  }
  ```
  - The id field is your telegram_chat_id.


## FlareSolverr

To bypass Cloudflare challenges, you need [FlareSolverr](https://github.com/FlareSolverr/FlareSolverr) running locally.

### Start via Docker:

```bash
docker run -d \
  --name flaresolverr \
  -p 8191:8191 \
  ghcr.io/flaresolverr/flaresolverr:latest
```

Make sure it's accessible at `http://localhost:8191`.



## Files

* `watcher.py`: main script
* `products.json`: product watchlist (auto-created)
* `config.json`: config for polling interval and Telegram
* `requirements.txt`: dependencies



## Example `products.json`

```json
[
  {
    "url": "https://www.vaurioajoneuvo.fi/tuote/example/",
    "target_price": 3500,
    "name": "Example"
  }
]
```

Adding, removing and editing products can be done through the TUI. 
Manual editing is also possible by modifying the `products.json` file.

## To-Do

* [ ] Add browser fallback for manual solving
* [ ] Export results
* [ ] Auto-retry failed requests

## Cleaning Up

To regenerate `requirements.txt` with only used libraries:

```bash
pip freeze > requirements.txt
```

## License

MIT License — use freely, credit appreciated.



## Author

Created by [@1nightcrawler]([https://github.com/yourhandle](https://github.com/1nightcrawler))

