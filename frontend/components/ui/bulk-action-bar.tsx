"use client";

import React from "react";
import { CheckSquare, Download, Trash2, X } from "lucide-react";

type BulkActionBarProps = {
  selectedCount: number;
  onClear: () => void;
  onBulkDeactivate?: () => void;
  onBulkExport?: () => void;
  isLoading?: boolean;
  resourceName?: string;
};

export function BulkActionBar({
  selectedCount,
  onClear,
  onBulkDeactivate,
  onBulkExport,
  isLoading = false,
  resourceName = "items",
}: BulkActionBarProps) {
  if (selectedCount === 0) return null;

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 flex items-center gap-3 rounded-xl border border-slate-800 bg-slate-900 px-5 py-3 text-white shadow-2xl animate-in fade-in slide-in-from-bottom-4">
      <div className="flex items-center gap-2 pr-3 border-r border-slate-700">
        <CheckSquare className="h-4 w-4 text-teal-400" />
        <span className="text-xs font-semibold">
          {selectedCount} {resourceName} selected
        </span>
      </div>

      <div className="flex items-center gap-2">
        {onBulkExport && (
          <button
            type="button"
            onClick={onBulkExport}
            disabled={isLoading}
            className="inline-flex items-center gap-1.5 rounded-lg bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-700 hover:text-white transition disabled:opacity-50"
          >
            <Download className="h-3.5 w-3.5" />
            Export Selected
          </button>
        )}

        {onBulkDeactivate && (
          <button
            type="button"
            onClick={onBulkDeactivate}
            disabled={isLoading}
            className="inline-flex items-center gap-1.5 rounded-lg bg-rose-600/90 px-3 py-1.5 text-xs font-medium text-white hover:bg-rose-600 transition disabled:opacity-50"
          >
            <Trash2 className="h-3.5 w-3.5" />
            Deactivate Selected
          </button>
        )}

        <button
          type="button"
          onClick={onClear}
          className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white transition"
          title="Clear Selection"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
