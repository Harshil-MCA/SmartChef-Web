# SmartChef Web

SmartChef is a React web client backed by Django REST Framework. It provides ingredient detection, nutrition analysis, recipes, diet planning, shopping lists, profiles, authentication, and activity history.

## Stack and layout

- `frontend/` — React 19 + TypeScript + Vite single-page application.
- `backend/` — Django 5 + Django REST Framework API, JWT authentication, Firebase exchange, SQLite locally, and PostgreSQL support through `DJANGO_DATABASE_URL`.
- `backend/config/` — Django settings, URL routing, ASGI, and WSGI entry points.
- `backend/*/` — feature apps for accounts, profiles, history, shopping, recipes, nutrition, ingredients, diet planning, and AI services.
- `backend/datasets/` — local data assets; these are intentionally ignored by Git because the current assets are too large for a normal GitHub repository.

## Prerequisites

- Python 3.11+ (3.12 recommended)
- Node.js 20+
- npm
- Tesseract OCR if OCR features are used
- The local dataset/model assets required by the enabled ingredient and nutrition features

## Local setup (Windows PowerShell)

```powershell
Set-Location .\backend
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py runserver
```

In a second PowerShell window:

```powershell
Set-Location .\frontend
npm ci
Copy-Item .env.example .env
npm run dev
```

The frontend runs at `http://localhost:5173` and calls the API at the URL in `VITE_API_BASE_URL` (default: `http://127.0.0.1:8000/api`). Do not commit either `.env` file.

## Environment configuration

Use `backend/.env.example` and `frontend/.env.example` as the complete variable-name reference. Production must set at least:

- `DJANGO_SECRET_KEY` — a newly generated secret.
- `DJANGO_DEBUG=False`.
- `DJANGO_ALLOWED_HOSTS` — comma-separated backend hostnames.
- `DJANGO_CORS_ALLOWED_ORIGINS` and `DJANGO_CSRF_TRUSTED_ORIGINS` — full frontend origins, including `https://`.
- `DJANGO_DATABASE_URL` — PostgreSQL in production; SQLite is suitable only for local development.
- `VITE_API_BASE_URL` — the deployed API base URL ending in `/api`.
- Any required Gemini, USDA, data.gov.in, Firebase, Tesseract, model, and nutrition-data settings.

Never put secrets, service-account JSON, API keys, production database URLs, uploaded files, or a real `.env` file in Git.

## API routes

The API is rooted at `/api/`:

- `/api/auth/` — register, login, Firebase exchange, refresh, logout, current user, and password reset.
- `/api/profile/`, `/api/history/`, `/api/shopping-items/`, `/api/recipes/`, `/api/nutrition/`, `/api/ingredients/`, and `/api/diet-plans/` — feature endpoints.
- `/admin/` — Django administration.

## Checks and production commands

```powershell
Set-Location .\backend
python manage.py check
python manage.py check --deploy
python manage.py makemigrations --check --dry-run
python manage.py test
python manage.py collectstatic --noinput
gunicorn config.wsgi:application --bind 0.0.0.0:$env:PORT
```

Build the frontend with:

```powershell
Set-Location .\frontend
npm ci
npm run build
```

Deploy the `frontend/dist` output to a static host with SPA fallback to `index.html`. Run the Django migration and collectstatic commands as a release step, then start the backend with Gunicorn. Use managed PostgreSQL and persistent/object storage for production uploads; do not rely on an ephemeral SQLite file or local filesystem for user data.

## GitHub upload (PowerShell)

Run these from this directory. Review every result before committing:

```powershell
git status --short --branch
git remote -v
git add .
git status --short
git diff --cached --stat
git diff --cached -- . ':!backend/datasets'
git diff --cached --name-only | Select-String -Pattern '(^|/|\\)\.env($|\.)|\.sqlite3$|credentials|secret|token|key' -CaseSensitive:$false
```

If the last command prints a real secret or local database, stop and unstage it before continuing. Then commit:

```powershell
git commit -m "Prepare SmartChef web app for deployment"
```

Check the existing remote before adding one. Replace the placeholder only after confirming the URL:

```powershell
$remote = git remote get-url origin 2>$null
if ($LASTEXITCODE -ne 0) {
    git remote add origin https://github.com/YOUR_USERNAME/SmartChef-Web.git
} else {
    Write-Host "origin already configured as $remote; leaving it unchanged"
}
git remote -v
git branch -M main
git push -u origin main
```

Do not force-push or overwrite an existing remote without an explicit review.

## Hosting recommendation

Use a static frontend host for React and a managed application host for Django, backed by managed PostgreSQL. This split matches the existing architecture and keeps frontend builds independent from the API process. Configure the backend environment variables in the host dashboard, set the frontend `VITE_API_BASE_URL` at build time, run migrations before the new release receives traffic, and configure the frontend origin in both CORS and CSRF trusted origins.

GitHub stores the source; it does not run Django, provide PostgreSQL, or host uploaded media by itself. No external deployment or paid resource has been created by this preparation.
