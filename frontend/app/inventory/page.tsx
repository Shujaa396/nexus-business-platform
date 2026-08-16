"use client";

import React, { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertCircle,
  AlertTriangle,
  ArrowDownLeft,
  ArrowUpRight,
  Boxes,
  CheckCircle2,
  Download,
  History,
  Loader2,
  Package,
  Plus,
  RefreshCw,
  Sliders,
} from "lucide-react";

import AppShell from "../../components/app-shell";
import { formatNumber } from "../../components/dashboard/stat-card";
import { Modal } from "../../components/ui/modal";
import {
  EmptyStateView,
  ErrorStateView,
  LoadingSpinner,
} from "../../components/ui/state-views";
import { exportToCSV } from "../../lib/export";
import { listBranches } from "../../lib/branches";
import {
  adjustStock,
  getInventoryTransactions,
  listInventory,
  stockIn,
  stockOut,
} from "../../lib/inventory";
import { listProducts } from "../../lib/products";
import type {
  InventoryItem,
  InventoryTransaction,
  StockOpRequest,
  InventoryAdjust,
} from "../../types/inventory";

export default function InventoryPage() {
  const queryClient = useQueryClient();
  const [selectedBranch, setSelectedBranch] = useState<string>("");
  const [lowStockOnly, setLowStockOnly] = useState(false);

  // Modal states
  const [isStockInModalOpen, setIsStockInModalOpen] = useState(false);
  const [isStockOutModalOpen, setIsStockOutModalOpen] = useState(false);
  const [isAdjustModalOpen, setIsAdjustModalOpen] = useState(false);
  const [selectedItemForHistory, setSelectedItemForHistory] = useState<InventoryItem | null>(null);

  // Form states
  const [formBranchId, setFormBranchId] = useState("");
  const [formProductId, setFormProductId] = useState("");
  const [formQuantity, setFormQuantity] = useState("");
  const [formDirection, setFormDirection] = useState<"IN" | "OUT">("IN");
  const [formNotes, setFormNotes] = useState("");
  const [formError, setFormError] = useState("");

  // Queries
  const {
    data: inventory,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ["inventory", selectedBranch, lowStockOnly],
    queryFn: () =>
      listInventory({
        branch_id: selectedBranch || undefined,
        low_stock: lowStockOnly ? true : undefined,
      }),
  });

  const { data: branches } = useQuery({
    queryKey: ["branches"],
    queryFn: () => listBranches(),
  });

  const { data: products } = useQuery({
    queryKey: ["products"],
    queryFn: () => listProducts({ page_size: 100 }),
  });

  const { data: transactions, isLoading: isLoadingTx } = useQuery({
    queryKey: ["inventory-transactions", selectedItemForHistory?.id],
    queryFn: () =>
      selectedItemForHistory
        ? getInventoryTransactions(selectedItemForHistory.id)
        : Promise.resolve([]),
    enabled: !!selectedItemForHistory,
  });

  // Mutations
  const stockInMutation = useMutation({
    mutationFn: (data: StockOpRequest) => stockIn(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inventory"] });
      queryClient.invalidateQueries({ queryKey: ["product-analytics"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
      setIsStockInModalOpen(false);
      resetForm();
    },
    onError: (err: Error) => {
      setFormError(err.message || "Failed to complete stock-in.");
    },
  });

  const stockOutMutation = useMutation({
    mutationFn: (data: StockOpRequest) => stockOut(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inventory"] });
      queryClient.invalidateQueries({ queryKey: ["product-analytics"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
      setIsStockOutModalOpen(false);
      resetForm();
    },
    onError: (err: Error) => {
      setFormError(err.message || "Failed to complete stock-out.");
    },
  });

  const adjustMutation = useMutation({
    mutationFn: (data: InventoryAdjust) => adjustStock(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inventory"] });
      queryClient.invalidateQueries({ queryKey: ["product-analytics"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
      setIsAdjustModalOpen(false);
      resetForm();
    },
    onError: (err: Error) => {
      setFormError(err.message || "Failed to adjust stock.");
    },
  });

  const resetForm = () => {
    setFormBranchId(branches?.[0]?.id || "");
    setFormProductId(products?.[0]?.id || "");
    setFormQuantity("");
    setFormDirection("IN");
    setFormNotes("");
    setFormError("");
  };

  const handleOpenStockIn = (item?: InventoryItem) => {
    resetForm();
    if (item) {
      setFormBranchId(item.branch_id);
      setFormProductId(item.product_id);
    }
    setIsStockInModalOpen(true);
  };

  const handleOpenStockOut = (item?: InventoryItem) => {
    resetForm();
    if (item) {
      setFormBranchId(item.branch_id);
      setFormProductId(item.product_id);
    }
    setIsStockOutModalOpen(true);
  };

  const handleOpenAdjust = (item?: InventoryItem) => {
    resetForm();
    if (item) {
      setFormBranchId(item.branch_id);
      setFormProductId(item.product_id);
    }
    setIsAdjustModalOpen(true);
  };

  const handleSubmitStockIn = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError("");
    const qty = parseFloat(formQuantity);
    if (isNaN(qty) || qty <= 0) {
      setFormError("Quantity must be greater than 0.");
      return;
    }
    stockInMutation.mutate({
      branch_id: formBranchId,
      product_id: formProductId,
      quantity: qty,
      notes: formNotes || undefined,
    });
  };

  const handleSubmitStockOut = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError("");
    const qty = parseFloat(formQuantity);
    if (isNaN(qty) || qty <= 0) {
      setFormError("Quantity must be greater than 0.");
      return;
    }
    stockOutMutation.mutate({
      branch_id: formBranchId,
      product_id: formProductId,
      quantity: qty,
      notes: formNotes || undefined,
    });
  };

  const handleSubmitAdjust = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError("");
    const qty = parseFloat(formQuantity);
    if (isNaN(qty) || qty <= 0) {
      setFormError("Quantity must be greater than 0.");
      return;
    }
    adjustMutation.mutate({
      branch_id: formBranchId,
      product_id: formProductId,
      quantity: qty,
      direction: formDirection,
      notes: formNotes || undefined,
    });
  };

  const branchMap = new Map(branches?.map((b) => [b.id, b.name]) || []);
  const productMap = new Map(
    products?.map((p) => [p.id, { name: p.name, sku: p.sku }]) || [],
  );

  const handleExportCSV = () => {
    if (!inventory || inventory.length === 0) return;
    exportToCSV(
      "inventory_stock",
      inventory.map((item) => {
        const prod = productMap.get(item.product_id);
        const branchName = branchMap.get(item.branch_id);
        return {
          Branch: branchName || "—",
          SKU: prod?.sku || "—",
          ProductName: prod?.name || "—",
          AvailableQuantity: item.quantity,
          ReorderLevel: item.reorder_level,
          Status: Number(item.quantity) <= Number(item.reorder_level) ? "LOW_STOCK" : "NORMAL",
        };
      }),
    );
  };

  return (
    <AppShell>
      <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8 space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-primary">
              Stock & Warehousing
            </p>
            <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-950 sm:text-3xl">
              Inventory
            </h1>
            <p className="mt-1 text-xs text-slate-500">
              Multi-branch stock levels, reorder alerts, stock intake, and audit adjustments.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => refetch()}
              className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-white px-3 py-2 text-xs font-medium text-slate-700 shadow-sm transition hover:bg-slate-50"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Refresh
            </button>
            <button
              type="button"
              onClick={handleExportCSV}
              disabled={!inventory || inventory.length === 0}
              className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-white px-3 py-2 text-xs font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50 disabled:opacity-50"
            >
              <Download className="h-3.5 w-3.5" />
              Export CSV
            </button>
            <button
              type="button"
              onClick={() => handleOpenStockIn()}
              className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3.5 py-2 text-xs font-semibold text-white shadow-sm transition hover:opacity-90"
            >
              <Plus className="h-4 w-4" />
              Stock In
            </button>
            <button
              type="button"
              onClick={() => handleOpenAdjust()}
              className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-white px-3.5 py-2 text-xs font-semibold text-slate-800 shadow-sm transition hover:bg-slate-50"
            >
              <Sliders className="h-3.5 w-3.5 text-slate-500" />
              Adjust Stock
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between rounded-xl border border-border bg-white p-4 shadow-sm">
          <div className="flex items-center gap-3">
            <select
              value={selectedBranch}
              onChange={(e) => setSelectedBranch(e.target.value)}
              className="rounded-lg border border-border bg-white px-3 py-2 text-xs text-slate-700 outline-none focus:border-primary transition"
            >
              <option value="">All Branches</option>
              {branches?.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.name} ({b.code})
                </option>
              ))}
            </select>

            <label className="flex items-center gap-2 text-xs font-medium text-slate-700 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={lowStockOnly}
                onChange={(e) => setLowStockOnly(e.target.checked)}
                className="rounded border-border text-primary focus:ring-primary h-4 w-4"
              />
              <span>Low Stock Alerts Only</span>
            </label>
          </div>
        </div>

        {/* Inventory Table */}
        <div className="rounded-xl border border-border bg-white shadow-sm overflow-hidden">
          {isLoading ? (
            <div className="flex h-64 items-center justify-center">
              <LoadingSpinner message="Loading branch inventory..." />
            </div>
          ) : isError ? (
            <div className="p-8">
              <ErrorStateView
                message={
                  error instanceof Error
                    ? error.message
                    : "Unable to load inventory data."
                }
                onRetry={() => refetch()}
              />
            </div>
          ) : !inventory || inventory.length === 0 ? (
            <div className="p-8">
              <EmptyStateView
                title="No inventory records found"
                message={
                  lowStockOnly
                    ? "No items are currently below reorder levels."
                    : "No stock intake recorded. Click 'Stock In' to add inventory."
                }
              />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-border bg-slate-50 text-slate-500">
                    <th className="py-3.5 pl-6 pr-3 font-semibold">Product</th>
                    <th className="py-3.5 px-3 font-semibold">SKU</th>
                    <th className="py-3.5 px-3 font-semibold">Branch</th>
                    <th className="py-3.5 px-3 text-right font-semibold">Available Stock</th>
                    <th className="py-3.5 px-3 text-right font-semibold">Reorder Threshold</th>
                    <th className="py-3.5 px-3 text-center font-semibold">Stock Status</th>
                    <th className="py-3.5 pl-3 pr-6 text-right font-semibold">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {inventory.map((item) => {
                    const prod = productMap.get(item.product_id);
                    const branchName = branchMap.get(item.branch_id) || "Branch";
                    const qty = Number(item.quantity);
                    const reorder = Number(item.reorder_level);
                    const isLow = qty <= reorder;
                    const isOut = qty <= 0;

                    return (
                      <tr key={item.id} className="hover:bg-slate-50 transition">
                        <td className="py-3.5 pl-6 pr-3 font-semibold text-slate-900">
                          <div className="flex items-center gap-2">
                            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-teal-50 text-teal-700">
                              <Package className="h-3.5 w-3.5" />
                            </div>
                            <span>{prod?.name || "Product"}</span>
                          </div>
                        </td>
                        <td className="py-3.5 px-3 font-mono text-slate-500">
                          {prod?.sku || "—"}
                        </td>
                        <td className="py-3.5 px-3 text-slate-700 font-medium">
                          {branchName}
                        </td>
                        <td className="py-3.5 px-3 text-right font-bold text-slate-950">
                          {formatNumber(qty)}
                        </td>
                        <td className="py-3.5 px-3 text-right text-slate-500">
                          {formatNumber(reorder)}
                        </td>
                        <td className="py-3.5 px-3 text-center">
                          {isOut ? (
                            <span className="inline-flex items-center gap-1 rounded-full border border-rose-200 bg-rose-50 px-2.5 py-0.5 text-[11px] font-semibold text-rose-700">
                              <AlertTriangle className="h-3 w-3" />
                              Out of Stock
                            </span>
                          ) : isLow ? (
                            <span className="inline-flex items-center gap-1 rounded-full border border-amber-200 bg-amber-50 px-2.5 py-0.5 text-[11px] font-semibold text-amber-700">
                              <AlertTriangle className="h-3 w-3" />
                              Low Stock
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-0.5 text-[11px] font-semibold text-emerald-700">
                              <CheckCircle2 className="h-3 w-3" />
                              Optimal
                            </span>
                          )}
                        </td>
                        <td className="py-3.5 pl-3 pr-6 text-right">
                          <div className="flex items-center justify-end gap-1.5">
                            <button
                              type="button"
                              onClick={() => handleOpenStockIn(item)}
                              className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 hover:text-primary transition"
                              title="Add Stock"
                            >
                              <ArrowDownLeft className="h-3.5 w-3.5" />
                            </button>
                            <button
                              type="button"
                              onClick={() => handleOpenStockOut(item)}
                              className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 hover:text-amber-600 transition"
                              title="Stock Out"
                            >
                              <ArrowUpRight className="h-3.5 w-3.5" />
                            </button>
                            <button
                              type="button"
                              onClick={() => setSelectedItemForHistory(item)}
                              className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-800 transition"
                              title="Transaction History"
                            >
                              <History className="h-3.5 w-3.5" />
                            </button>
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
      </div>

      {/* Stock In Modal */}
      <Modal
        isOpen={isStockInModalOpen}
        onClose={() => setIsStockInModalOpen(false)}
        title="Stock Intake (Stock In)"
        description="Receive incoming stock for a branch location."
      >
        <form onSubmit={handleSubmitStockIn} className="space-y-4">
          {formError && (
            <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-2.5 text-xs text-red-700">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <p>{formError}</p>
            </div>
          )}

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-800">
              Destination Branch <span className="text-rose-500">*</span>
            </label>
            <select
              required
              value={formBranchId}
              onChange={(e) => setFormBranchId(e.target.value)}
              className="w-full rounded-lg border border-border bg-white px-3 py-2 text-xs outline-none focus:border-primary transition"
            >
              <option value="">Select branch...</option>
              {branches?.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.name} ({b.code})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-800">
              Product <span className="text-rose-500">*</span>
            </label>
            <select
              required
              value={formProductId}
              onChange={(e) => setFormProductId(e.target.value)}
              className="w-full rounded-lg border border-border bg-white px-3 py-2 text-xs outline-none focus:border-primary transition"
            >
              <option value="">Select product...</option>
              {products?.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.sku})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-800">
              Quantity to Receive <span className="text-rose-500">*</span>
            </label>
            <input
              type="number"
              step="1"
              min="1"
              required
              value={formQuantity}
              onChange={(e) => setFormQuantity(e.target.value)}
              placeholder="e.g. 50"
              className="w-full rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary transition"
            />
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-800">
              Audit Notes
            </label>
            <textarea
              rows={2}
              value={formNotes}
              onChange={(e) => setFormNotes(e.target.value)}
              placeholder="Purchase order or supplier reference notes..."
              className="w-full rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary transition"
            />
          </div>

          <div className="flex items-center justify-end gap-2 border-t border-border pt-4">
            <button
              type="button"
              onClick={() => setIsStockInModalOpen(false)}
              className="rounded-lg border border-border px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={stockInMutation.isPending}
              className="flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-xs font-semibold text-white shadow-sm transition hover:opacity-90 disabled:opacity-50"
            >
              {stockInMutation.isPending && (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              )}
              Confirm Stock In
            </button>
          </div>
        </form>
      </Modal>

      {/* Stock Out Modal */}
      <Modal
        isOpen={isStockOutModalOpen}
        onClose={() => setIsStockOutModalOpen(false)}
        title="Stock Out"
        description="Deduct stock from branch inventory."
      >
        <form onSubmit={handleSubmitStockOut} className="space-y-4">
          {formError && (
            <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-2.5 text-xs text-red-700">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <p>{formError}</p>
            </div>
          )}

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-800">
              Source Branch <span className="text-rose-500">*</span>
            </label>
            <select
              required
              value={formBranchId}
              onChange={(e) => setFormBranchId(e.target.value)}
              className="w-full rounded-lg border border-border bg-white px-3 py-2 text-xs outline-none focus:border-primary transition"
            >
              <option value="">Select branch...</option>
              {branches?.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.name} ({b.code})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-800">
              Product <span className="text-rose-500">*</span>
            </label>
            <select
              required
              value={formProductId}
              onChange={(e) => setFormProductId(e.target.value)}
              className="w-full rounded-lg border border-border bg-white px-3 py-2 text-xs outline-none focus:border-primary transition"
            >
              <option value="">Select product...</option>
              {products?.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.sku})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-800">
              Quantity to Deduct <span className="text-rose-500">*</span>
            </label>
            <input
              type="number"
              step="1"
              min="1"
              required
              value={formQuantity}
              onChange={(e) => setFormQuantity(e.target.value)}
              placeholder="e.g. 10"
              className="w-full rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary transition"
            />
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-800">
              Reason / Notes
            </label>
            <textarea
              rows={2}
              value={formNotes}
              onChange={(e) => setFormNotes(e.target.value)}
              placeholder="Damaged stock, transfer, or audit removal..."
              className="w-full rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary transition"
            />
          </div>

          <div className="flex items-center justify-end gap-2 border-t border-border pt-4">
            <button
              type="button"
              onClick={() => setIsStockOutModalOpen(false)}
              className="rounded-lg border border-border px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={stockOutMutation.isPending}
              className="flex items-center gap-1.5 rounded-lg bg-rose-600 px-4 py-2 text-xs font-semibold text-white shadow-sm transition hover:bg-rose-700 disabled:opacity-50"
            >
              {stockOutMutation.isPending && (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              )}
              Confirm Stock Out
            </button>
          </div>
        </form>
      </Modal>

      {/* Stock Adjustment Modal */}
      <Modal
        isOpen={isAdjustModalOpen}
        onClose={() => setIsAdjustModalOpen(false)}
        title="Stock Level Adjustment"
        description="Audit stock discrepancies with direct positive or negative adjustments."
      >
        <form onSubmit={handleSubmitAdjust} className="space-y-4">
          {formError && (
            <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-2.5 text-xs text-red-700">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <p>{formError}</p>
            </div>
          )}

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-800">
              Branch <span className="text-rose-500">*</span>
            </label>
            <select
              required
              value={formBranchId}
              onChange={(e) => setFormBranchId(e.target.value)}
              className="w-full rounded-lg border border-border bg-white px-3 py-2 text-xs outline-none focus:border-primary transition"
            >
              <option value="">Select branch...</option>
              {branches?.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.name} ({b.code})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-800">
              Product <span className="text-rose-500">*</span>
            </label>
            <select
              required
              value={formProductId}
              onChange={(e) => setFormProductId(e.target.value)}
              className="w-full rounded-lg border border-border bg-white px-3 py-2 text-xs outline-none focus:border-primary transition"
            >
              <option value="">Select product...</option>
              {products?.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.sku})
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-800">
                Direction <span className="text-rose-500">*</span>
              </label>
              <select
                value={formDirection}
                onChange={(e) => setFormDirection(e.target.value as "IN" | "OUT")}
                className="w-full rounded-lg border border-border bg-white px-3 py-2 text-xs outline-none focus:border-primary transition"
              >
                <option value="IN">Add Stock (+ IN)</option>
                <option value="OUT">Deduct Stock (- OUT)</option>
              </select>
            </div>

            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-800">
                Quantity <span className="text-rose-500">*</span>
              </label>
              <input
                type="number"
                step="1"
                min="1"
                required
                value={formQuantity}
                onChange={(e) => setFormQuantity(e.target.value)}
                placeholder="e.g. 5"
                className="w-full rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary transition"
              />
            </div>
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-800">
              Audit Notes
            </label>
            <textarea
              rows={2}
              value={formNotes}
              onChange={(e) => setFormNotes(e.target.value)}
              placeholder="Physical stock count reconciliation notes..."
              className="w-full rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary transition"
            />
          </div>

          <div className="flex items-center justify-end gap-2 border-t border-border pt-4">
            <button
              type="button"
              onClick={() => setIsAdjustModalOpen(false)}
              className="rounded-lg border border-border px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={adjustMutation.isPending}
              className="flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-xs font-semibold text-white shadow-sm transition hover:opacity-90 disabled:opacity-50"
            >
              {adjustMutation.isPending && (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              )}
              Save Adjustment
            </button>
          </div>
        </form>
      </Modal>

      {/* Transaction History Modal */}
      <Modal
        isOpen={!!selectedItemForHistory}
        onClose={() => setSelectedItemForHistory(null)}
        title="Stock Transaction Audit Log"
        description="Chronological log of stock movements, fulfillments, and adjustments."
        maxWidth="xl"
      >
        <div className="space-y-4">
          {isLoadingTx ? (
            <div className="flex h-48 items-center justify-center">
              <LoadingSpinner message="Loading transaction logs..." />
            </div>
          ) : !transactions || transactions.length === 0 ? (
            <div className="py-8 text-center text-xs text-slate-400">
              No transactions recorded for this item yet.
            </div>
          ) : (
            <div className="overflow-x-auto max-h-96">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-border bg-slate-50 text-slate-500">
                    <th className="py-2.5 px-3 font-semibold">Type</th>
                    <th className="py-2.5 px-3 text-right font-semibold">Quantity</th>
                    <th className="py-2.5 px-3 font-semibold">Reference</th>
                    <th className="py-2.5 px-3 font-semibold">Notes</th>
                    <th className="py-2.5 px-3 text-right font-semibold">Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {transactions.map((tx) => (
                    <tr key={tx.id} className="hover:bg-slate-50">
                      <td className="py-2.5 px-3 font-semibold">
                        <span
                          className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold ${
                            tx.transaction_type.includes("IN")
                              ? "bg-emerald-50 text-emerald-700"
                              : tx.transaction_type.includes("OUT")
                              ? "bg-rose-50 text-rose-700"
                              : "bg-blue-50 text-blue-700"
                          }`}
                        >
                          {tx.transaction_type}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-right font-mono font-bold text-slate-900">
                        {formatNumber(Number(tx.quantity))}
                      </td>
                      <td className="py-2.5 px-3 text-slate-500 font-mono text-[11px]">
                        {tx.reference_type || "Direct Op"}
                      </td>
                      <td className="py-2.5 px-3 text-slate-600 max-w-xs truncate">
                        {tx.notes || "—"}
                      </td>
                      <td className="py-2.5 px-3 text-right text-slate-400">
                        {new Date(tx.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <div className="flex justify-end border-t border-border pt-4">
            <button
              type="button"
              onClick={() => setSelectedItemForHistory(null)}
              className="rounded-lg border border-border px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition"
            >
              Close
            </button>
          </div>
        </div>
      </Modal>
    </AppShell>
  );
}
