# Keelnote

Keelnote is a changelog and release manager for a maintainer's own software. You keep one log per product, collect notes while work is in progress, and cut a semantic version when a release is ready.

It is a single-maintainer tool. It stores your products, versions, and changelog notes. It does not keep a customer list, and it does not handle billing, health, or finance records.

## Stack

- Backend: Django 5, Django REST Framework, SimpleJWT, SQLite
- Frontend: React 18, TypeScript, Vite, react-router-dom, TanStack Query, axios, zustand, react-hook-form, zod, date-fns, lucide-react

## Run it locally

From the `backend` directory:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python manage.py migrate
.\.venv\Scripts\python manage.py runserver
```

From the `frontend` directory, in a second terminal:

```powershell
npm install
npm run dev
```

Open http://127.0.0.1:5173 and register a maintainer account. The API listens on http://127.0.0.1:8000.

Optional: `.\.venv\Scripts\python manage.py createsuperuser`, then visit http://127.0.0.1:8000/admin/.

Add a note without opening the app:

```powershell
.\.venv\Scripts\python manage.py addnote --username keeper --product harbor --kind fixed --text "Repair the tag writer"
```

Pass `--release 0.1.0` to attach the note to a version that already exists. Leave `--release` off and the note stays in the unreleased bucket.

For anything beyond this machine, set `DJANGO_SECRET_KEY` and `DJANGO_DEBUG=0`.

## How a release works

1. Create a product.
2. Add notes to the unreleased bucket. Each note is added, changed, fixed, or removed.
3. Cut a patch, minor, or major version, or step a pre-release channel (`alpha`, `beta`, then `rc`). Keelnote moves the unreleased notes into that version. You can still attach an explicit pre-release label such as `rc.1` on a major, minor, or patch cut. A channel bump sets its own numbered label.
4. Work through the checklist: tests, notes, and tag.
5. Publish the version. The markdown changelog uses a Keep a Changelog layout, with your notes and Keelnote's own section text.
6. If a published version should not be used, yank it. The version and its notes stay in the log, marked yanked, with the reason you give.
7. Compare two versions to see which notes are only on one side and which they share. A note can be flagged as a breaking change. Keelnote suggests the next stable version from the unreleased kinds, lints notes for a missing kind or an empty summary, and can export every version as one markdown file. Note templates fill in a starting sentence.

Cutting a patch from a pre-release promotes it to the stable version of that same core number. For example, `1.2.0-rc.1` becomes `1.2.0`.

## Tests and production build

Backend:

```powershell
cd backend
.\.venv\Scripts\python manage.py test
```

Frontend:

```powershell
cd frontend
npx vite build
```

## License

MIT License. Copyright (c) 2026 Madsvs123.
