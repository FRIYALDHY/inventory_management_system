"use client";

import { useEffect, useState } from "react";
import { Boxes, CircleDollarSign, PackageSearch, ShoppingCart, TrendingUp } from "lucide-react";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { EmptyState } from "@/components/data/empty-state";
import { StatCard } from "@/components/data/stat-card";
import { AppShell } from "@/components/layout/app-shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TBody, TD, TH, THead, TR, Table } from "@/components/ui/table";
import { useAuth } from "@/features/auth/auth-provider";
import { apiFetch } from "@/lib/api";
import type { Dashboard } from "@/lib/types";
import { formatCurrency, formatNumber } from "@/lib/utils";

export default function OwnerDashboardPage() {
  const { accessToken } = useAuth();
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!accessToken) return;
    apiFetch<Dashboard>("/dashboard/owner", { token: accessToken })
      .then(setData)
      .catch((err) => setError(err.message));
  }, [accessToken]);

  return (
    <ProtectedRoute roles={["OWNER"]}>
      <AppShell title="Dashboard Owner" description="KPI inventory dan biaya operasional inventory.">
        {error ? <div className="mb-4 rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">{error}</div> : null}
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
          <StatCard title="Total SKU" value={data?.total_sku ?? 0} icon={Boxes} />
          <StatCard title="Nilai Inventory" value={formatCurrency(data?.inventory_value)} icon={CircleDollarSign} tone="info" />
          <StatCard title="Pengeluaran Bulanan" value={formatCurrency(data?.monthly_purchase_expense)} icon={ShoppingCart} />
          <StatCard title="Pengeluaran Tahunan" value={formatCurrency(data?.yearly_purchase_expense)} icon={TrendingUp} />
          <StatCard title="Waste Bulanan" value={formatCurrency(data?.monthly_waste_value)} icon={PackageSearch} tone="warning" />
        </div>
        <Card className="mt-4">
          <CardHeader>
            <CardTitle>Prioritas Restock</CardTitle>
          </CardHeader>
          <CardContent>
            {data && data.low_stock_items.length > 0 ? (
              <Table>
                <THead>
                  <TR>
                    <TH>SKU</TH>
                    <TH>Nama Barang</TH>
                    <TH>Stok Saat Ini</TH>
                    <TH>Minimum</TH>
                  </TR>
                </THead>
                <TBody>
                  {data.low_stock_items.map((item) => (
                    <TR key={item.item_id}>
                      <TD>{item.sku}</TD>
                      <TD>{item.name}</TD>
                      <TD>{formatNumber(item.current_quantity)} {item.unit_symbol}</TD>
                      <TD>{formatNumber(item.minimum_stock)} {item.unit_symbol}</TD>
                    </TR>
                  ))}
                </TBody>
              </Table>
            ) : (
              <EmptyState title="Belum ada barang yang perlu direstock." />
            )}
          </CardContent>
        </Card>
      </AppShell>
    </ProtectedRoute>
  );
}

