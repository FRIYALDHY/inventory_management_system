"use client";

import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import { Plus, RefreshCcw, Save } from "lucide-react";

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
import type { Item, Page, Purchase, Supplier } from "@/lib/types";
import { formatCurrency, formatNumber } from "@/lib/utils";

type PurchaseRow = {
  item_id: string;
  quantity: string;
  unit_price: string;
};

type ReceiveRow = {
  purchase_item_id: string;
  quantity: string;
};

const selectClass =
  "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring";

const statusVariant = {
  DRAFT: "outline",
  ORDERED: "secondary",
  PARTIALLY_RECEIVED: "default",
  RECEIVED: "default",
  CANCELLED: "destructive"
} as const;

export default function PurchasePage() {
  const { accessToken, hasRole } = useAuth();
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [items, setItems] = useState<Item[]>([]);
  const [purchases, setPurchases] = useState<Purchase[]>([]);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const canCreatePurchase = hasRole("OWNER", "PURCHASE");
  const canReceive = hasRole("OWNER", "PURCHASE", "GUDANG");

  const [supplierForm, setSupplierForm] = useState({
    name: "",
    contact_name: "",
    phone: "",
    email: "",
    address: ""
  });
  const [purchaseHeader, setPurchaseHeader] = useState({
    purchase_number: "",
    supplier_id: "",
    purchase_date: new Date().toISOString().slice(0, 10),
    notes: ""
  });
  const [purchaseRows, setPurchaseRows] = useState<PurchaseRow[]>([
    { item_id: "", quantity: "", unit_price: "0" }
  ]);
  const [selectedPurchaseId, setSelectedPurchaseId] = useState("");
  const [receiveHeader, setReceiveHeader] = useState({
    receipt_number: "",
    receipt_date: new Date().toISOString().slice(0, 10),
    notes: ""
  });
  const [receiveRows, setReceiveRows] = useState<ReceiveRow[]>([]);

  const loadData = useCallback(async () => {
    if (!accessToken) return;
    setError("");
    try {
      const [supplierRes, itemRes, purchaseRes] = await Promise.all([
        apiFetch<Page<Supplier>>("/suppliers?page_size=100&active_only=true", { token: accessToken }),
        apiFetch<Page<Item>>("/items?page_size=100&active_only=true", { token: accessToken }),
        apiFetch<Page<Purchase>>("/purchases?page_size=50", { token: accessToken })
      ]);
      setSuppliers(supplierRes.items);
      setItems(itemRes.items);
      setPurchases(purchaseRes.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal memuat purchase");
    }
  }, [accessToken]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const itemLabelById = useMemo(() => {
    return new Map(items.map((item) => [item.id, `${item.sku} - ${item.name}`]));
  }, [items]);

  const selectedPurchase = purchases.find((purchase) => purchase.id === selectedPurchaseId);

  useEffect(() => {
    if (!selectedPurchase) {
      setReceiveRows([]);
      return;
    }
    setReceiveRows(
      selectedPurchase.items
        .filter((item) => Number(item.quantity) > Number(item.received_quantity))
        .map((item) => ({ purchase_item_id: item.id, quantity: "" }))
    );
  }, [selectedPurchaseId]);

  async function createSupplier(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!accessToken) return;
    setError("");
    setMessage("");
    try {
      await apiFetch<Supplier>("/suppliers", {
        method: "POST",
        token: accessToken,
        body: JSON.stringify({
          ...supplierForm,
          email: supplierForm.email || null
        })
      });
      setMessage("Supplier berhasil dibuat");
      setSupplierForm({ name: "", contact_name: "", phone: "", email: "", address: "" });
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal menyimpan supplier");
    }
  }

  async function createPurchase(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!accessToken) return;
    setError("");
    setMessage("");
    try {
      await apiFetch<Purchase>("/purchases", {
        method: "POST",
        token: accessToken,
        body: JSON.stringify({
          ...purchaseHeader,
          supplier_id: purchaseHeader.supplier_id || null,
          items: purchaseRows.map((row) => ({
            item_id: row.item_id,
            quantity: row.quantity,
            unit_price: row.unit_price
          }))
        })
      });
      setMessage("Purchase berhasil dibuat");
      setPurchaseRows([{ item_id: "", quantity: "", unit_price: "0" }]);
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal membuat purchase");
    }
  }

  async function receivePurchase(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!accessToken || !selectedPurchaseId) return;
    setError("");
    setMessage("");
    try {
      await apiFetch(`/purchases/${selectedPurchaseId}/receive`, {
        method: "POST",
        token: accessToken,
        body: JSON.stringify({
          ...receiveHeader,
          items: receiveRows.filter((row) => Number(row.quantity) > 0)
        })
      });
      setMessage("Purchase berhasil diterima dan stok bertambah");
      setSelectedPurchaseId("");
      setReceiveRows([]);
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal menerima purchase");
    }
  }

  return (
    <ProtectedRoute>
      <AppShell title="Purchase" description="Supplier, purchase order, dan penerimaan barang.">
        {error ? <div className="mb-4 rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">{error}</div> : null}
        {message ? <div className="mb-4 rounded-md border border-primary/30 bg-primary/10 p-3 text-sm text-primary">{message}</div> : null}

        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Daftar Purchase</CardTitle>
            <Button variant="outline" onClick={loadData}>
              <RefreshCcw className="h-4 w-4" />
              Refresh
            </Button>
          </CardHeader>
          <CardContent>
            {purchases.length > 0 ? (
              <Table>
                <THead>
                  <TR>
                    <TH>Nomor</TH>
                    <TH>Tanggal</TH>
                    <TH>Supplier</TH>
                    <TH>Total</TH>
                    <TH>Status</TH>
                  </TR>
                </THead>
                <TBody>
                  {purchases.map((purchase) => (
                    <TR key={purchase.id}>
                      <TD>{purchase.purchase_number}</TD>
                      <TD>{purchase.purchase_date}</TD>
                      <TD>{purchase.supplier?.name ?? "-"}</TD>
                      <TD>{formatCurrency(purchase.total_amount)}</TD>
                      <TD><Badge variant={statusVariant[purchase.status]}>{purchase.status}</Badge></TD>
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
          {canCreatePurchase ? (
            <Card>
              <CardHeader>
                <CardTitle>Supplier</CardTitle>
              </CardHeader>
              <CardContent>
                <form className="space-y-3" onSubmit={createSupplier}>
                  <Input placeholder="Nama supplier" value={supplierForm.name} onChange={(e) => setSupplierForm({ ...supplierForm, name: e.target.value })} required />
                  <Input placeholder="Kontak" value={supplierForm.contact_name} onChange={(e) => setSupplierForm({ ...supplierForm, contact_name: e.target.value })} />
                  <Input placeholder="Telepon" value={supplierForm.phone} onChange={(e) => setSupplierForm({ ...supplierForm, phone: e.target.value })} />
                  <Input type="email" placeholder="Email" value={supplierForm.email} onChange={(e) => setSupplierForm({ ...supplierForm, email: e.target.value })} />
                  <Input placeholder="Alamat" value={supplierForm.address} onChange={(e) => setSupplierForm({ ...supplierForm, address: e.target.value })} />
                  <Button className="w-full">
                    <Save className="h-4 w-4" />
                    Simpan Supplier
                  </Button>
                </form>
              </CardContent>
            </Card>
          ) : null}

          {canCreatePurchase ? (
            <Card>
              <CardHeader>
                <CardTitle>Purchase Baru</CardTitle>
              </CardHeader>
              <CardContent>
                <form className="space-y-3" onSubmit={createPurchase}>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <Input placeholder="Nomor PO" value={purchaseHeader.purchase_number} onChange={(e) => setPurchaseHeader({ ...purchaseHeader, purchase_number: e.target.value })} required />
                    <Input type="date" value={purchaseHeader.purchase_date} onChange={(e) => setPurchaseHeader({ ...purchaseHeader, purchase_date: e.target.value })} required />
                  </div>
                  <div className="space-y-2">
                    <Label>Supplier</Label>
                    <select className={selectClass} value={purchaseHeader.supplier_id} onChange={(e) => setPurchaseHeader({ ...purchaseHeader, supplier_id: e.target.value })}>
                      <option value="">Tanpa supplier</option>
                      {suppliers.map((supplier) => <option key={supplier.id} value={supplier.id}>{supplier.name}</option>)}
                    </select>
                  </div>
                  {purchaseRows.map((row, index) => (
                    <div className="grid gap-2 sm:grid-cols-[1fr_90px_110px]" key={index}>
                      <select className={selectClass} value={row.item_id} onChange={(e) => setPurchaseRows(purchaseRows.map((r, i) => i === index ? { ...r, item_id: e.target.value } : r))} required>
                        <option value="">Barang</option>
                        {items.map((item) => <option key={item.id} value={item.id}>{item.sku} - {item.name}</option>)}
                      </select>
                      <Input type="number" step="0.001" placeholder="Qty" value={row.quantity} onChange={(e) => setPurchaseRows(purchaseRows.map((r, i) => i === index ? { ...r, quantity: e.target.value } : r))} required />
                      <Input type="number" step="0.01" placeholder="Harga" value={row.unit_price} onChange={(e) => setPurchaseRows(purchaseRows.map((r, i) => i === index ? { ...r, unit_price: e.target.value } : r))} required />
                    </div>
                  ))}
                  <Button type="button" variant="outline" className="w-full" onClick={() => setPurchaseRows([...purchaseRows, { item_id: "", quantity: "", unit_price: "0" }])}>
                    <Plus className="h-4 w-4" />
                    Tambah Item
                  </Button>
                  <Button className="w-full">Buat Purchase</Button>
                </form>
              </CardContent>
            </Card>
          ) : null}

          {canReceive ? (
            <Card>
              <CardHeader>
                <CardTitle>Terima Purchase</CardTitle>
              </CardHeader>
              <CardContent>
                <form className="space-y-3" onSubmit={receivePurchase}>
                  <select className={selectClass} value={selectedPurchaseId} onChange={(e) => setSelectedPurchaseId(e.target.value)} required>
                    <option value="">Pilih purchase</option>
                    {purchases
                      .filter((purchase) => !["RECEIVED", "CANCELLED"].includes(purchase.status))
                      .map((purchase) => <option key={purchase.id} value={purchase.id}>{purchase.purchase_number}</option>)}
                  </select>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <Input placeholder="Nomor receipt" value={receiveHeader.receipt_number} onChange={(e) => setReceiveHeader({ ...receiveHeader, receipt_number: e.target.value })} required />
                    <Input type="date" value={receiveHeader.receipt_date} onChange={(e) => setReceiveHeader({ ...receiveHeader, receipt_date: e.target.value })} required />
                  </div>
                  {receiveRows.map((row, index) => {
                    const purchaseItem = selectedPurchase?.items.find((item) => item.id === row.purchase_item_id);
                    return (
                      <div className="grid gap-2 sm:grid-cols-[1fr_120px]" key={row.purchase_item_id}>
                        <div className="rounded-md border bg-muted/40 px-3 py-2 text-sm">
                          {purchaseItem ? itemLabelById.get(purchaseItem.item_id) ?? purchaseItem.item_id : "-"}
                          {purchaseItem ? <span className="ml-2 text-muted-foreground">sisa {formatNumber(Number(purchaseItem.quantity) - Number(purchaseItem.received_quantity))}</span> : null}
                        </div>
                        <Input type="number" step="0.001" placeholder="Qty" value={row.quantity} onChange={(e) => setReceiveRows(receiveRows.map((r, i) => i === index ? { ...r, quantity: e.target.value } : r))} />
                      </div>
                    );
                  })}
                  <Button className="w-full">Terima Barang</Button>
                </form>
              </CardContent>
            </Card>
          ) : null}
        </div>
      </AppShell>
    </ProtectedRoute>
  );
}

