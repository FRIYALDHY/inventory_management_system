"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Download, FileSpreadsheet, FileText, RefreshCcw } from "lucide-react";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { EmptyState } from "@/components/data/empty-state";
import { StatCard } from "@/components/data/stat-card";
import { AppShell } from "@/components/layout/app-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { TBody, TD, TH, THead, TR, Table } from "@/components/ui/table";
import { useAuth } from "@/features/auth/auth-provider";
import { apiFetch, downloadUrl } from "@/lib/api";
import type { ExportJob, Page, ReportSummary } from "@/lib/types";
import { formatCurrency } from "@/lib/utils";

function monthStart() {
  const now = new Date();
  return new Date(now.getFullYear(), now.getMonth(), 1).toISOString().slice(0, 10);
}

export default function ReportsPage() {
  const { accessToken } = useAuth();
  const [startDate, setStartDate] = useState(monthStart());
  const [endDate, setEndDate] = useState(new Date().toISOString().slice(0, 10));
  const [summary, setSummary] = useState<ReportSummary | null>(null);
  const [exports, setExports] = useState<ExportJob[]>([]);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const loadExports = useCallback(async () => {
    if (!accessToken) return;
    const result = await apiFetch<Page<ExportJob>>("/reports/exports?page_size=20", { token: accessToken });
    setExports(result.items);
  }, [accessToken]);

  const loadSummary = useCallback(async () => {
    if (!accessToken) return;
    setError("");
    try {
      const params = new URLSearchParams({ start_date: startDate, end_date: endDate });
      const result = await apiFetch<ReportSummary>(`/reports/summary?${params}`, { token: accessToken });
      setSummary(result);
      await loadExports();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal memuat laporan");
    }
  }, [accessToken, endDate, loadExports, startDate]);

  useEffect(() => {
    loadSummary();
  }, [loadSummary]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await loadSummary();
  }

  async function exportReport(format: "pdf" | "xlsx") {
    if (!accessToken) return;
    setError("");
    setMessage("");
    try {
      await apiFetch<ExportJob>("/reports/export", {
        method: "POST",
        token: accessToken,
        body: JSON.stringify({ start_date: startDate, end_date: endDate, format })
      });
      setMessage(`Export ${format.toUpperCase()} berhasil dibuat`);
      await loadExports();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal export laporan");
    }
  }

  async function downloadExport(job: ExportJob) {
    if (!accessToken) return;
    const response = await fetch(downloadUrl(`/reports/exports/${job.id}/download`), {
      headers: { Authorization: `Bearer ${accessToken}` }
    });
    if (!response.ok) {
      setError("Gagal mengunduh export");
      return;
    }
    const blob = await response.blob();
    const objectUrl = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = objectUrl;
    anchor.download = `ata-pims-report-${job.id}.${job.file_format}`;
    anchor.click();
    URL.revokeObjectURL(objectUrl);
  }

  return (
    <ProtectedRoute roles={["OWNER"]}>
      <AppShell title="Laporan" description="Laporan pembelian, pengeluaran, waste, nilai inventory, dan export.">
        {error ? <div className="mb-4 rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">{error}</div> : null}
        {message ? <div className="mb-4 rounded-md border border-primary/30 bg-primary/10 p-3 text-sm text-primary">{message}</div> : null}

        <Card>
          <CardHeader>
            <CardTitle>Range Laporan</CardTitle>
          </CardHeader>
          <CardContent>
            <form className="flex flex-col gap-3 sm:flex-row sm:items-end" onSubmit={onSubmit}>
              <div className="space-y-2">
                <Label>Mulai</Label>
                <Input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} required />
              </div>
              <div className="space-y-2">
                <Label>Sampai</Label>
                <Input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} required />
              </div>
              <Button>
                <RefreshCcw className="h-4 w-4" />
                Tampilkan
              </Button>
              <Button type="button" variant="outline" onClick={() => exportReport("pdf")}>
                <FileText className="h-4 w-4" />
                PDF
              </Button>
              <Button type="button" variant="outline" onClick={() => exportReport("xlsx")}>
                <FileSpreadsheet className="h-4 w-4" />
                Excel
              </Button>
            </form>
          </CardContent>
        </Card>

        <div className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard title="Total Purchase" value={formatCurrency(summary?.purchase_total)} icon={FileSpreadsheet} />
          <StatCard title="Total Waste" value={formatCurrency(summary?.waste_total)} icon={FileText} tone="warning" />
          <StatCard title="Nilai Inventory" value={formatCurrency(summary?.inventory_value)} icon={Download} tone="info" />
          <StatCard title="Transaksi Waste" value={summary?.waste_count ?? 0} icon={RefreshCcw} />
        </div>

        <Card className="mt-4">
          <CardHeader>
            <CardTitle>Histori Export</CardTitle>
          </CardHeader>
          <CardContent>
            {exports.length > 0 ? (
              <Table>
                <THead>
                  <TR>
                    <TH>Jenis</TH>
                    <TH>Format</TH>
                    <TH>Status</TH>
                    <TH>File</TH>
                  </TR>
                </THead>
                <TBody>
                  {exports.map((job) => (
                    <TR key={job.id}>
                      <TD>{job.report_type}</TD>
                      <TD>{job.file_format.toUpperCase()}</TD>
                      <TD>
                        <Badge variant={job.status === "FAILED" ? "destructive" : job.status === "SUCCESS" ? "secondary" : "outline"}>
                          {job.status}
                        </Badge>
                      </TD>
                      <TD>
                        {job.status === "SUCCESS" ? (
                          <Button size="sm" variant="outline" onClick={() => downloadExport(job)}>
                            <Download className="h-4 w-4" />
                            Download
                          </Button>
                        ) : (
                          job.error_message ?? "-"
                        )}
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
      </AppShell>
    </ProtectedRoute>
  );
}

