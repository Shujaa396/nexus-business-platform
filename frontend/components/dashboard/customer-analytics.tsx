"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getCustomerAnalytics } from "../../lib/dashboard";
import { formatCurrency, formatNumber } from "./stat-card";
import { EmptyStateView, ErrorStateView, LoadingSpinner } from "../ui/state-views";
import { UserCheck, Users, UserPlus } from "lucide-react";

export function CustomerAnalytics() {
  const [preset, setPreset] = useState<string>("all_time");

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["customer-analytics", preset],
    queryFn: () => getCustomerAnalytics(preset === "all_time" ? undefined : preset),
  });

  return (
    <article className="rounded-xl border border-border bg-white p-6 shadow-sm">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-base font-semibold text-slate-950">
            Customer Insights
          </h2>
          <p className="mt-1 text-xs text-slate-500">
            Customer acquisition and top spenders
          </p>
        </div>

        <select
          value={preset}
          onChange={(e) => setPreset(e.target.value)}
          className="rounded-lg border border-border bg-white px-3 py-1.5 text-xs font-medium text-slate-700 outline-none transition hover:border-slate-300 focus:border-primary focus:ring-1 focus:ring-primary"
        >
          <option value="all_time">All Time</option>
          <option value="this_month">This Month</option>
          <option value="this_week">This Week</option>
          <option value="today">Today</option>
        </select>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3">
        <div className="rounded-lg border border-border bg-slate-50 p-3.5">
          <div className="flex items-center gap-2">
            <Users className="h-4 w-4 text-primary" />
            <p className="text-xs font-medium text-slate-500">Total Customers</p>
          </div>
          <p className="mt-2 text-xl font-bold text-slate-950">
            {isLoading ? "..." : formatNumber(data?.total_customers)}
          </p>
        </div>

        <div className="rounded-lg border border-border bg-slate-50 p-3.5">
          <div className="flex items-center gap-2">
            <UserPlus className="h-4 w-4 text-accent" />
            <p className="text-xs font-medium text-slate-500">New in Period</p>
          </div>
          <p className="mt-2 text-xl font-bold text-slate-950">
            {isLoading ? "..." : formatNumber(data?.new_customers_in_period)}
          </p>
        </div>
      </div>

      <div className="mt-5">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">
          Top Spending Customers
        </h3>

        {isLoading ? (
          <div className="flex h-48 items-center justify-center">
            <LoadingSpinner message="Loading top customers..." />
          </div>
        ) : isError ? (
          <div className="flex h-48 items-center justify-center">
            <ErrorStateView
              message={
                error instanceof Error
                  ? error.message
                  : "Unable to load customer analytics."
              }
              onRetry={() => refetch()}
            />
          </div>
        ) : !data?.top_customers || data.top_customers.length === 0 ? (
          <div className="flex h-48 items-center justify-center">
            <EmptyStateView
              title="No customer purchases"
              message="Top spenders will appear once customer orders are placed."
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-border text-slate-400">
                  <th className="pb-2 font-medium">Customer</th>
                  <th className="pb-2 text-center font-medium">Orders</th>
                  <th className="pb-2 text-right font-medium">Total Spent</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data.top_customers.map((cust) => (
                  <tr key={cust.customer_id} className="hover:bg-slate-50">
                    <td className="py-2.5 pr-2">
                      <div className="flex items-center gap-2">
                        <div className="flex h-7 w-7 items-center justify-center rounded-full bg-slate-100 text-slate-600 font-semibold text-xs">
                          {cust.name ? cust.name.charAt(0).toUpperCase() : "C"}
                        </div>
                        <div className="min-w-0">
                          <p className="font-semibold text-slate-900 truncate max-w-[130px]">
                            {cust.name}
                          </p>
                          {cust.email && (
                            <p className="text-[10px] text-slate-400 truncate max-w-[130px]">
                              {cust.email}
                            </p>
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="py-2.5 px-2 text-center font-medium text-slate-700">
                      {formatNumber(cust.order_count)}
                    </td>
                    <td className="py-2.5 pl-2 text-right font-bold text-slate-950">
                      {formatCurrency(cust.total_spent)}
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
