# ATA Cafe & Billiard PIMS

Purchase & Inventory Management System berbasis PRD v1.0 untuk ATA Cafe & Billiard.

## Stack

- Backend: Python, FastAPI, SQLAlchemy, Alembic, PostgreSQL
- Frontend: Next.js, TypeScript, TailwindCSS, Shadcn-style UI
- Auth: JWT access token, refresh token rotation, Role Based Access Control
- Roles: Owner, Purchase, Gudang

## Modul MVP

- Login dan RBAC
- Dashboard umum dan dashboard owner
- Master barang, kategori, satuan
- Supplier management
- Purchase management
- Inventory masuk, keluar, movement ledger, stock alert
- Waste management
- Laporan summary, export PDF, export Excel
- Backup database PostgreSQL

## Setup Lokal

1. Copy environment file.

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

2. Jalankan PostgreSQL.

```bash
docker compose up -d postgres
```

3. Install backend dan jalankan migration.

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e .
alembic upgrade head
```

4. Buat user Owner pertama.

```bash
python -m app.scripts.create_user --email owner@ata.local --full-name "Owner ATA" --password "ChangeMe123!" --role OWNER
```

5. Jalankan backend.

```bash
uvicorn app.main:app --reload
```

6. Jalankan frontend.

```bash
cd frontend
npm install
npm run dev
```

Frontend tersedia di `http://localhost:3000`, backend docs di `http://localhost:8000/api/v1/docs`.

## Docker Compose

Setelah `backend/.env` tersedia:

```bash
docker compose up --build
```

Jalankan migration dari container backend:

```bash
docker compose exec backend alembic upgrade head
```

## Dokumentasi

- Architecture dan database design: `docs/ARCHITECTURE.md`
- Database schema: `docs/DATABASE.md`
- API endpoint specification: `docs/API.md`
