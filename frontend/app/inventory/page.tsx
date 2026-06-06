"use client";

import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import { Plus, RefreshCcw, Save, Search } from "lucide-react";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { EmptyState } from "@/components/data/empty-state";
import { AppShell } from "@/components/layout/app-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { TBody, TD, TH, THead, TR, Table } from "@/components/ui/table";
import { useAuth } from "@/features/auth/auth-provider";
import { apiFetch } from "@/lib/api";
import type { Category, InventoryBalance, Item, Page, Unit } from "@/lib/types";
import { formatCurrency, formatNumber } from "@/lib/utils";

type StockRow = {
  item_id: string;
  quantity: string;
  unit_cost?: string;
};

const selectClass =
  "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring";

export default function InventoryPage() {
  const { accessToken, hasRole } = useAuth();
  const [balances, setBalances] = useState<InventoryBalance[]>([]);
  const [items, setItems] = useState<Item[]>([]);
  const [units, setUnits] = useState<Unit[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [q, setQ] = useState("");
  const [lowStock, setLowStock] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const canManageItem = hasRole("OWNER", "PURCHASE");
  const canMoveStock = hasRole("OWNER", "GUDANG");

  const [itemForm, setItemForm] = useState({
    sku: "",
    name: "",
    category_id: "",
    unit_id: "",
    minimum_stock: "0",
    reorder_level: "0",
    default_cost: "0"
  });
  const [categoryForm, setCategoryForm] = useState({ name: "", description: "" });
  const [unitForm, setUnitForm] = useState({ name: "", symbol: "" });
  const [receiptRows, setReceiptRows] = useState<StockRow[]>([{ item_id: "", quantity: "", unit_cost: "0" }]);
  const [issueRows, setIssueRows] = useState<StockRow[]>([{ item_id: "", quantity: "" }]);
  const [receiptHeader, setReceiptHeader] = useState({
    receipt_number: "",
    receipt_date: new Date().toISOString().slice(0, 10),
    notes: ""
  });
  const [issueHeader, setIssueHeader] = useState({
    issue_number: "",
    issue_date: new Date().toISOString().slice(0, 10),
    destination: "",
    notes: ""
  });

  const loadData = useCallback(async () => {
    if (!accessToken) return;
    setError("");
    const query = new URLSearchParams({ page_size: "100" });
    if (q) query.set("q", q);
    if (lowStock) query.set("low_stock", "true");
    try {
      const [balanceRes, itemRes, unitRes, categoryRes] = await Promise.all([
        apiFetch<Page<InventoryBalance>>(`/inventory/balances?${query}`, { token: accessToken }),
        apiFetch<Page<Item>>("/items?page_size=100&active_only=true", { token: accessToken }),
        apiFetch<Unit[]>("/units", { token: accessToken }),
        apiFetch<Category[]>("/categories", { token: accessToken })
      ]);
      setBalances(balanceRes.items);
      setItems(itemRes.items);
      setUnits(unitRes);
      setCategories(categoryRes);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal memuat inventory");
    }
  }, [accessToken, lowStock, q]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const itemOptions = useMemo(
    () => items.map((item) => ({ value: item.id, label: `${item.sku} - ${item.name}` })),
    [items]
  );

  async function createItem(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!accessToken) return;
    setError("");
    setMessage("");
    try {
      await apiFetch<Item>("/items", {
        method: "POST",
        token: accessToken,
        body: JSON.stringify({
          ...itemForm,
          category_id: itemForm.category_id || null
        })
      });
      setMessage("Barang berhasil dibuat");
      setItemForm({ sku: "", name: "", category_id: "", unit_id: "", minimum_stock: "0", reorder_level: "0", default_cost: "0" });
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal menyimpan barang");
    }
  }

  async function createCategory(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!accessToken) return;
    setError("");
    setMessage("");
    try {
      await apiFetch("/categories", {
        method: "POST",
        token: accessToken,
        body: JSON.stringify(categoryForm)
      });
      setMessage("Kategori berhasil dibuat");
      setCategoryForm({ name: "", description: "" });
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal menyimpan kategori");
    }
  }

  async function createUnit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!accessToken) return;
    setError("");
    setMessage("");
    try {
      await apiFetch("/units", {
        method: "POST",
        token: accessToken,
        body: JSON.stringify(unitForm)
      });
      setMessage("Satuan berhasil dibuat");
      setUnitForm({ name: "", symbol: "" });
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal menyimpan satuan");
    }
  }

  async function createReceipt(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!accessToken) return;
    setError("");
    setMessage("");
    try {
      await apiFetch("/inventory/receipts", {
        method: "POST",
        token: accessToken,
        body: JSON.stringify({
          ...receiptHeader,
          items: receiptRows.map((row) => ({
            item_id: row.item_id,
            quantity: row.quantity,
            unit_cost: row.unit_cost || "0"
          }))
        })
      });
      setMessage("Barang masuk berhasil dicatat");
      setReceiptRows([{ item_id: "", quantity: "", unit_cost: "0" }]);
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal mencatat barang masuk");
    }
  }

  async function createIssue(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!accessToken) return;
    setError("");
    setMessage("");
    try {
      await apiFetch("/inventory/issues", {
        method: "POST",
        token: accessToken,
        body: JSON.stringify({
          ...issueHeader,
          items: issueRows.map((row) => ({ item_id: row.item_id, quantity: row.quantity }))
        })
      });
      setMessage("Barang keluar berhasil dicatat");
      setIssueRows([{ item_id: "", quantity: "" }]);
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal mencatat barang keluar");
    }
  }

  return (
    <ProtectedRoute>
      <AppShell title="Inventory" description="Master barang, stok aktual, barang masuk, dan barang keluar.">
        {error ? <div className="mb-4 rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">{error}</div> : null}
        {message ? <div className="mb-4 rounded-md border border-primary/30 bg-primary/10 p-3 text-sm text-primary">{message}</div> : null}

        <Card>
          <CardHeader className="gap-3">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <CardTitle>Stok Aktual</CardTitle>
              <div className="flex flex-col gap-2 sm:flex-row">
                <div className="relative">
                  <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input className="pl-9" value={q} onChange={(event) => setQ(event.target.value)} placeholder="Cari SKU/barang" />
                </div>
                <label className="flex h-10 items-center gap-2 rounded-md border px-3 text-sm">
                  <input type="checkbox" checked={lowStock} onChange={(event) => setLowStock(event.target.checked)} />
                  Low stock
                </label>
                <Button variant="outline" onClick={loadData}>
                  <RefreshCcw className="h-4 w-4" />
                  Refresh
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {balances.length > 0 ? (
              <Table>
                <THead>
                  <TR>
                    <TH>SKU</TH>
                    <TH>Barang</TH>
                    <TH>Stok</TH>
                    <TH>Min</TH>
                    <TH>Avg Cost</TH>
                    <TH>Nilai</TH>
                    <TH>Status</TH>
                  </TR>
                </THead>
                <TBody>
                  {balances.map((row) => (
                    <TR key={row.item_id}>
                      <TD>{row.sku}</TD>
                      <TD>{row.item_name}</TD>
                      <TD>{formatNumber(row.current_quantity)} {row.unit_symbol}</TD>
                      <TD>{formatNumber(row.minimum_stock)}</TD>
                      <TD>{formatCurrency(row.average_cost)}</TD>
                      <TD>{formatCurrency(row.inventory_value)}</TD>
                      <TD>
                        {row.is_low_stock ? <Badge variant="destructive">Low</Badge> : <Badge variant="secondary">OK</Badge>}
                      </TD>
                    </TR>
                  ))}
                </TBody>
              </Table>
            ) : (
              <EmptyState />
            )}
          </CardContent>
        </Card>

        <div className="mt-4 grid gap-4 xl:grid-cols-3">
          {canManageItem ? (
            <Card>
              <CardHeader>
                <CardTitle>Kategori & Satuan</CardTitle>
              </CardHeader>
              <CardContent className="space-y-5">
                <form className="space-y-3" onSubmit={createCategory}>
                  <Input placeholder="Nama kategori" value={categoryForm.name} onChange={(e) => setCategoryForm({ ...categoryForm, name: e.target.value })} required />
                  <Input placeholder="Deskripsi" value={categoryForm.description} onChange={(e) => setCategoryForm({ ...categoryForm, description: e.target.value })} />
                  <Button className="w-full" variant="outline">Simpan Kategori</Button>
                </form>
                <form className="space-y-3" onSubmit={createUnit}>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <Input placeholder="Nama satuan" value={unitForm.name} onChange={(e) => setUnitForm({ ...unitForm, name: e.target.value })} required />
                    <Input placeholder="Simbol" value={unitForm.symbol} onChange={(e) => setUnitForm({ ...unitForm, symbol: e.target.value })} required />
                  </div>
                  <Button className="w-full" variant="outline">Simpan Satuan</Button>
                </form>
              </CardContent>
            </Card>
          ) : null}

          {canManageItem ? (
            <Card>
              <CardHeader>
                <CardTitle>Master Barang</CardTitle>
              </CardHeader>
              <CardContent>
                <form className="space-y-3" onSubmit={createItem}>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <div className="space-y-2">
                      <Label>SKU</Label>
                      <Input value={itemForm.sku} onChange={(e) => setItemForm({ ...itemForm, sku: e.target.value })} required />
                    </div>
                    <div className="space-y-2">
                      <Label>Nama</Label>
                      <Input value={itemForm.name} onChange={(e) => setItemForm({ ...itemForm, name: e.target.value })} required />
                    </div>
                  </div>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <div className="space-y-2">
                      <Label>Satuan</Label>
                      <select className={selectClass} value={itemForm.unit_id} onChange={(e) => setItemForm({ ...itemForm, unit_id: e.target.value })} required>
                        <option value="">Pilih</option>
                        {units.map((unit) => <option key={unit.id} value={unit.id}>{unit.name} ({unit.symbol})</option>)}
                      </select>
                    </div>
                    <div className="space-y-2">
                      <Label>Kategori</Label>
                      <select className={selectClass} value={itemForm.category_id} onChange={(e) => setItemForm({ ...itemForm, category_id: e.target.value })}>
                        <option value="">Tanpa kategori</option>
                        {categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}
                      </select>
                    </div>
                  </div>
                  <div className="grid gap-3 sm:grid-cols-3">
                    <div className="space-y-2">
                      <Label>Min</Label>
                      <Input type="number" step="0.001" value={itemForm.minimum_stock} onChange={(e) => setItemForm({ ...itemForm, minimum_stock: e.target.value })} required />
                    </div>
                    <div className="space-y-2">
                      <Label>Reorder</Label>
                      <Input type="number" step="0.001" value={itemForm.reorder_level} onChange={(e) => setItemForm({ ...itemForm, reorder_level: e.target.value })} required />
                    </div>
                    <div className="space-y-2">
                      <Label>Default Cost</Label>
                      <Input type="number" step="0.01" value={itemForm.default_cost} onChange={(e) => setItemForm({ ...itemForm, default_cost: e.target.value })} required />
                    </div>
                  </div>
                  <Button className="w-full">
                    <Save className="h-4 w-4" />
                    Simpan Barang
                  </Button>
                </form>
              </CardContent>
            </Card>
          ) : null}

          {canMoveStock ? (
            <>
              <Card>
                <CardHeader>
                  <CardTitle>Barang Masuk</CardTitle>
                </CardHeader>
                <CardContent>
                  <form className="space-y-3" onSubmit={createReceipt}>
                    <div className="grid gap-3 sm:grid-cols-2">
                      <Input placeholder="Nomor receipt" value={receiptHeader.receipt_number} onChange={(e) => setReceiptHeader({ ...receiptHeader, receipt_number: e.target.value })} required />
                      <Input type="date" value={receiptHeader.receipt_date} onChange={(e) => setReceiptHeader({ ...receiptHeader, receipt_date: e.target.value })} required />
                    </div>
                    {receiptRows.map((row, index) => (
                      <div className="grid gap-2 sm:grid-cols-[1fr_90px_110px]" key={index}>
                        <select className={selectClass} value={row.item_id} onChange={(e) => setReceiptRows(receiptRows.map((r, i) => i === index ? { ...r, item_id: e.target.value } : r))} required>
                          <option value="">Barang</option>
                          {itemOptions.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
                        </select>
                        <Input type="number" step="0.001" placeholder="Qty" value={row.quantity} onChange={(e) => setReceiptRows(receiptRows.map((r, i) => i === index ? { ...r, quantity: e.target.value } : r))} required />
                        <Input type="number" step="0.01" placeholder="Cost" value={row.unit_cost} onChange={(e) => setReceiptRows(receiptRows.map((r, i) => i === index ? { ...r, unit_cost: e.target.value } : r))} required />
                      </div>
                    ))}
                    <Button type="button" variant="outline" className="w-full" onClick={() => setReceiptRows([...receiptRows, { item_id: "", quantity: "", unit_cost: "0" }])}>
                      <Plus className="h-4 w-4" />
                      Tambah Baris
                    </Button>
                    <Button className="w-full">Catat Masuk</Button>
                  </form>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Barang Keluar</CardTitle>
                </CardHeader>
                <CardContent>
                  <form className="space-y-3" onSubmit={createIssue}>
                    <div className="grid gap-3 sm:grid-cols-2">
                      <Input placeholder="Nomor keluar" value={issueHeader.issue_number} onChange={(e) => setIssueHeader({ ...issueHeader, issue_number: e.target.value })} required />
                      <Input type="date" value={issueHeader.issue_date} onChange={(e) => setIssueHeader({ ...issueHeader, issue_date: e.target.value })} required />
                    </div>
                    <Input placeholder="Tujuan" value={issueHeader.destination} onChange={(e) => setIssueHeader({ ...issueHeader, destination: e.target.value })} />
                    {issueRows.map((row, index) => (
                      <div className="grid gap-2 sm:grid-cols-[1fr_110px]" key={index}>
                        <select className={selectClass} value={row.item_id} onChange={(e) => setIssueRows(issueRows.map((r, i) => i === index ? { ...r, item_id: e.target.value } : r))} required>
                          <option value="">Barang</option>
                          {itemOptions.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
                        </select>
                        <Input type="number" step="0.001" placeholder="Qty" value={row.quantity} onChange={(e) => setIssueRows(issueRows.map((r, i) => i === index ? { ...r, quantity: e.target.value } : r))} required />
                      </div>
                    ))}
                    <Button type="button" variant="outline" className="w-full" onClick={() => setIssueRows([...issueRows, { item_id: "", quantity: "" }])}>
                      <Plus className="h-4 w-4" />
                      Tambah Baris
                    </Button>
                    <Button className="w-full">Catat Keluar</Button>
                  </form>
                </CardContent>
              </Card>
            </>
          ) : null}
        </div>
      </AppShell>
    </ProtectedRoute>
  );
}
