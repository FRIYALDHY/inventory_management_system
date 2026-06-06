# API Endpoint Specification

Base URL: `/api/v1`

FastAPI juga menyediakan OpenAPI interaktif di `/api/v1/docs`.

## Auth

| Method | Path | Role | Description |
| --- | --- | --- | --- |
| POST | `/auth/login` | Public | Login dan terbitkan access/refresh token |
| POST | `/auth/refresh` | Public | Rotasi refresh token |
| POST | `/auth/logout` | Public | Revoke refresh token |
| GET | `/auth/me` | Authenticated | Profil user aktif |

## Users

| Method | Path | Role | Description |
| --- | --- | --- | --- |
| GET | `/users` | Owner | List user |
| POST | `/users` | Owner | Buat user Owner/Purchase/Gudang |
| PATCH | `/users/{user_id}` | Owner | Update user |

## Master Data

| Method | Path | Role | Description |
| --- | --- | --- | --- |
| GET | `/suppliers` | Owner, Purchase, Gudang | List supplier |
| POST | `/suppliers` | Owner, Purchase | Buat supplier |
| PATCH | `/suppliers/{supplier_id}` | Owner, Purchase | Update supplier |
| GET | `/categories` | Owner, Purchase, Gudang | List kategori |
| POST | `/categories` | Owner, Purchase | Buat kategori |
| PATCH | `/categories/{category_id}` | Owner, Purchase | Update kategori |
| GET | `/units` | Owner, Purchase, Gudang | List satuan |
| POST | `/units` | Owner, Purchase | Buat satuan |
| PATCH | `/units/{unit_id}` | Owner, Purchase | Update satuan |
| GET | `/items` | Owner, Purchase, Gudang | List barang dan stok |
| GET | `/items/{item_id}` | Owner, Purchase, Gudang | Detail barang |
| POST | `/items` | Owner, Purchase | Buat barang |
| PATCH | `/items/{item_id}` | Owner, Purchase | Update barang |

## Purchase

| Method | Path | Role | Description |
| --- | --- | --- | --- |
| GET | `/purchases` | Owner, Purchase, Gudang | List purchase |
| GET | `/purchases/{purchase_id}` | Owner, Purchase, Gudang | Detail purchase |
| POST | `/purchases` | Owner, Purchase | Buat purchase |
| PATCH | `/purchases/{purchase_id}` | Owner, Purchase | Update header/status purchase |
| POST | `/purchases/{purchase_id}/receive` | Owner, Purchase, Gudang | Terima purchase dan tambah stok |

## Inventory

| Method | Path | Role | Description |
| --- | --- | --- | --- |
| GET | `/inventory/balances` | Owner, Purchase, Gudang | Stok aktual |
| GET | `/inventory/movements` | Owner, Purchase, Gudang | Ledger stok |
| POST | `/inventory/receipts` | Owner, Gudang | Barang masuk manual |
| GET | `/inventory/receipts` | Owner, Purchase, Gudang | Histori barang masuk |
| POST | `/inventory/issues` | Owner, Gudang | Barang keluar |
| GET | `/inventory/issues` | Owner, Purchase, Gudang | Histori barang keluar |
| GET | `/inventory/alerts` | Owner, Purchase, Gudang | Stock alert |

## Waste

| Method | Path | Role | Description |
| --- | --- | --- | --- |
| POST | `/waste` | Owner, Gudang | Input waste dan kurangi stok |
| GET | `/waste` | Owner, Gudang | List waste |
| GET | `/waste/{waste_id}` | Owner, Gudang | Detail waste |

## Dashboard, Reports, Backup

| Method | Path | Role | Description |
| --- | --- | --- | --- |
| GET | `/dashboard` | Owner, Purchase, Gudang | Dashboard umum |
| GET | `/dashboard/owner` | Owner | Dashboard owner |
| GET | `/reports/summary` | Owner | Laporan berdasarkan date range |
| POST | `/reports/export` | Owner | Export PDF/XLSX |
| GET | `/reports/exports` | Owner | Histori export |
| GET | `/reports/exports/{export_id}/download` | Owner | Download export |
| POST | `/backups` | Owner | Backup database PostgreSQL |
| GET | `/backups` | Owner | Histori backup |
| GET | `/backups/{backup_id}/download` | Owner | Download backup |

