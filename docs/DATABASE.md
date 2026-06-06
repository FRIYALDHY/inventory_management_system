# Database Schema

PostgreSQL adalah source of truth. Semua primary key memakai UUID di level aplikasi.

## Auth

- `users`: email, full_name, hashed_password, role, is_active, last_login_at.
- `refresh_tokens`: user_id, token_hash, expires_at, revoked_at.

## Master Data

- `suppliers`: name, contact_name, phone, email, address, is_active.
- `item_categories`: name, description.
- `units`: name, symbol.
- `items`: sku, name, category_id, unit_id, minimum_stock, reorder_level, default_cost, is_active, notes.

## Purchase

- `purchases`: purchase_number, supplier_id, purchase_date, status, total_amount, notes, created_by_id.
- `purchase_items`: purchase_id, item_id, quantity, unit_price, subtotal, received_quantity.

## Inventory

- `inventory_receipts`: receipt_number, purchase_id, receipt_date, notes, created_by_id.
- `inventory_receipt_items`: receipt_id, item_id, purchase_item_id, quantity, unit_cost.
- `inventory_issues`: issue_number, issue_date, destination, notes, created_by_id.
- `inventory_issue_items`: issue_id, item_id, quantity, unit_cost.
- `stock_movements`: item_id, movement_type, quantity_change, unit_cost, reference_type, reference_id, note, performed_by_id.
- `inventory_balances`: item_id, current_quantity, average_cost, last_movement_at.
- `stock_alerts`: item_id, alert_type, threshold_quantity, current_quantity, is_active, resolved_at.

## Waste

- `waste_records`: waste_number, waste_date, notes, created_by_id.
- `waste_items`: waste_id, item_id, quantity, reason, unit_cost, estimated_cost.

## Operations

- `export_jobs`: report_type, file_format, status, file_path, error_message, requested_by_id.
- `backup_jobs`: status, file_path, file_size_bytes, error_message, requested_by_id.
- `audit_logs`: actor_id, action, entity_name, entity_id, metadata_json, created_at.

## Enums

- `user_role`: OWNER, PURCHASE, GUDANG.
- `purchase_status`: DRAFT, ORDERED, PARTIALLY_RECEIVED, RECEIVED, CANCELLED.
- `movement_type`: PURCHASE_IN, MANUAL_IN, OUT, WASTE, ADJUSTMENT.
- `alert_type`: LOW_STOCK, OUT_OF_STOCK.
- `job_status`: PENDING, PROCESSING, SUCCESS, FAILED.
- `backup_job_status`: PENDING, PROCESSING, SUCCESS, FAILED.

