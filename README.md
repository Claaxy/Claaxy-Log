# Claaxy Log

AI-powered voice logging for contractors — record job notes, extract income & expenses from speech, and view project profit.

## Stack

- Django 5+ / SQLite
- Google OAuth (django-allauth)
- OpenAI Whisper + GPT
- Bootstrap 5

## Setup

1. **Clone and enter the project**

```bash
cd "Claaxy Log"
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
```

2. **Environment variables**

```bash
copy .env.example .env         # Windows
# cp .env.example .env
```

Edit `.env` and set:

- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` — [Google Cloud Console](https://console.cloud.google.com/) OAuth 2.0 Web client
- `OPENAI_API_KEY` — OpenAI API key

**Redirect URI for local dev:**

```
http://127.0.0.1:8000/accounts/google/login/callback/
```

3. **Database**

```bash
python manage.py migrate
python manage.py createsuperuser   # optional, for /admin/
```

4. **Run**

```bash
python manage.py runserver
```

Open http://127.0.0.1:8000/

## Usage

1. Sign in with Google
2. Create a project
3. Open the project → **Start Recording**
4. Say something like: *这单卖了8000，人工5000，材料2000，吃饭100，加油50*
5. Wait for background AI processing (page auto-refreshes)
6. View **Income / Expenses / Profit** and project summary

## Project structure

```
manage.py
claaxy_log/          # settings, urls
apps/core/           # home, dashboard
apps/projects/       # models, views, OpenAI tasks
templates/
static/
media/               # voice uploads (gitignored)
```

See [DEVELOPMENT.md](DEVELOPMENT.md) for full specification.

## Production (Docker)

### 1. Push code to Git

From your dev machine:

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin <your-repo-url>
git push -u origin main
```

Do **not** commit `.env`, `db.sqlite3`, `media/`, or `venv/`.

### 2. Deploy on the server

```bash
git clone <your-repo-url> claaxy-log
cd claaxy-log
cp .env.example .env
# Edit .env: SECRET_KEY, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS, SITE_DOMAIN, Google OAuth, OpenAI
docker compose up -d --build
```

App listens on port `8000` by default (`HTTP_PORT` in `.env` can change the host mapping).

### 3. Google OAuth (production)

In [Google Cloud Console](https://console.cloud.google.com/), add this **Authorized redirect URI**:

```
https://your-domain.com/accounts/google/login/callback/
```

Replace `your-domain.com` with your real domain.

### 4. Reverse proxy (recommended)

Put Nginx or Caddy in front of the container for HTTPS. Example Nginx upstream:

```nginx
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

Keep `SECURE_SSL_REDIRECT=False` when TLS terminates at the proxy.

### 5. Useful commands

```bash
docker compose logs -f web          # view logs
docker compose restart web          # restart after .env changes
docker compose exec web python manage.py createsuperuser   # optional Django admin
docker compose exec web python manage.py shell             # Django shell
```

Data persists in Docker volumes `claaxy_data` (SQLite) and `claaxy_media` (voice uploads).
