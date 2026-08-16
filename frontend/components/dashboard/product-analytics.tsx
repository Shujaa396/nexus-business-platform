"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getProductAnalytics } from "../../lib/dashboard";
import { formatCurrency, formatNumber } from "./stat-card";
import { EmptyStateView, ErrorStateView, LoadingSpinner } from "../ui/state-views";
import { ArrowUpRight, Boxes, Package, TrendingUp } from "lucide-react";

export function ProductAnalytics() {
  const [tab, setTab] = useState<"top_selling" | "highest_revenue">("top_selling");

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["product-analytics"],
    queryFn: () => getProductAnalytics(10),
  });

  const products = tab === "top_selling"
    ? (data?.top_selling_products ?? [])
    : (data?.highest_revenue_products ?? []);

  return (
    <article className="rounded-xl border border-border bg-white p-6 shadow-sm">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-base font-semibold text-slate-950">
              Product Performance
            </h2>
            {data && (
              <span className="inline-flex items-center gap-1 rounded-md bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-700">
                <Boxes className="h-3 w-3 text-primary" />
                Valuation: {formatCurrency(data.total_inventory_value)}
              </span>
            )}
          </div>
          <p className="mt-1 text-xs text-slate-500">
            Top selling products and highest revenue generators
          </p>
        </div>

        <div className="inline-flex rounded-lg border border-border bg-slate-50 p-1 text-xs font-medium">
          <button
            type="button"
            onClick={() => setTab("top_selling")}
            className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 transition ${
              tab === "top_selling"
                ? "bg-white text-slate-900 shadow-sm"
                : "text-slate-500 hover:text-slate-900"
            }`}
          >
            <TrendingUp className="h-3.5 w-3.5" />
            Top Selling
          </button>
          <button
            type="button"
            onClick={() => setTab("highest_revenue")}
            className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 transition ${
              tab === "highest_revenue"
                ? "bg-white text-slate-900 shadow-sm"
                : "text-slate-500 hover:text-slate-900"
            }`}
          >
            <ArrowUpRight className="h-3.5 w-3.5" />
            Highest Revenue
          </button>
        </div>
      </div>

      <div className="mt-5">
        {isLoading ? (
          <div className="flex h-56 items-center justify-center">
            <LoadingSpinner message="Loading product analytics..." />
          </div>
        ) : isError ? (
          <div className="flex h-56 items-center justify-center">
            <ErrorStateView
              message={
                error instanceof Error
                  ? error.message
                  : "Unable to load product analytics."
              }
              onRetry={() => refetch()}
            />
          </div>
        ) : products.length === 0 ? (
          <div className="flex h-56 items-center justify-center">
            <EmptyStateView
              title="No product sales data"
              message="Top products will appear once sales orders are recorded."
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-border text-xs text-slate-400">
                  <th className="pb-3 font-medium">#</th>
                  <th className="pb-3 font-medium">Product</th>
                  <th className="pb-3 font-medium">SKU</th>
                  <th className="pb-3 text-right font-medium">Units Sold</th>
                  <th className="pb-3 text-right font-medium">Total Revenue</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {products.map((item, idx) => (
                  <tr key={item.product_id} className="hover:bg-slate-50">
                    <td className="py-3 pr-2 text-xs font-semibold text-slate-400">
                      {idx + 1}
                    </td>
                    <td className="py-3 pr-4">
                      <div className="flex items-center gap-2.5">
                        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
                          <Package className="h-4 w-4" />
                        </div>
                        <span className="font-semibold text-slate-900">
                          {item.name}
                        </span>
                      </div>
                    </td>
                    <td className="py-3 px-2 text-xs text-slate-500 font-mono">
                      {item.sku}
                    </td>
                    <td className="py-3 px-2 text-right font-medium text-slate-700">
                      {formatNumber(Number(item.units_sold))}
                    </td>
                    <td className="py-3 pl-2 text-right font-semibold text-slate-950">
                      {formatCurrency(item.total_revenue)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </article>
  );
}
