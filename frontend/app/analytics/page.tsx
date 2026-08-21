"use client";

import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  BarChart3,
  Bot,
  Download,
  Package,
  RefreshCw,
  Send,
  TrendingUp,
  Users,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import AppShell from "../../components/app-shell";
import { formatCurrency, formatNumber, StatCard } from "../../components/dashboard/stat-card";
import { EmptyStateView, ErrorStateView, LoadingSpinner } from "../../components/ui/state-views";
import { askAnalytics, getAnalyticsDashboard } from "../../lib/analytics";
import { exportToCSV } from "../../lib/export";
import type { AnalyticsFilters, AnalyticsPeriod } from "../../types/analytics";

function numberValue(value: string | number | undefined): number {
  return typeof value === "number" ? value : Number(value || 0);
}

function dateInput(daysAgo: number): string {
  const date = new Date();
  date.setDate(date.getDate() - daysAgo);
  return date.toISOString().slice(0, 10);
}

function toUtcStart(value: string): string {
  return value ? `${value}T00:00:00Z` : "";
}

function toUtcEnd(value: string): string {
  return value ? `${value}T23:59:59Z` : "";
}

export default function AnalyticsPage() {
  const [dateFrom, setDateFrom] = useState(dateInput(30));
  const [dateTo, setDateTo] = useState(dateInput(0));
  const [period, setPeriod] = useState<AnalyticsPeriod>("daily");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);

  const filters: AnalyticsFilters = {
    date_from: toUtcStart(dateFrom),
    date_to: toUtcEnd(dateTo),
    limit: 10,
    period,
  };

  const dashboardQuery = useQuery({
    queryKey: ["analytics-dashboard", dateFrom, dateTo, period],
    queryFn: () => getAnalyticsDashboard(filters),
  });

  const askMutation = useMutation({
    mutationFn: askAnalytics,
    onSuccess: (result) => {
      setAnswer(result.message);
    },
    onError: (error: Error) => {
      setAnswer(error.message || "Unable to answer that analytics question.");
    },
  });

  const data = dashboardQuery.data;
  const trend = data?.trend.data.breakdown.map((item) => ({
    period: item.period,
    sales: numberValue(item.sales),
    orders: item.order_count,
  })) ?? [];

  const handleExportProducts = () => {
    if (!data?.products.data.products.length) return;
    exportToCSV(
      "analytics_top_products",
      data.products.data.products.map((product) => ({
        Product: product.name,
        SKU: product.sku,
        Quantity: product.quantity,
        Revenue: product.revenue,
      })),
    );
  };

  return (
    <AppShell>
      <div className="mx-auto w-full max-w-7xl space-y-6 px-4 py-6 sm:px-6 lg:px-8">
        <header className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-primary">Business Intelligence</p>
            <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-950 sm:text-3xl">Analytics</h1>
            <p className="mt-1 text-xs text-slate-500">Controlled insights from your organization&apos;s approved business data.</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <label className="text-xs font-semibold text-slate-500" htmlFor="analytics-from">From</label>
            <input id="analytics-from" type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} className="rounded-lg border border-border bg-white px-3 py-2 text-xs text-slate-700" />
            <label className="text-xs font-semibold text-slate-500" htmlFor="analytics-to">To</label>
            <input id="analytics-to" type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)} className="rounded-lg border border-border bg-white px-3 py-2 text-xs text-slate-700" />
            <select value={period} onChange={(event) => setPeriod(event.target.value as AnalyticsPeriod)} className="rounded-lg border border-border bg-white px-3 py-2 text-xs text-slate-700">
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
            </select>
            <button type="button" onClick={() => dashboardQuery.refetch()} className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-white px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50">
              <RefreshCw className="h-3.5 w-3.5" /> Refresh
            </button>
          </div>
        </header>

        {dashboardQuery.isLoading && <div className="rounded-xl border border-border bg-white py-16"><LoadingSpinner message="Loading controlled analytics..." /></div>}
        {dashboardQuery.isError && <div className="rounded-xl border border-red-200 bg-red-50/50 p-8"><ErrorStateView message={dashboardQuery.error instanceof Error ? dashboardQuery.error.message : "Unable to load analytics."} onRetry={() => dashboardQuery.refetch()} /></div>}

        {data && !dashboardQuery.isLoading && !dashboardQuery.isError && (
          <>
            <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <StatCard label="Sales" value={formatCurrency(data.summary.data.total_sales)} description="Confirmed and completed orders" icon={TrendingUp} />
              <StatCard label="Orders" value={formatNumber(data.summary.data.order_count)} description="Orders in selected range" icon={BarChart3} />
              <StatCard label="Average Order" value={formatCurrency(data.summary.data.average_order_value)} description="Sales per completed order" icon={Users} />
              <StatCard label="Inventory Value" value={formatCurrency(data.inventory.data.inventory_value)} description="Current cost valuation" icon={Package} />
            </section>

            <section className="grid gap-6 lg:grid-cols-3">
              <article className="min-h-[360px] rounded-xl border border-border bg-white p-5 shadow-sm lg:col-span-2">
                <div className="flex items-center justify-between">
                  <div><h2 className="text-base font-semibold text-slate-950">Sales Trend</h2><p className="mt-1 text-xs text-slate-500">Revenue and order volume for the selected range.</p></div>
                  <TrendingUp className="h-5 w-5 text-primary" />
                </div>
                {trend.length === 0 ? <EmptyStateView title="No sales in this range" message="Confirmed orders will appear here when recorded." /> : <div className="mt-6 h-64"><ResponsiveContainer width="100%" height="100%"><BarChart data={trend}><CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" /><XAxis dataKey="period" tick={{ fontSize: 10 }} /><YAxis tick={{ fontSize: 10 }} /><Tooltip formatter={(value: unknown, name: string) => [name === "orders" ? formatNumber(Number(value)) : formatCurrency(Number(value)), name]} /><Bar dataKey="sales" name="Sales" fill="#0d9488" radius={[3, 3, 0, 0]} /><Bar dataKey="orders" name="Orders" fill="#f97316" radius={[3, 3, 0, 0]} /></BarChart></ResponsiveContainer></div>}
              </article>

              <article className="rounded-xl border border-slate-800 bg-slate-900 p-5 text-white shadow-sm">
                <div className="flex items-center gap-2"><Bot className="h-5 w-5 text-teal-300" /><h2 className="text-base font-semibold">Ask Analytics</h2></div>
                <p className="mt-2 text-xs leading-relaxed text-slate-300">Ask a supported business question. NEXUS only uses approved analytics capabilities.</p>
                <form className="mt-5 space-y-3" onSubmit={(event) => { event.preventDefault(); if (question.trim()) askMutation.mutate(question.trim()); }}>
                  <textarea value={question} onChange={(event) => setQuestion(event.target.value)} rows={4} maxLength={500} placeholder="How much did we sell this month?" className="w-full resize-none rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-xs text-white outline-none placeholder:text-slate-500 focus:border-teal-400" />
                  <button type="submit" disabled={!question.trim() || askMutation.isPending} className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-teal-400 px-3 py-2 text-xs font-bold text-slate-950 hover:bg-teal-300 disabled:cursor-not-allowed disabled:opacity-50"><Send className="h-3.5 w-3.5" /> {askMutation.isPending ? "Analyzing..." : "Ask"}</button>
                </form>
                {answer && <div className="mt-4 rounded-lg border border-slate-700 bg-slate-800 p-3 text-xs leading-relaxed text-slate-200">{answer}</div>}
              </article>
            </section>

            <section className="grid gap-6 lg:grid-cols-2">
              <article className="rounded-xl border border-border bg-white p-5 shadow-sm"><div className="flex items-center justify-between"><div><h2 className="text-base font-semibold text-slate-950">Top Products</h2><p className="mt-1 text-xs text-slate-500">Ranked by revenue.</p></div><button type="button" onClick={handleExportProducts} className="inline-flex items-center gap-1.5 rounded-lg border border-border px-2.5 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-50"><Download className="h-3.5 w-3.5" /> CSV</button></div><AnalyticsTable headers={["Product", "Qty", "Revenue"]} rows={data.products.data.products.map((item) => [item.name, formatNumber(numberValue(item.quantity)), formatCurrency(item.revenue)])} /></article>
              <article className="rounded-xl border border-border bg-white p-5 shadow-sm"><h2 className="text-base font-semibold text-slate-950">Top Customers</h2><p className="mt-1 text-xs text-slate-500">Highest revenue contribution.</p><AnalyticsTable headers={["Customer", "Orders", "Revenue"]} rows={data.customers.data.customers.map((item) => [item.name, formatNumber(item.order_count), formatCurrency(item.revenue)])} /></article>
            </section>

            <section className="grid gap-6 lg:grid-cols-3">
              <article className="rounded-xl border border-border bg-white p-5 shadow-sm"><h2 className="text-base font-semibold text-slate-950">Branch Performance</h2><AnalyticsTable headers={["Branch", "Orders", "Sales"]} rows={data.branches.data.branches.map((item) => [item.name, formatNumber(item.order_count), formatCurrency(item.sales)])} /></article>
              <article className="rounded-xl border border-amber-200 bg-amber-50/40 p-5 shadow-sm"><div className="flex items-center gap-2"><AlertTriangle className="h-4 w-4 text-amber-600" /><h2 className="text-base font-semibold text-slate-950">Inventory Alerts</h2></div><p className="mt-1 text-xs text-slate-500">{data.inventory.data.out_of_stock.length} out of stock, {data.inventory.data.low_stock.length} low stock.</p><AnalyticsTable headers={["Product", "Branch", "Qty"]} rows={data.inventory.data.low_stock.map((item) => [item.name, item.branch_name, formatNumber(numberValue(item.quantity))])} /></article>
              <article className="rounded-xl border border-border bg-white p-5 shadow-sm"><h2 className="text-base font-semibold text-slate-950">Payments & Invoices</h2><div className="mt-4 space-y-3 text-xs"><MetricLine label="Payments" value={formatCurrency(data.payments.data.total)} /><MetricLine label="Invoices" value={formatNumber(data.invoices.data.invoice_count)} /><MetricLine label="Invoice total" value={formatCurrency(data.invoices.data.total)} /><MetricLine label="Overdue" value={formatNumber(data.invoices.data.overdue_count)} /></div></article>
            </section>

            <section className="rounded-xl border border-border bg-white p-5 shadow-sm"><h2 className="text-base font-semibold text-slate-950">Supplier Coverage</h2><p className="mt-1 text-xs text-slate-500">Products connected to Phase 8 supplier records.</p><AnalyticsTable headers={["Supplier", "Products", "Inventory value"]} rows={data.suppliers.data.suppliers.map((item) => [item.supplier_name, formatNumber(item.product_count), formatCurrency(item.inventory_value)])} /></section>
          </>
        )}
      </div>
    </AppShell>
  );
}

function MetricLine({ label, value }: { label: string; value: string }) {
  return <div className="flex items-center justify-between border-b border-border pb-2"><span className="text-slate-500">{label}</span><strong className="text-slate-900">{value}</strong></div>;
}

function AnalyticsTable({ headers, rows }: { headers: string[]; rows: string[][] }) {
  if (rows.length === 0) return <EmptyStateView title="No data" message="There is no matching activity in this date range." />;
  return <div className="mt-4 overflow-x-auto"><table className="w-full text-left text-xs"><thead><tr className="border-b border-border text-[10px] uppercase tracking-wider text-slate-400">{headers.map((header) => <th key={header} className="px-2 py-2 font-semibold">{header}</th>)}</tr></thead><tbody className="divide-y divide-border">{rows.map((row, index) => <tr key={`${row[0]}-${index}`} className="text-slate-700">{row.map((value, cellIndex) => <td key={`${cellIndex}-${value}`} className="max-w-[180px] truncate px-2 py-2.5">{value}</td>)}</tr>)}</tbody></table></div>;
}
