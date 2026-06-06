export type UserRole = "OWNER" | "PURCHASE" | "GUDANG";

export type Page<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};

export type User = {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  last_login_at?: string | null;
};

export type TokenResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_at: string;
};

export type Supplier = {
  id: string;
  name: string;
  contact_name?: string | null;
  phone?: string | null;
  email?: string | null;
  address?: string | null;
  is_active: boolean;
};

export type Category = {
  id: string;
  name: string;
  description?: string | null;
};

export type Unit = {
  id: string;
  name: string;
  symbol: string;
};

export type Item = {
  id: string;
  sku: string;
  name: string;
  category_id?: string | null;
  unit_id: string;
  minimum_stock: string;
  reorder_level: string;
  default_cost: string;
  is_active: boolean;
  unit?: Unit;
  category?: Category | null;
  balance?: {
    current_quantity: string;
    average_cost: string;
    last_movement_at?: string | null;
  } | null;
};

export type InventoryBalance = {
  item_id: string;
  sku: string;
  item_name: string;
  unit_symbol: string;
  current_quantity: string;
  minimum_stock: string;
  reorder_level: string;
  average_cost: string;
  inventory_value: string;
  last_movement_at?: string | null;
  is_low_stock: boolean;
};

export type PurchaseStatus =
  | "DRAFT"
  | "ORDERED"
  | "PARTIALLY_RECEIVED"
  | "RECEIVED"
  | "CANCELLED";

export type Purchase = {
  id: string;
  purchase_number: string;
  supplier_id?: string | null;
  purchase_date: string;
  status: PurchaseStatus;
  total_amount: string;
  notes?: string | null;
  supplier?: Supplier | null;
  items: Array<{
    id: string;
    item_id: string;
    quantity: string;
    unit_price: string;
    subtotal: string;
    received_quantity: string;
  }>;
};

export type WasteRecord = {
  id: string;
  waste_number: string;
  waste_date: string;
  notes?: string | null;
  items: Array<{
    id: string;
    item_id: string;
    quantity: string;
    reason: string;
    unit_cost: string;
    estimated_cost: string;
  }>;
};

export type Dashboard = {
  total_sku: number;
  inventory_value: string;
  monthly_purchase_expense: string;
  yearly_purchase_expense: string;
  monthly_waste_value: string;
  low_stock_count: number;
  active_alerts?: number;
  low_stock_items: Array<{
    item_id: string;
    sku: string;
    name: string;
    current_quantity: string;
    minimum_stock: string;
    unit_symbol: string;
  }>;
};

export type ReportSummary = {
  start_date: string;
  end_date: string;
  purchase_total: string;
  waste_total: string;
  inventory_value: string;
  purchase_count: number;
  receipt_count: number;
  issue_count: number;
  waste_count: number;
};

export type ExportJob = {
  id: string;
  report_type: string;
  file_format: string;
  status: "PENDING" | "PROCESSING" | "SUCCESS" | "FAILED";
  file_path?: string | null;
  error_message?: string | null;
};

