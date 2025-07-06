# Auto LinkedIn Poster

This project automates creation and publishing of daily LinkedIn posts (article-style text, an explanatory graph and optional slides) on a user-defined topic.

## Features

* Fetches fresh web content every 24 h using a simple Google search scrape.
* Summarises the most relevant articles with a local, **free** open-source LLM (`distilbart-cnn-6-6`).
* Builds a search-interest graph with **pytrends** and embeds it into the post.
* Optionally produces a one-slide PowerPoint deck with the key take-aways.
* Publishes directly to LinkedIn via the official REST v2 API.

## Quick start

1. Install dependencies

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

2. Export required environment variables (see table below).
3. Run once to test:

```bash
python src/main.py --topic "quantum computing"
```

4. Schedule daily execution with `cron` (example: 07:05 every morning):

```cron
5 7 * * * /usr/bin/python /path/to/workspace/src/main.py --topic "quantum computing" >> /path/to/workspace/post.log 2>&1
```

### Environment variables

| Variable | Purpose |
|----------|---------|
| `LINKEDIN_ACCESS_TOKEN` | OAuth2 Access Token with `w_member_social` scope |
| `LINKEDIN_MEMBER_URN`   | Your member URN, e.g. `urn:li:person:xxxxxxxx` |
| `HUGGINGFACE_TOKEN`     | *(Optional)* improves inference speed when downloading models |

## Legal note

Automated posting may violate LinkedIn's Terms of Service. Use this project at your own risk.

## Deployment on a free MCP server

Any cloud that lets you run a small scheduled container for free will do. A popular choice is **Render's free "background worker"** tier (but feel free to use Fly.io, Railway, or a spare VPS):

1. Push this repo to your own GitHub account.
2. Create a new **Background Worker** on Render, pointing to your repository.
3. Set the start command to:

```bash
python src/main.py --topic "quantum computing"
```

4. Add the required environment variables under the *Environment* tab.
5. In the **Advanced** settings, toggle *Start on deploy* **off** and instead add a *Cron Job* set to run every 24 h at your desired time. The Cron job command should be the same as the start command above.

Render's free tier gives 550 free runtime hours/month, which is enough for this once-a-day task.

## LinkedIn API Setup

Follow these steps to obtain the `LINKEDIN_ACCESS_TOKEN` and `LINKEDIN_MEMBER_URN` that the app needs:

1. Create a LinkedIn developer application at https://www.linkedin.com/developers/apps .
2. In the *Products* tab, request access to **Sign In with LinkedIn** and **Share on LinkedIn** (this grants the `w_member_social` scope).
3. Under *Auth* → *OAuth 2.0 settings* add `http://localhost:8080` as a redirect URL (or any URL you control for local testing).
4. Click "Generate access token" (under *OAuth 2.0 testing tools*) selecting the `w_member_social` scope. Copy the generated **access token** – it remains valid for up to 60 days.
5. Grab your member URN. Hit the API once with the token:

   ```bash
   curl -H "Authorization: Bearer <ACCESS_TOKEN>" https://api.linkedin.com/v2/me | jq '.id'
   ```

   and format it as `urn:li:person:<id>` – that string is `LINKEDIN_MEMBER_URN`.
6. Export both variables in your deployment environment.

When the token expires the script will raise a `TokenExpiredError`. Simply repeat step 4 to generate a fresh token.