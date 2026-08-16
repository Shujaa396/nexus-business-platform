"use client";

import React from "react";
import { AlertTriangle, CheckCircle2 } from "lucide-react";
import type { LowStockItem } from "../../types/dashboard";
import { ErrorStateView, LoadingSpinner } from "../ui/state-views";

export function LowStockTable({
  items,
  isLoading,
  isError,
  errorMessage,
  onRetry,
}: {
  items: LowStockItem[] | undefined;
  isLoading: boolean;
  isError: boolean;
  errorMessage?: string;
  onRetry?: () => void;
}) {
  return (
    <article className="min-h-[380px] rounded-xl border border-border bg-white p-6 shadow-sm flex flex-col">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-base font-semibold text-slate-950">
              Low Stock Alerts
            </h2>
            {items && items.length > 0 && (
              <span className="rounded-full bg-rose-100 px-2 py-0.5 text-xs font-semibold text-rose-700">
                {items.length}
              </span>
            )}
          </div>
          <p className="mt-1 text-xs text-slate-500">
            Products that require immediate reordering
          </p>
        </div>
      </div>

      <div className="mt-4 flex-1 flex flex-col justify-center">
        {isLoading ? (
          <div className="flex h-56 items-center justify-center">
            <LoadingSpinner message="Checking inventory levels..." />
          </div>
        ) : isError ? (
          <div className="flex h-56 items-center justify-center">
            <ErrorStateView
              message={errorMessage || "Unable to load low-stock data."}
              onRetry={onRetry}
            />
          </div>
        ) : !items || items.length === 0 ? (
          <div className="flex h-56 flex-col items-center justify-center text-center p-6">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-50 text-emerald-600">
              <CheckCircle2 className="h-6 w-6" />
            </div>
            <p className="mt-3 text-sm font-semibold text-slate-800">
              No low-stock products.
            </p>
            <p className="mt-1 text-xs text-slate-400 max-w-xs">
              All inventory levels are currently above their reorder thresholds.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-border text-slate-400">
                  <th className="pb-2 font-medium">Product</th>
                  <th className="pb-2 font-medium">Branch</th>
                  <th className="pb-2 text-right font-medium">Stock / Reorder</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {items.map((item) => {
                  const qty = Number(item.quantity);
                  const reorder = Number(item.reorder_level);
                  const isOut = qty <= 0;

                  return (
                    <tr key={item.inventory_item_id} className="hover:bg-slate-50">
                      <td className="py-2.5 pr-2">
                        <p className="font-semibold text-slate-900 truncate max-w-[140px]">
                          {item.name}
                        </p>
                        <p className="text-[10px] text-slate-400">{item.sku}</p>
                      </td>
                      <td className="py-2.5 px-2 text-slate-600 truncate max-w-[100px]">
                        {item.branch_name}
                      </td>
                      <td className="py-2.5 pl-2 text-right">
                        <div className="flex flex-col items-end">
                          <span
                            className={`inline-flex items-center gap-1 font-bold ${
                              isOut ? "text-rose-600" : "text-amber-600"
                            }`}
                          >
                            <AlertTriangle className="h-3 w-3" />
                            {qty} / {reorder}
                          </span>
                          <span className="text-[10px] text-slate-400">
                            {isOut ? "Out of stock" : "Low stock"}
                          </span>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </article>
  );
}
