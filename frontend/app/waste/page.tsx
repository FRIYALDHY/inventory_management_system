"use client";

import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import { Plus, RefreshCcw } from "lucide-react";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { EmptyState } from "@/components/data/empty-state";
import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { TBody, TD, TH, THead, TR, Table } from "@/components/ui/table";
import { useAuth } from "@/features/auth/auth-provider";
import { apiFetch } from "@/lib/api";
import type { Item, Page, WasteRecord } from "@/lib/types";
import { formatCurrency, formatNumber } from "@/lib/utils";

type WasteRow = {
  item_id: string;
  quantity: string;
  reason: string;
};

const selectClass =
  "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring";

export default function WastePage() {
  const { accessToken } = useAuth();
  const [items, setItems] = useState<Item[]>([]);
  const [waste, setWaste] = useState<WasteRecord[]>([]);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [header, setHeader] = useState({
    waste_number: "",
    waste_date: new Date().toISOString().slice(0, 10),
    notes: ""
  });
  const [rows, setRows] = useState<WasteRow[]>([{ item_id: "", quantity: "", reason: "" }]);

  const loadData = useCallback(async () => {
    if (!accessToken) return;
    setError("");
    try {
      const [itemRes, wasteRes] = await Promise.all([
        apiFetch<Page<Item>>("/items?page_size=100&active_only=true", { token: accessToken }),
        apiFetch<Page<WasteRecord>>("/waste?page_size=50", { token: accessToken })
      ]);
      setItems(itemRes.items);
      setWaste(wasteRes.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal memuat waste");
    }
  }, [accessToken]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const itemLabelById = useMemo(() => new Map(items.map((item) => [item.id, `${item.sku} - ${item.name}`])), [items]);

  async function createWaste(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!accessToken) return;
    setError("");
    setMessage("");
    try {
      await apiFetch("/waste", {
        method: "POST",
        token: accessToken,
        body: JSON.stringify({
          ...header,
          items: rows.map((row) => ({
            item_id: row.item_id,
            quantity: row.quantity,
            reason: row.reason
          }))
        })
      });
      setMessage("Waste berhasil dicatat");
      setRows([{ item_id: "", quantity: "", reason: "" }]);
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal mencatat waste");
    }
  }

  return (
    <ProtectedRoute roles={["OWNER", "GUDANG"]}>
      <AppShell title="Waste Management" description="Pencatatan waste terstruktur dan dampak biaya inventory.">
        {error ? <div className="mb-4 rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">{error}</div> : null}
        {message ? <div className="mb-4 rounded-md border border-primary/30 bg-primary/10 p-3 text-sm text-primary">{message}</div> : null}

        <div className="grid gap-4 xl:grid-cols-[420px_1fr]">
          <Card>
            <CardHeader>
              <CardTitle>Input Waste</CardTitle>
            </CardHeader>
            <CardContent>
              <form className="space-y-3" onSubmit={createWaste}>
                <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
                  <Input placeholder="Nomor waste" value={header.waste_number} onChange={(e) => setHeader({ ...header, waste_number: e.target.value })} required />
                  <Input type="date" value={header.waste_date} onChange={(e) => setHeader({ ...header, waste_date: e.target.value })} required />
                </div>
                {rows.map((row, index) => (
                  <div className="space-y-2 rounded-md border p-3" key={index}>
                    <select className={selectClass} value={row.item_id} onChange={(e) => setRows(rows.map((r, i) => i === index ? { ...r, item_id: e.target.value } : r))} required>
                      <option value="">Barang</option>
                      {items.map((item) => <option key={item.id} value={item.id}>{item.sku} - {item.name}</option>)}
                    </select>
                    <div className="grid gap-2 sm:grid-cols-[110px_1fr]">
                      <Input type="number" step="0.001" placeholder="Qty" value={row.quantity} onChange={(e) => setRows(rows.map((r, i) => i === index ? { ...r, quantity: e.target.value } : r))} required />
                      <Input placeholder="Reason" value={row.reason} onChange={(e) => setRows(rows.map((r, i) => i === index ? { ...r, reason: e.target.value } : r))} required />
                    </div>
                  </div>
                ))}
                <Button type="button" variant="outline" className="w-full" onClick={() => setRows([...rows, { item_id: "", quantity: "", reason: "" }])}>
                  <Plus className="h-4 w-4" />
                  Tambah Baris
                </Button>
                <Button className="w-full">Catat Waste</Button>
              </form>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Histori Waste</CardTitle>
              <Button variant="outline" onClick={loadData}>
                <RefreshCcw className="h-4 w-4" />
                Refresh
              </Button>
            </CardHeader>
            <CardContent>
              {waste.length > 0 ? (
                <Table>
                  <THead>
                    <TR>
                      <TH>Nomor</TH>
                      <TH>Tanggal</TH>
                      <TH>Barang</TH>
                      <TH>Qty</TH>
                      <TH>Reason</TH>
                      <TH>Estimasi</TH>
                    </TR>
                  </THead>
                  <TBody>
                    {waste.flatMap((record) =>
                      record.items.map((item) => (
                        <TR key={item.id}>
                          <TD>{record.waste_number}</TD>
                          <TD>{record.waste_date}</TD>
                          <TD>{itemLabelById.get(item.item_id) ?? item.item_id}</TD>
                          <TD>{formatNumber(item.quantity)}</TD>
                          <TD>{item.reason}</TD>
                          <TD>{formatCurrency(item.estimated_cost)}</TD>
                        </TR>
                      ))
                    )}
                  </TBody>
                </Table>
              ) : (
                <EmptyState />
              )}
            </CardContent>
          </Card>
        </div>
      </AppShell>
    </ProtectedRoute>
  );
}

