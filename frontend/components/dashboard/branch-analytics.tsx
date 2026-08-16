"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { getBranchAnalytics } from "../../lib/dashboard";
import { formatCurrency, formatNumber } from "./stat-card";
import { EmptyStateView, ErrorStateView, LoadingSpinner } from "../ui/state-views";
import { Building2 } from "lucide-react";

export function BranchAnalytics() {
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["branch-analytics"],
    queryFn: getBranchAnalytics,
  });

  const branches = data?.branches ?? [];

  return (
    <article className="rounded-xl border border-border bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-base font-semibold text-slate-950">
              Branch Performance
            </h2>
            {branches.length > 0 && (
              <span className="rounded-md bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-700">
                {branches.length} {branches.length === 1 ? "Branch" : "Branches"}
              </span>
            )}
          </div>
          <p className="mt-1 text-xs text-slate-500">
            Multi-branch revenue, order volume, and inventory distribution
          </p>
        </div>
      </div>

      <div className="mt-5">
        {isLoading ? (
          <div className="flex h-56 items-center justify-center">
            <LoadingSpinner message="Loading branch analytics..." />
          </div>
        ) : isError ? (
          <div className="flex h-56 items-center justify-center">
            <ErrorStateView
              message={
                error instanceof Error
                  ? error.message
                  : "Unable to load branch analytics."
              }
              onRetry={() => refetch()}
            />
          </div>
        ) : branches.length === 0 ? (
          <div className="flex h-56 items-center justify-center">
            <EmptyStateView
              title="No branches registered"
              message="Add branches to monitor distributed performance and inventory."
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-border text-xs text-slate-400">
                  <th className="pb-3 font-medium">Branch</th>
                  <th className="pb-3 font-medium">Code</th>
                  <th className="pb-3 text-right font-medium">Orders</th>
                  <th className="pb-3 text-right font-medium">Revenue</th>
                  <th className="pb-3 text-right font-medium">Inventory Items</th>
                  <th className="pb-3 text-right font-medium">Inventory Value</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {branches.map((branch) => (
                  <tr key={branch.branch_id} className="hover:bg-slate-50">
                    <td className="py-3 pr-4">
                      <div className="flex items-center gap-2.5">
                        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-teal-50 text-teal-700">
                          <Building2 className="h-4 w-4" />
                        </div>
                        <span className="font-semibold text-slate-900">
                          {branch.name}
                        </span>
                      </div>
                    </td>
                    <td className="py-3 px-2 text-xs font-mono text-slate-500">
                      {branch.code}
                    </td>
                    <td className="py-3 px-2 text-right font-medium text-slate-700">
                      {formatNumber(branch.order_count)}
                    </td>
                    <td className="py-3 px-2 text-right font-semibold text-slate-950">
                      {formatCurrency(branch.revenue)}
                    </td>
                    <td className="py-3 px-2 text-right font-medium text-slate-700">
                      {formatNumber(branch.inventory_items_count)}
                    </td>
                    <td className="py-3 pl-2 text-right font-semibold text-emerald-700">
                      {formatCurrency(branch.inventory_value)}
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
