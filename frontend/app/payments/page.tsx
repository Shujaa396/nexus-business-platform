"use client";

import React, { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Banknote,
  CheckCircle2,
  CreditCard,
  Download,
  Filter,
  RefreshCw,
  RotateCcw,
  Search,
  Wallet,
} from "lucide-react";

import AppShell from "../../components/app-shell";
import { formatCurrency } from "../../components/dashboard/stat-card";
import { StatusBadge } from "../../components/ui/badge";
import { ConfirmDialog } from "../../components/ui/confirm-dialog";
import {
  EmptyStateView,
  ErrorStateView,
  LoadingSpinner,
} from "../../components/ui/state-views";
import { exportToCSV } from "../../lib/export";
import { listOrders } from "../../lib/orders";
import { listPayments, refundPayment } from "../../lib/payments";
import type { Payment } from "../../types/orders";

export default function PaymentsPage() {
  const queryClient = useQueryClient();
  const [selectedStatus, setSelectedStatus] = useState<string>("");
  const [selectedMethod, setSelectedMethod] = useState<string>("");
  const [refundingPayment, setRefundingPayment] = useState<Payment | null>(null);

  // Queries
  const {
    data: payments,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ["payments", selectedStatus, selectedMethod],
    queryFn: () =>
      listPayments({
        status: selectedStatus || undefined,
        payment_method: selectedMethod || undefined,
      }),
  });

  const { data: orders } = useQuery({
    queryKey: ["orders"],
    queryFn: () => listOrders({ page_size: 100 }),
  });

  // Mutations
  const refundMutation = useMutation({
    mutationFn: (paymentId: string) => refundPayment(paymentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["payments"] });
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
      setRefundingPayment(null);
    },
  });

  const orderMap = new Map(orders?.map((o) => [o.id, o.order_number]) || []);

  const totalCollected = payments
    ?.filter((p) => p.status === "COMPLETED")
    .reduce((sum, p) => sum + Number(p.amount), 0) || 0;

  const totalRefunded = payments
    ?.filter((p) => p.status === "REFUNDED")
    .reduce((sum, p) => sum + Number(p.amount), 0) || 0;

  const handleExportCSV = () => {
    if (!payments || payments.length === 0) return;
    exportToCSV(
      "payments_ledger",
      payments.map((p) => ({
        PaymentID: p.id,
        OrderNumber: orderMap.get(p.order_id) || "—",
        PaymentMethod: p.payment_method,
        Amount: p.amount,
        Status: p.status,
        Reference: p.reference || "—",
        Date: new Date(p.created_at).toISOString().split("T")[0],
      })),
    );
  };

  return (
    <AppShell>
      <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8 space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-primary">
              Financial Operations
            </p>
            <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-950 sm:text-3xl">
              Payments
            </h1>
            <p className="mt-1 text-xs text-slate-500">
              Audit cash inflow, card transactions, bank settlements, and issue refunds.
            </p>
          </div>

          <div className="flex items-center gap-2">
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
              disabled={!payments || payments.length === 0}
              className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-white px-3 py-2 text-xs font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50 disabled:opacity-50"
            >
              <Download className="h-3.5 w-3.5" />
              Export CSV
            </button>
          </div>
        </div>

        {/* Quick Summary Metric Cards */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div className="rounded-xl border border-border bg-white p-4 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-50 text-emerald-700">
                <Banknote className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs text-slate-500 font-medium">
                  Total Collected (Completed)
                </p>
                <p className="text-lg font-bold text-slate-950">
                  {formatCurrency(totalCollected)}
                </p>
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-border bg-white p-4 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-50 text-purple-700">
                <RotateCcw className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs text-slate-500 font-medium">
                  Total Refunded
                </p>
                <p className="text-lg font-bold text-slate-950">
                  {formatCurrency(totalRefunded)}
                </p>
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-border bg-white p-4 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-50 text-teal-700">
                <Wallet className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs text-slate-500 font-medium">
                  Net Settlement Volume
                </p>
                <p className="text-lg font-bold text-teal-700">
                  {formatCurrency(totalCollected - totalRefunded)}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between rounded-xl border border-border bg-white p-4 shadow-sm">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-1.5">
              <Filter className="h-4 w-4 text-slate-400" />
              <select
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
                className="rounded-lg border border-border bg-white px-3 py-2 text-xs text-slate-700 outline-none focus:border-primary transition"
              >
                <option value="">All Payment Statuses</option>
                <option value="COMPLETED">COMPLETED</option>
                <option value="REFUNDED">REFUNDED</option>
              </select>
            </div>

            <select
              value={selectedMethod}
              onChange={(e) => setSelectedMethod(e.target.value)}
              className="rounded-lg border border-border bg-white px-3 py-2 text-xs text-slate-700 outline-none focus:border-primary transition"
            >
              <option value="">All Payment Methods</option>
              <option value="CASH">Cash</option>
              <option value="CARD">Debit / Credit Card</option>
              <option value="BANK_TRANSFER">Bank Transfer</option>
              <option value="CHEQUE">Cheque</option>
              <option value="ONLINE">Online Gateway</option>
            </select>
          </div>
        </div>

        {/* Payments Table */}
        <div className="rounded-xl border border-border bg-white shadow-sm overflow-hidden">
          {isLoading ? (
            <div className="flex h-64 items-center justify-center">
              <LoadingSpinner message="Loading payments ledger..." />
            </div>
          ) : isError ? (
            <div className="p-8">
              <ErrorStateView
                message={
                  error instanceof Error
                    ? error.message
                    : "Unable to load payments."
                }
                onRetry={() => refetch()}
              />
            </div>
          ) : !payments || payments.length === 0 ? (
            <div className="p-8">
              <EmptyStateView
                title="No payment transactions found"
                message="No payments recorded under the selected filters."
              />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-border bg-slate-50 text-slate-500">
                    <th className="py-3.5 pl-6 pr-3 font-semibold">Payment ID</th>
                    <th className="py-3.5 px-3 font-semibold">Order Reference</th>
                    <th className="py-3.5 px-3 font-semibold">Payment Method</th>
                    <th className="py-3.5 px-3 text-right font-semibold">Amount</th>
                    <th className="py-3.5 px-3 text-center font-semibold">Status</th>
                    <th className="py-3.5 px-3 font-semibold">Reference / Notes</th>
                    <th className="py-3.5 px-3 font-semibold">Date & Time</th>
                    <th className="py-3.5 pl-3 pr-6 text-right font-semibold">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {payments.map((p) => {
                    const orderNum = orderMap.get(p.order_id) || "Order";

                    return (
                      <tr key={p.id} className="hover:bg-slate-50 transition">
                        <td className="py-3.5 pl-6 pr-3 font-mono font-medium text-slate-500 text-[11px]">
                          {p.id.substring(0, 8)}...
                        </td>
                        <td className="py-3.5 px-3 font-mono font-bold text-slate-900">
                          {orderNum}
                        </td>
                        <td className="py-3.5 px-3 font-semibold text-slate-800">
                          <div className="flex items-center gap-1.5">
                            <CreditCard className="h-3.5 w-3.5 text-slate-400" />
                            <span>{p.payment_method}</span>
                          </div>
                        </td>
                        <td className="py-3.5 px-3 text-right font-bold font-mono text-slate-950">
                          {formatCurrency(p.amount)}
                        </td>
                        <td className="py-3.5 px-3 text-center">
                          <StatusBadge status={p.status} />
                        </td>
                        <td className="py-3.5 px-3 text-slate-500 font-mono text-[11px] max-w-xs truncate">
                          {p.reference || "—"}
                        </td>
                        <td className="py-3.5 px-3 text-slate-500 font-mono text-[11px]">
                          {new Date(p.created_at).toLocaleString()}
                        </td>
                        <td className="py-3.5 pl-3 pr-6 text-right">
                          {p.status === "COMPLETED" && (
                            <button
                              type="button"
                              onClick={() => setRefundingPayment(p)}
                              className="inline-flex items-center gap-1 rounded-lg border border-border px-2.5 py-1 text-[11px] font-semibold text-slate-700 hover:bg-rose-50 hover:border-rose-200 hover:text-rose-600 transition"
                            >
                              <RotateCcw className="h-3 w-3" />
                              Refund
                            </button>
                          )}
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

      {/* Refund Confirmation Dialog */}
      <ConfirmDialog
        isOpen={!!refundingPayment}
        onClose={() => setRefundingPayment(null)}
        onConfirm={() =>
          refundingPayment && refundMutation.mutate(refundingPayment.id)
        }
        title="Refund Payment"
        message={`Are you sure you want to refund ${formatCurrency(
          refundingPayment?.amount || 0,
        )}? Refunding will update the order payment status to UNPAID or PARTIAL.`}
        confirmText="Confirm Refund"
        variant="warning"
        isLoading={refundMutation.isPending}
      />
    </AppShell>
  );
}
