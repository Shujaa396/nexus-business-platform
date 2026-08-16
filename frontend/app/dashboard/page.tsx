"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  Boxes,
  Calendar,
  CheckCircle,
  Clock,
  CreditCard,
  DollarSign,
  Package,
  RefreshCw,
  ShoppingCart,
  TrendingUp,
  Users,
} from "lucide-react";

import AppShell from "../../components/app-shell";
import { BranchAnalytics } from "../../components/dashboard/branch-analytics";
import { CustomerAnalytics } from "../../components/dashboard/customer-analytics";
import { LowStockTable } from "../../components/dashboard/low-stock-table";
import { ProductAnalytics } from "../../components/dashboard/product-analytics";
import { SalesChart } from "../../components/dashboard/sales-chart";
import {
  formatCurrency,
  formatNumber,
  StatCard,
} from "../../components/dashboard/stat-card";
import { ErrorStateView } from "../../components/ui/state-views";
import { useAuth } from "../../hooks/use-auth";
import { getDashboardSummary, getProductAnalytics } from "../../lib/dashboard";

export default function DashboardPage() {
  const { organization } = useAuth();

  // 1. Dashboard Summary
  const {
    data: summary,
    isLoading: isSummaryLoading,
    isError: isSummaryError,
    error: summaryError,
    refetch: refetchSummary,
  } = useQuery({
    queryKey: ["dashboard-summary"],
    queryFn: getDashboardSummary,
  });

  // 2. Product Analytics (for Low Stock section & quick stats)
  const {
    data: productData,
    isLoading: isProductLoading,
    isError: isProductError,
    error: productError,
    refetch: refetchProducts,
  } = useQuery({
    queryKey: ["product-analytics"],
    queryFn: () => getProductAnalytics(10),
  });

  return (
    <AppShell>
      <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8 space-y-6">
        {/* Header section */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <p className="text-xs font-semibold uppercase tracking-wider text-primary">
                Executive Overview
              </p>
              {organization?.name && (
                <span className="text-xs font-medium text-slate-400">• {organization.name}</span>
              )}
            </div>

            <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-950 sm:text-3xl">
              Dashboard
            </h1>

            <p className="mt-1 text-xs text-slate-500">
              Live multi-branch operational performance, revenue metrics, and inventory intelligence.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => {
                refetchSummary();
                refetchProducts();
              }}
              className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-white px-3 py-2 text-xs font-medium text-slate-700 shadow-sm transition hover:bg-slate-50 hover:text-slate-900"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Refresh Data
            </button>
          </div>
        </div>

        {/* Global Summary Error State */}
        {isSummaryError && (
          <div className="rounded-xl border border-red-200 bg-red-50/50 p-6">
            <ErrorStateView
              message={
                summaryError instanceof Error
                  ? summaryError.message
                  : "Unable to load summary metrics from the NEXUS server."
              }
              onRetry={() => refetchSummary()}
            />
          </div>
        )}

        {/* Primary Summary Metric Cards */}
        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            label="Total Revenue"
            value={
              isSummaryLoading
                ? "..."
                : isSummaryError
                ? "—"
                : formatCurrency(summary?.total_revenue)
            }
            description="Lifetime collected & invoiced revenue"
            icon={DollarSign}
            isLoading={isSummaryLoading}
          />

          <StatCard
            label="Orders"
            value={
              isSummaryLoading
                ? "..."
                : isSummaryError
                ? "—"
                : formatNumber(summary?.total_orders)
            }
            description="Total customer orders recorded"
            icon={ShoppingCart}
            isLoading={isSummaryLoading}
          />

          <StatCard
            label="Customers"
            value={
              isSummaryLoading
                ? "..."
                : isSummaryError
                ? "—"
                : formatNumber(summary?.total_customers)
            }
            description="Active customer accounts"
            icon={Users}
            isLoading={isSummaryLoading}
          />

          <StatCard
            label="Products"
            value={
              isSummaryLoading
                ? "..."
                : isSummaryError
                ? "—"
                : formatNumber(summary?.total_products)
            }
            description="Catalog product definitions"
            icon={Package}
            isLoading={isSummaryLoading}
          />
        </section>

        {/* Secondary Real-time Business Metrics */}
        <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
          <div className="rounded-xl border border-border bg-white p-4 shadow-sm">
            <div className="flex items-center gap-2 text-slate-500">
              <TrendingUp className="h-4 w-4 text-emerald-600" />
              <p className="text-xs font-medium truncate">Today&apos;s Sales</p>
            </div>
            <p className="mt-2 text-lg font-bold text-slate-950">
              {isSummaryLoading
                ? "..."
                : isSummaryError
                ? "—"
                : formatCurrency(summary?.today_sales)}
            </p>
            <p className="mt-0.5 text-[11px] text-slate-400">
              {isSummaryLoading
                ? "..."
                : `${formatNumber(summary?.today_orders)} orders today`}
            </p>
          </div>

          <div className="rounded-xl border border-border bg-white p-4 shadow-sm">
            <div className="flex items-center gap-2 text-slate-500">
              <Calendar className="h-4 w-4 text-primary" />
              <p className="text-xs font-medium truncate">Month Revenue</p>
            </div>
            <p className="mt-2 text-lg font-bold text-slate-950">
              {isSummaryLoading
                ? "..."
                : isSummaryError
                ? "—"
                : formatCurrency(summary?.current_month_revenue)}
            </p>
            <p className="mt-0.5 text-[11px] text-slate-400">Current calendar month</p>
          </div>

          <div className="rounded-xl border border-border bg-white p-4 shadow-sm">
            <div className="flex items-center gap-2 text-slate-500">
              <CreditCard className="h-4 w-4 text-teal-600" />
              <p className="text-xs font-medium truncate">Total Payments</p>
            </div>
            <p className="mt-2 text-lg font-bold text-slate-950">
              {isSummaryLoading
                ? "..."
                : isSummaryError
                ? "—"
                : formatCurrency(summary?.total_payments)}
            </p>
            <p className="mt-0.5 text-[11px] text-slate-400">Cleared payments</p>
          </div>

          <div className="rounded-xl border border-border bg-white p-4 shadow-sm">
            <div className="flex items-center gap-2 text-slate-500">
              <Clock className="h-4 w-4 text-amber-600" />
              <p className="text-xs font-medium truncate">Pending Invoices</p>
            </div>
            <p className="mt-2 text-lg font-bold text-slate-950">
              {isSummaryLoading
                ? "..."
                : isSummaryError
                ? "—"
                : formatCurrency(summary?.pending_payments)}
            </p>
            <p className="mt-0.5 text-[11px] text-slate-400">Outstanding balance</p>
          </div>

          <div className="rounded-xl border border-border bg-white p-4 shadow-sm">
            <div className="flex items-center gap-2 text-slate-500">
              <AlertTriangle className="h-4 w-4 text-rose-600" />
              <p className="text-xs font-medium truncate">Low Stock Count</p>
            </div>
            <p className="mt-2 text-lg font-bold text-rose-600">
              {isSummaryLoading
                ? "..."
                : isSummaryError
                ? "—"
                : formatNumber(summary?.low_stock_product_count)}
            </p>
            <p className="mt-0.5 text-[11px] text-slate-400">Needs restock</p>
          </div>

          <div className="rounded-xl border border-border bg-white p-4 shadow-sm">
            <div className="flex items-center gap-2 text-slate-500">
              <Boxes className="h-4 w-4 text-indigo-600" />
              <p className="text-xs font-medium truncate">Inventory Value</p>
            </div>
            <p className="mt-2 text-lg font-bold text-slate-950 truncate">
              {isProductLoading
                ? "..."
                : isProductError
                ? "—"
                : formatCurrency(productData?.total_inventory_value)}
            </p>
            <p className="mt-0.5 text-[11px] text-slate-400">Current stock valuation</p>
          </div>
        </section>

        {/* Middle Section: Sales Overview Chart (2 cols) & Low Stock Alerts (1 col) */}
        <section className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <SalesChart />
          </div>

          <div>
            <LowStockTable
              items={productData?.low_stock_products}
              isLoading={isProductLoading}
              isError={isProductError}
              errorMessage={
                productError instanceof Error ? productError.message : undefined
              }
              onRetry={() => refetchProducts()}
            />
          </div>
        </section>

        {/* Lower Section: Product Performance & Customer Insights */}
        <section className="grid gap-6 lg:grid-cols-2">
          <ProductAnalytics />
          <CustomerAnalytics />
        </section>

        {/* Bottom Section: Branch Performance Table */}
        <section>
          <BranchAnalytics />
        </section>
      </div>
    </AppShell>
  );
}