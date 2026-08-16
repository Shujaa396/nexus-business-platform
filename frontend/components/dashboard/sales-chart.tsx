"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { getSalesAnalytics } from "../../lib/dashboard";
import { formatCurrency, formatNumber } from "./stat-card";
import { EmptyStateView, ErrorStateView, LoadingSpinner } from "../ui/state-views";

type PeriodType = "daily" | "weekly" | "monthly";
type MetricType = "revenue" | "orders" | "payments" | "all";

export function SalesChart() {
  const [period, setPeriod] = useState<PeriodType>("daily");
  const [chartType, setChartType] = useState<"area" | "bar">("area");
  const [activeMetric, setActiveMetric] = useState<MetricType>("revenue");

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["sales-analytics", period],
    queryFn: () => getSalesAnalytics(period),
  });

  const chartData = (data?.breakdown ?? []).map((item) => ({
    period: item.period,
    revenue: typeof item.revenue === "string" ? parseFloat(item.revenue) : item.revenue,
    orders: item.order_count,
    payments: typeof item.payment_total === "string" ? parseFloat(item.payment_total) : item.payment_total,
    invoices: typeof item.invoice_total === "string" ? parseFloat(item.invoice_total) : item.invoice_total,
  }));

  const formatYAxis = (val: number) => {
    if (activeMetric === "orders") {
      return val.toString();
    }
    if (val >= 1000000) return `Rs. ${(val / 1000000).toFixed(1)}M`;
    if (val >= 1000) return `Rs. ${(val / 1000).toFixed(0)}k`;
    return `Rs. ${val}`;
  };

  return (
    <article className="min-h-[380px] rounded-xl border border-border bg-white p-6 shadow-sm">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-base font-semibold text-slate-950">
              Sales Overview
            </h2>
            {data && (
              <span className="rounded-md bg-primary/10 px-2 py-0.5 text-xs font-semibold text-primary">
                {formatCurrency(data.total_revenue)}
              </span>
            )}
          </div>
          <p className="mt-1 text-xs text-slate-500">
            Revenue, orders, invoices, and payments performance
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Metric selector */}
          <div className="inline-flex rounded-lg border border-border bg-slate-50 p-1 text-xs font-medium">
            <button
              type="button"
              onClick={() => setActiveMetric("revenue")}
              className={`rounded-md px-2.5 py-1 transition ${
                activeMetric === "revenue"
                  ? "bg-white text-slate-900 shadow-sm"
                  : "text-slate-500 hover:text-slate-900"
              }`}
            >
              Revenue
            </button>
            <button
              type="button"
              onClick={() => setActiveMetric("orders")}
              className={`rounded-md px-2.5 py-1 transition ${
                activeMetric === "orders"
                  ? "bg-white text-slate-900 shadow-sm"
                  : "text-slate-500 hover:text-slate-900"
              }`}
            >
              Orders
            </button>
            <button
              type="button"
              onClick={() => setActiveMetric("payments")}
              className={`rounded-md px-2.5 py-1 transition ${
                activeMetric === "payments"
                  ? "bg-white text-slate-900 shadow-sm"
                  : "text-slate-500 hover:text-slate-900"
              }`}
            >
              Payments
            </button>
            <button
              type="button"
              onClick={() => setActiveMetric("all")}
              className={`rounded-md px-2.5 py-1 transition ${
                activeMetric === "all"
                  ? "bg-white text-slate-900 shadow-sm"
                  : "text-slate-500 hover:text-slate-900"
              }`}
            >
              Combined
            </button>
          </div>

          {/* Period selector */}
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value as PeriodType)}
            className="rounded-lg border border-border bg-white px-3 py-1.5 text-xs font-medium text-slate-700 outline-none transition hover:border-slate-300 focus:border-primary focus:ring-1 focus:ring-primary"
          >
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
          </select>
        </div>
      </div>

      <div className="mt-6">
        {isLoading ? (
          <div className="flex h-64 items-center justify-center">
            <LoadingSpinner message="Loading sales analytics..." />
          </div>
        ) : isError ? (
          <div className="flex h-64 items-center justify-center">
            <ErrorStateView
              message={
                error instanceof Error
                  ? error.message
                  : "Unable to load sales data."
              }
              onRetry={() => refetch()}
            />
          </div>
        ) : chartData.length === 0 ? (
          <div className="flex h-64 items-center justify-center">
            <EmptyStateView
              title="No sales data recorded"
              message="Sales will populate as orders and invoices are generated."
            />
          </div>
        ) : (
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              {chartType === "area" ? (
                <AreaChart
                  data={chartData}
                  margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
                >
                  <defs>
                    <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#0d9488" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#0d9488" stopOpacity={0.0} />
                    </linearGradient>
                    <linearGradient id="colorPayments" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#f97316" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#f97316" stopOpacity={0.0} />
                    </linearGradient>
                    <linearGradient id="colorInvoices" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>

                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                  <XAxis
                    dataKey="period"
                    tick={{ fontSize: 11, fill: "#64748b" }}
                    axisLine={{ stroke: "#cbd5e1" }}
                    tickLine={false}
                  />
                  <YAxis
                    tickFormatter={formatYAxis}
                    tick={{ fontSize: 11, fill: "#64748b" }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#ffffff",
                      borderRadius: "8px",
                      border: "1px solid #e2e8f0",
                      boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                      fontSize: "12px",
                    }}
                    formatter={(value: unknown, name: string) => {
                      if (name === "Orders") return [formatNumber(Number(value)), name];
                      return [formatCurrency(Number(value)), name];
                    }}
                  />
                  <Legend
                    wrapperStyle={{ fontSize: "12px", paddingTop: "12px" }}
                  />

                  {(activeMetric === "revenue" || activeMetric === "all") && (
                    <Area
                      type="monotone"
                      dataKey="revenue"
                      name="Revenue"
                      stroke="#0d9488"
                      strokeWidth={2}
                      fillOpacity={1}
                      fill="url(#colorRevenue)"
                    />
                  )}

                  {(activeMetric === "payments" || activeMetric === "all") && (
                    <Area
                      type="monotone"
                      dataKey="payments"
                      name="Payments"
                      stroke="#f97316"
                      strokeWidth={2}
                      fillOpacity={1}
                      fill="url(#colorPayments)"
                    />
                  )}

                  {activeMetric === "all" && (
                    <Area
                      type="monotone"
                      dataKey="invoices"
                      name="Invoices"
                      stroke="#6366f1"
                      strokeWidth={2}
                      fillOpacity={1}
                      fill="url(#colorInvoices)"
                    />
                  )}

                  {activeMetric === "orders" && (
                    <Area
                      type="monotone"
                      dataKey="orders"
                      name="Orders"
                      stroke="#0284c7"
                      strokeWidth={2}
                      fill="#0284c7"
                      fillOpacity={0.2}
                    />
                  )}
                </AreaChart>
              ) : (
                <BarChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                  <XAxis dataKey="period" tick={{ fontSize: 11, fill: "#64748b" }} />
                  <YAxis tickFormatter={formatYAxis} tick={{ fontSize: 11, fill: "#64748b" }} />
                  <Tooltip
                    formatter={(value: unknown, name: string) => {
                      if (name === "Orders") return [formatNumber(Number(value)), name];
                      return [formatCurrency(Number(value)), name];
                    }}
                  />
                  <Legend />
                  <Bar dataKey="revenue" name="Revenue" fill="#0d9488" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="payments" name="Payments" fill="#f97316" radius={[4, 4, 0, 0]} />
                </BarChart>
              )}
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </article>
  );
}
