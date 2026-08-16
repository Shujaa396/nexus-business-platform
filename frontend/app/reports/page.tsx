"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Banknote,
  Building2,
  Download,
  Package,
  Printer,
  RefreshCw,
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
import { formatCurrency, formatNumber } from "../../components/dashboard/stat-card";
import { exportToCSV } from "../../lib/export";
import {
  getBranchAnalytics,
  getCustomerAnalytics,
  getDashboardSummary,
  getProductAnalytics,
  getSalesAnalytics,
} from "../../lib/dashboard";

type ReportTab = "financial" | "sales" | "products" | "customers" | "branches";

export default function ReportsPage() {
  const [activeTab, setActiveTab] = useState<ReportTab>("financial");
  const [salesInterval, setSalesInterval] = useState<
    "daily" | "weekly" | "monthly"
  >("daily");

  // Queries
  const {
    data: summary,
    refetch: refetchSummary,
  } = useQuery({
    queryKey: ["dashboard-summary"],
    queryFn: () => getDashboardSummary(),
  });

  const {
    data: salesData,
    refetch: refetchSales,
  } = useQuery({
    queryKey: ["sales-analytics", salesInterval],
    queryFn: () => getSalesAnalytics(salesInterval),
  });

  const {
    data: productData,
    refetch: refetchProducts,
  } = useQuery({
    queryKey: ["product-analytics"],
    queryFn: () => getProductAnalytics(),
  });

  const {
    data: customerData,
    refetch: refetchCustomers,
  } = useQuery({
    queryKey: ["customer-analytics"],
    queryFn: () => getCustomerAnalytics(),
  });

  const {
    data: branchData,
    refetch: refetchBranches,
  } = useQuery({
    queryKey: ["branch-analytics"],
    queryFn: () => getBranchAnalytics(),
  });

  const handleRefreshAll = () => {
    refetchSummary();
    refetchSales();
    refetchProducts();
    refetchCustomers();
    refetchBranches();
  };

  const handleExportReportCSV = () => {
    if (activeTab === "products" && productData?.top_selling_products) {
      exportToCSV(
        "product_performance_report",
        productData.top_selling_products.map((p) => ({
          SKU: p.sku,
          ProductName: p.name,
          UnitsSold: p.units_sold,
          RevenueGenerated: p.total_revenue,
        })),
      );
    } else if (activeTab === "customers" && customerData?.top_customers) {
      exportToCSV(
        "customer_acquisition_report",
        customerData.top_customers.map((c) => ({
          CustomerName: c.name,
          Email: c.email || "—",
          TotalOrders: c.order_count,
          TotalSpent: c.total_spent,
        })),
      );
    } else if (activeTab === "branches" && branchData?.branches) {
      exportToCSV(
        "branch_performance_report",
        branchData.branches.map((b) => ({
          BranchCode: b.code,
          BranchName: b.name,
          TotalOrders: b.order_count,
          TotalRevenue: b.revenue,
          InventoryItemsCount: b.inventory_items_count,
          StockValuation: b.inventory_value,
        })),
      );
    } else {
      // Financial summary export
      exportToCSV("financial_audit_summary", [
        {
          Metric: "Total Gross Revenue",
          Value: summary?.total_revenue || 0,
        },
        {
          Metric: "Total Orders Count",
          Value: summary?.total_orders || 0,
        },
        {
          Metric: "Total Products in Catalog",
          Value: summary?.total_products || 0,
        },
        {
          Metric: "Total Customers Registered",
          Value: summary?.total_customers || 0,
        },
        {
          Metric: "Total Invoices Issued",
          Value: summary?.total_invoices || 0,
        },
        {
          Metric: "Total Payments Collected",
          Value: summary?.total_payments || 0,
        },
        {
          Metric: "Pending Receivables",
          Value: summary?.pending_payments || 0,
        },
        {
          Metric: "Low Stock Alert Count",
          Value: summary?.low_stock_product_count || 0,
        },
        {
          Metric: "Month-to-Date Revenue",
          Value: summary?.current_month_revenue || 0,
        },
      ]);
    }
  };

  const tabs: Array<{ id: ReportTab; label: string; icon: React.ElementType }> = [
    { id: "financial", label: "Financial Audit", icon: Banknote },
    { id: "sales", label: "Sales & Volume", icon: TrendingUp },
    { id: "products", label: "Product Performance", icon: Package },
    { id: "customers", label: "Customer Acquisition", icon: Users },
    { id: "branches", label: "Branch Operations", icon: Building2 },
  ];

  return (
    <AppShell>
      <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8 space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-primary">
              Business Intelligence & Analytics
            </p>
            <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-950 sm:text-3xl">
              Reports & Audits
            </h1>
            <p className="mt-1 text-xs text-slate-500">
              Deep-dive metrics across revenue streams, product turns, customer lifetime value, and branch performance.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleRefreshAll}
              className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-white px-3 py-2 text-xs font-medium text-slate-700 shadow-sm transition hover:bg-slate-50"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Refresh All
            </button>
            <button
              type="button"
              onClick={handleExportReportCSV}
              className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-white px-3 py-2 text-xs font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50"
            >
              <Download className="h-3.5 w-3.5" />
              Export CSV
            </button>
            <button
              type="button"
              onClick={() => window.print()}
              className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50"
            >
              <Printer className="h-3.5 w-3.5" />
              Print Report
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex flex-wrap gap-1 border-b border-border pb-1">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 rounded-lg px-3.5 py-2 text-xs font-semibold transition ${
                  isActive
                    ? "bg-primary text-white shadow-sm"
                    : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                }`}
              >
                <Icon className="h-4 w-4" />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* TAB 1: FINANCIAL AUDIT */}
        {activeTab === "financial" && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div className="rounded-xl border border-border bg-white p-4 shadow-sm">
                <p className="text-xs text-slate-500 font-medium">
                  Total Gross Revenue
                </p>
                <p className="mt-1 text-2xl font-bold font-mono text-slate-950">
                  {formatCurrency(summary?.total_revenue || 0)}
                </p>
                <p className="mt-1 text-[11px] text-slate-400">
                  Across all confirmed orders
                </p>
              </div>

              <div className="rounded-xl border border-border bg-white p-4 shadow-sm">
                <p className="text-xs text-slate-500 font-medium">
                  Collected Payments
                </p>
                <p className="mt-1 text-2xl font-bold font-mono text-emerald-700">
                  {formatCurrency(summary?.total_payments || 0)}
                </p>
                <p className="mt-1 text-[11px] text-emerald-600">
                  Settled cash and card inflow
                </p>
              </div>

              <div className="rounded-xl border border-border bg-white p-4 shadow-sm">
                <p className="text-xs text-slate-500 font-medium">
                  Outstanding Receivables
                </p>
                <p className="mt-1 text-2xl font-bold font-mono text-amber-700">
                  {formatCurrency(summary?.pending_payments || 0)}
                </p>
                <p className="mt-1 text-[11px] text-amber-600">
                  Pending customer balance
                </p>
              </div>

              <div className="rounded-xl border border-border bg-white p-4 shadow-sm">
                <p className="text-xs text-slate-500 font-medium">
                  Current Month Revenue
                </p>
                <p className="mt-1 text-2xl font-bold font-mono text-teal-700">
                  {formatCurrency(summary?.current_month_revenue || 0)}
                </p>
                <p className="mt-1 text-[11px] text-teal-600">
                  Month-to-date sales
                </p>
              </div>
            </div>

            {/* Financial Breakdown Table */}
            <div className="rounded-xl border border-border bg-white shadow-sm overflow-hidden">
              <div className="border-b border-border bg-slate-50 px-6 py-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                  Executive Balance Summary
                </h3>
              </div>
              <div className="p-6">
                <table className="w-full text-left text-xs">
                  <tbody className="divide-y divide-slate-100 font-mono">
                    <tr>
                      <td className="py-3 font-sans font-semibold text-slate-800">
                        Total Invoiced Transactions
                      </td>
                      <td className="py-3 text-right font-bold text-slate-950">
                        {formatNumber(summary?.total_invoices || 0)}
                      </td>
                    </tr>
                    <tr>
                      <td className="py-3 font-sans font-semibold text-slate-800">
                        Total Order Volume
                      </td>
                      <td className="py-3 text-right font-bold text-slate-950">
                        {formatNumber(summary?.total_orders || 0)}
                      </td>
                    </tr>
                    <tr>
                      <td className="py-3 font-sans font-semibold text-slate-800">
                        Catalog Asset Valuation
                      </td>
                      <td className="py-3 text-right font-bold text-teal-700">
                        {formatCurrency(productData?.total_inventory_value || 0)}
                      </td>
                    </tr>
                    <tr>
                      <td className="py-3 font-sans font-semibold text-slate-800">
                        Active Branch Locations
                      </td>
                      <td className="py-3 text-right font-bold text-slate-950">
                        {branchData?.branches?.length || 0}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: SALES & VOLUME */}
        {activeTab === "sales" && (
          <div className="space-y-6">
            <div className="flex items-center justify-between rounded-xl border border-border bg-white p-4 shadow-sm">
              <span className="text-xs font-semibold text-slate-700">
                Reporting Interval:
              </span>
              <div className="flex items-center gap-1.5 rounded-lg bg-slate-100 p-1">
                {(["daily", "weekly", "monthly"] as const).map((interval) => (
                  <button
                    key={interval}
                    type="button"
                    onClick={() => setSalesInterval(interval)}
                    className={`rounded-md px-3 py-1 text-xs font-semibold capitalize transition ${
                      salesInterval === interval
                        ? "bg-white text-slate-900 shadow-sm"
                        : "text-slate-500 hover:text-slate-900"
                    }`}
                  >
                    {interval}
                  </button>
                ))}
              </div>
            </div>

            {/* Sales Chart */}
            <div className="rounded-xl border border-border bg-white p-6 shadow-sm">
              <h3 className="mb-4 text-xs font-bold uppercase tracking-wider text-slate-700">
                Revenue Inflow Over Time ({salesInterval})
              </h3>
              <div className="h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={salesData?.breakdown || []}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis dataKey="period" tick={{ fontSize: 11, fill: "#64748b" }} />
                    <YAxis
                      tickFormatter={(v) => `Rs. ${(v / 1000).toFixed(0)}k`}
                      tick={{ fontSize: 11, fill: "#64748b" }}
                    />
                    <Tooltip
                      formatter={(v: unknown) => [
                        formatCurrency(Number(v)),
                        "Revenue",
                      ]}
                    />
                    <Bar dataKey="revenue" fill="#0d9488" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: PRODUCT PERFORMANCE */}
        {activeTab === "products" && (
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <div className="rounded-xl border border-border bg-white shadow-sm overflow-hidden">
              <div className="border-b border-border bg-slate-50 px-6 py-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                  Top Volume Movers
                </h3>
              </div>
              <div className="p-4">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="text-slate-400 border-b border-slate-100">
                      <th className="py-2">Product</th>
                      <th className="py-2 text-right">Units Sold</th>
                      <th className="py-2 text-right">Revenue</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 font-mono">
                    {productData?.top_selling_products?.map((p) => (
                      <tr key={p.product_id}>
                        <td className="py-2.5 font-sans font-semibold text-slate-900">
                          {p.name}
                        </td>
                        <td className="py-2.5 text-right font-bold text-slate-800">
                          {formatNumber(Number(p.units_sold))}
                        </td>
                        <td className="py-2.5 text-right text-emerald-700">
                          {formatCurrency(p.total_revenue)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="rounded-xl border border-border bg-white shadow-sm overflow-hidden">
              <div className="border-b border-border bg-slate-50 px-6 py-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                  Highest Grossing Products
                </h3>
              </div>
              <div className="p-4">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="text-slate-400 border-b border-slate-100">
                      <th className="py-2">Product</th>
                      <th className="py-2 text-right">Units Sold</th>
                      <th className="py-2 text-right">Total Revenue</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 font-mono">
                    {productData?.highest_revenue_products?.map((p) => (
                      <tr key={p.product_id}>
                        <td className="py-2.5 font-sans font-semibold text-slate-900">
                          {p.name}
                        </td>
                        <td className="py-2.5 text-right text-slate-600">
                          {formatNumber(Number(p.units_sold))}
                        </td>
                        <td className="py-2.5 text-right font-bold text-teal-700">
                          {formatCurrency(p.total_revenue)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* TAB 4: CUSTOMER ACQUISITION */}
        {activeTab === "customers" && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="rounded-xl border border-border bg-white p-4 shadow-sm">
                <p className="text-xs text-slate-500 font-medium">
                  Total Registered Clients
                </p>
                <p className="mt-1 text-2xl font-bold font-mono text-slate-950">
                  {formatNumber(customerData?.total_customers || 0)}
                </p>
              </div>

              <div className="rounded-xl border border-border bg-white p-4 shadow-sm">
                <p className="text-xs text-slate-500 font-medium">
                  New Clients Acquired (30 Days)
                </p>
                <p className="mt-1 text-2xl font-bold font-mono text-teal-700">
                  {formatNumber(customerData?.new_customers_in_period || 0)}
                </p>
              </div>
            </div>

            <div className="rounded-xl border border-border bg-white shadow-sm overflow-hidden">
              <div className="border-b border-border bg-slate-50 px-6 py-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                  Top Spenders (Client Lifetime Value)
                </h3>
              </div>
              <div className="p-4">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="text-slate-400 border-b border-slate-100">
                      <th className="py-2 pl-2">Customer</th>
                      <th className="py-2">Email</th>
                      <th className="py-2 text-right">Orders Placed</th>
                      <th className="py-2 pr-2 text-right">Total Spent</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {customerData?.top_customers?.map((cust) => (
                      <tr key={cust.customer_id} className="hover:bg-slate-50">
                        <td className="py-2.5 pl-2 font-semibold text-slate-900">
                          {cust.name}
                        </td>
                        <td className="py-2.5 text-slate-500">
                          {cust.email || "—"}
                        </td>
                        <td className="py-2.5 text-right font-mono font-semibold text-slate-800">
                          {formatNumber(cust.order_count)}
                        </td>
                        <td className="py-2.5 pr-2 text-right font-mono font-bold text-teal-700">
                          {formatCurrency(cust.total_spent)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* TAB 5: BRANCH OPERATIONS */}
        {activeTab === "branches" && (
          <div className="rounded-xl border border-border bg-white shadow-sm overflow-hidden">
            <div className="border-b border-border bg-slate-50 px-6 py-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                Multi-Branch Performance Matrix
              </h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-border bg-slate-50 text-slate-500">
                    <th className="py-3.5 pl-6 pr-3 font-semibold">Branch Name</th>
                    <th className="py-3.5 px-3 font-semibold">Code</th>
                    <th className="py-3.5 px-3 text-right font-semibold">Total Orders</th>
                    <th className="py-3.5 px-3 text-right font-semibold">Gross Revenue</th>
                    <th className="py-3.5 px-3 text-right font-semibold">Inventory Items</th>
                    <th className="py-3.5 pl-3 pr-6 text-right font-semibold">Stock Valuation</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-mono">
                  {branchData?.branches?.map((b) => (
                    <tr key={b.branch_id} className="hover:bg-slate-50">
                      <td className="py-3.5 pl-6 pr-3 font-sans font-semibold text-slate-900">
                        {b.name}
                      </td>
                      <td className="py-3.5 px-3 text-slate-600">
                        {b.code}
                      </td>
                      <td className="py-3.5 px-3 text-right font-bold text-slate-900">
                        {formatNumber(b.order_count)}
                      </td>
                      <td className="py-3.5 px-3 text-right font-bold text-teal-700">
                        {formatCurrency(b.revenue)}
                      </td>
                      <td className="py-3.5 px-3 text-right text-slate-600">
                        {formatNumber(b.inventory_items_count)}
                      </td>
                      <td className="py-3.5 pl-3 pr-6 text-right font-bold text-slate-950">
                        {formatCurrency(b.inventory_value)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
