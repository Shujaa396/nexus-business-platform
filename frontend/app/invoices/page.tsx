"use client";

import React, { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertCircle,
  Banknote,
  Download,
  Eye,
  FileCheck,
  FileSpreadsheet,
  FileText,
  Filter,
  Loader2,
  Plus,
  Printer,
  RefreshCw,
  Search,
  XCircle,
} from "lucide-react";

import AppShell from "../../components/app-shell";
import { formatCurrency, formatNumber } from "../../components/dashboard/stat-card";
import { StatusBadge } from "../../components/ui/badge";
import { ConfirmDialog } from "../../components/ui/confirm-dialog";
import { Modal } from "../../components/ui/modal";
import {
  EmptyStateView,
  ErrorStateView,
  LoadingSpinner,
} from "../../components/ui/state-views";
import { exportToCSV } from "../../lib/export";
import { listCustomers } from "../../lib/customers";
import {
  createInvoice,
  getInvoice,
  issueInvoice,
  listInvoices,
  recordInvoicePayment,
  voidInvoice,
} from "../../lib/invoices";
import { listOrders } from "../../lib/orders";
import type {
  Invoice,
  InvoiceCreate,
  InvoicePayment,
} from "../../types/invoices";

export default function InvoicesPage() {
  const queryClient = useQueryClient();
  const [searchInvoiceNumber, setSearchInvoiceNumber] = useState("");
  const [selectedStatus, setSelectedStatus] = useState<string>("");

  // Modals
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [selectedInvoiceForDetail, setSelectedInvoiceForDetail] = useState<Invoice | null>(null);
  const [selectedInvoiceForPayment, setSelectedInvoiceForPayment] = useState<Invoice | null>(null);
  const [confirmActionInvoice, setConfirmActionInvoice] = useState<{
    invoice: Invoice;
    action: "issue" | "void";
  } | null>(null);

  // Form states
  const [formOrderId, setFormOrderId] = useState("");
  const [formDueDate, setFormDueDate] = useState("");
  const [formNotes, setFormNotes] = useState("");
  const [formError, setFormError] = useState("");

  // Payment states
  const [paymentAmount, setPaymentAmount] = useState("");
  const [paymentMethod, setPaymentMethod] = useState("CASH");
  const [paymentReference, setPaymentReference] = useState("");
  const [paymentError, setPaymentError] = useState("");

  // Queries
  const {
    data: invoices,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ["invoices", searchInvoiceNumber, selectedStatus],
    queryFn: () =>
      listInvoices({
        invoice_number: searchInvoiceNumber || undefined,
        status: selectedStatus || undefined,
      }),
  });

  const { data: customers } = useQuery({
    queryKey: ["customers"],
    queryFn: () => listCustomers({ page_size: 100 }),
  });

  const { data: orders } = useQuery({
    queryKey: ["orders"],
    queryFn: () => listOrders({ page_size: 100 }),
  });

  const { data: activeInvoiceDetail } = useQuery({
    queryKey: ["invoice-detail", selectedInvoiceForDetail?.id],
    queryFn: () =>
      selectedInvoiceForDetail
        ? getInvoice(selectedInvoiceForDetail.id)
        : null,
    enabled: !!selectedInvoiceForDetail,
  });

  // Mutations
  const createMutation = useMutation({
    mutationFn: (data: InvoiceCreate) => createInvoice(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["invoices"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
      setIsCreateModalOpen(false);
      resetCreateForm();
    },
    onError: (err: Error) => {
      setFormError(err.message || "Failed to create invoice.");
    },
  });

  const issueMutation = useMutation({
    mutationFn: (invoiceId: string) => issueInvoice(invoiceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["invoices"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
      setConfirmActionInvoice(null);
      if (selectedInvoiceForDetail) {
        queryClient.invalidateQueries({
          queryKey: ["invoice-detail", selectedInvoiceForDetail.id],
        });
      }
    },
  });

  const voidMutation = useMutation({
    mutationFn: (invoiceId: string) => voidInvoice(invoiceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["invoices"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
      setConfirmActionInvoice(null);
      if (selectedInvoiceForDetail) {
        queryClient.invalidateQueries({
          queryKey: ["invoice-detail", selectedInvoiceForDetail.id],
        });
      }
    },
  });

  const paymentMutation = useMutation({
    mutationFn: ({
      invoiceId,
      data,
    }: {
      invoiceId: string;
      data: InvoicePayment;
    }) => recordInvoicePayment(invoiceId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["invoices"] });
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      queryClient.invalidateQueries({ queryKey: ["payments"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
      if (selectedInvoiceForDetail) {
        queryClient.invalidateQueries({
          queryKey: ["invoice-detail", selectedInvoiceForDetail.id],
        });
      }
      setSelectedInvoiceForPayment(null);
      setPaymentAmount("");
      setPaymentReference("");
    },
    onError: (err: Error) => {
      setPaymentError(err.message || "Failed to record payment.");
    },
  });

  const resetCreateForm = () => {
    setFormOrderId(orders?.[0]?.id || "");
    setFormDueDate("");
    setFormNotes("");
    setFormError("");
  };

  const handleOpenCreate = () => {
    resetCreateForm();
    setIsCreateModalOpen(true);
  };

  const handleSubmitCreate = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError("");
    if (!formOrderId) {
      setFormError("Please select an order.");
      return;
    }
    createMutation.mutate({
      order_id: formOrderId,
      due_date: formDueDate || undefined,
      notes: formNotes || undefined,
    });
  };

  const handleSubmitPayment = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedInvoiceForPayment) return;
    setPaymentError("");

    const amt = parseFloat(paymentAmount);
    if (isNaN(amt) || amt <= 0) {
      setPaymentError("Payment amount must be greater than 0.");
      return;
    }

    paymentMutation.mutate({
      invoiceId: selectedInvoiceForPayment.id,
      data: {
        amount: amt,
        payment_method: paymentMethod,
        reference: paymentReference || undefined,
      },
    });
  };

  const customerMap = new Map(customers?.map((c) => [c.id, c.name]) || []);
  const orderMap = new Map(orders?.map((o) => [o.id, o.order_number]) || []);

  const handleExportCSV = () => {
    if (!invoices || invoices.length === 0) return;
    exportToCSV(
      "invoices_ledger",
      invoices.map((inv) => ({
        InvoiceNumber: inv.invoice_number,
        Customer: inv.customer_id ? customerMap.get(inv.customer_id) || "Customer" : "Walk-in",
        Subtotal: inv.subtotal,
        DiscountTotal: inv.discount_total,
        TaxTotal: inv.tax_total,
        Total: inv.total,
        AmountPaid: inv.amount_paid,
        BalanceDue: Number(inv.total) - Number(inv.amount_paid),
        Status: inv.status,
        IssueDate: inv.issue_date ? new Date(inv.issue_date).toLocaleDateString() : "—",
        DueDate: inv.due_date ? new Date(inv.due_date).toLocaleDateString() : "—",
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
              Billing & Accounts Receivable
            </p>
            <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-950 sm:text-3xl">
              Invoices
            </h1>
            <p className="mt-1 text-xs text-slate-500">
              Generate tax invoices, track payment status, issue bills, and manage receivables.
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
              disabled={!invoices || invoices.length === 0}
              className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-white px-3 py-2 text-xs font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50 disabled:opacity-50"
            >
              <Download className="h-3.5 w-3.5" />
              Export CSV
            </button>
            <button
              type="button"
              onClick={handleOpenCreate}
              className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3.5 py-2 text-xs font-semibold text-white shadow-sm transition hover:opacity-90"
            >
              <Plus className="h-4 w-4" />
              Generate Invoice
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between rounded-xl border border-border bg-white p-4 shadow-sm">
          <div className="relative flex-1 max-w-xs">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              type="search"
              value={searchInvoiceNumber}
              onChange={(e) => setSearchInvoiceNumber(e.target.value)}
              placeholder="Search by invoice number..."
              className="w-full rounded-lg border border-border bg-slate-50 py-2 pl-9 pr-3 text-xs outline-none focus:border-primary focus:bg-white transition"
            />
          </div>

          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-slate-400" />
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="rounded-lg border border-border bg-white px-3 py-2 text-xs text-slate-700 outline-none focus:border-primary transition"
            >
              <option value="">All Invoice Statuses</option>
              <option value="DRAFT">DRAFT</option>
              <option value="ISSUED">ISSUED</option>
              <option value="PARTIAL">PARTIAL</option>
              <option value="PAID">PAID</option>
              <option value="VOID">VOID</option>
            </select>
          </div>
        </div>

        {/* Invoices Table */}
        <div className="rounded-xl border border-border bg-white shadow-sm overflow-hidden">
          {isLoading ? (
            <div className="flex h-64 items-center justify-center">
              <LoadingSpinner message="Loading invoices ledger..." />
            </div>
          ) : isError ? (
            <div className="p-8">
              <ErrorStateView
                message={
                  error instanceof Error
                    ? error.message
                    : "Unable to load invoices."
                }
                onRetry={() => refetch()}
              />
            </div>
          ) : !invoices || invoices.length === 0 ? (
            <div className="p-8">
              <EmptyStateView
                title="No invoices found"
                message={
                  searchInvoiceNumber || selectedStatus
                    ? "No invoices match your search filters."
                    : "No invoices created yet. Click 'Generate Invoice' to create your first tax bill."
                }
              />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-border bg-slate-50 text-slate-500">
                    <th className="py-3.5 pl-6 pr-3 font-semibold">Invoice #</th>
                    <th className="py-3.5 px-3 font-semibold">Order Ref</th>
                    <th className="py-3.5 px-3 font-semibold">Customer</th>
                    <th className="py-3.5 px-3 text-right font-semibold">Total Amount</th>
                    <th className="py-3.5 px-3 text-right font-semibold">Amount Paid</th>
                    <th className="py-3.5 px-3 text-center font-semibold">Status</th>
                    <th className="py-3.5 px-3 font-semibold">Due Date</th>
                    <th className="py-3.5 pl-3 pr-6 text-right font-semibold">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {invoices.map((inv) => {
                    const custName = inv.customer_id
                      ? customerMap.get(inv.customer_id) || "Customer"
                      : "Walk-in Customer";
                    const orderNum = inv.order_id
                      ? orderMap.get(inv.order_id) || "Order"
                      : "—";

                    return (
                      <tr key={inv.id} className="hover:bg-slate-50 transition">
                        <td className="py-3.5 pl-6 pr-3 font-mono font-bold text-slate-900">
                          <div className="flex items-center gap-2">
                            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-teal-50 text-teal-700">
                              <FileText className="h-3.5 w-3.5" />
                            </div>
                            <span>{inv.invoice_number}</span>
                          </div>
                        </td>
                        <td className="py-3.5 px-3 font-mono text-slate-600">
                          {orderNum}
                        </td>
                        <td className="py-3.5 px-3 font-semibold text-slate-800">
                          {custName}
                        </td>
                        <td className="py-3.5 px-3 text-right font-bold text-slate-950">
                          {formatCurrency(inv.total)}
                        </td>
                        <td className="py-3.5 px-3 text-right font-medium text-emerald-700">
                          {formatCurrency(inv.amount_paid)}
                        </td>
                        <td className="py-3.5 px-3 text-center">
                          <StatusBadge status={inv.status} />
                        </td>
                        <td className="py-3.5 px-3 text-slate-500 font-mono text-[11px]">
                          {inv.due_date
                            ? new Date(inv.due_date).toLocaleDateString()
                            : "—"}
                        </td>
                        <td className="py-3.5 pl-3 pr-6 text-right">
                          <div className="flex items-center justify-end gap-1.5">
                            <button
                              type="button"
                              onClick={() => setSelectedInvoiceForDetail(inv)}
                              className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-900 transition"
                              title="View Invoice"
                            >
                              <Eye className="h-3.5 w-3.5" />
                            </button>

                            {inv.status === "DRAFT" && (
                              <button
                                type="button"
                                onClick={() =>
                                  setConfirmActionInvoice({
                                    invoice: inv,
                                    action: "issue",
                                  })
                                }
                                className="rounded-lg p-1.5 text-teal-600 hover:bg-teal-50 transition"
                                title="Issue Invoice"
                              >
                                <FileCheck className="h-3.5 w-3.5" />
                              </button>
                            )}

                            {inv.status !== "PAID" && inv.status !== "VOID" && (
                              <button
                                type="button"
                                onClick={() => setSelectedInvoiceForPayment(inv)}
                                className="rounded-lg p-1.5 text-emerald-600 hover:bg-emerald-50 transition"
                                title="Record Payment"
                              >
                                <Banknote className="h-3.5 w-3.5" />
                              </button>
                            )}

                            {inv.status !== "VOID" && inv.status !== "PAID" && (
                              <button
                                type="button"
                                onClick={() =>
                                  setConfirmActionInvoice({
                                    invoice: inv,
                                    action: "void",
                                  })
                                }
                                className="rounded-lg p-1.5 text-rose-500 hover:bg-rose-50 transition"
                                title="Void Invoice"
                              >
                                <XCircle className="h-3.5 w-3.5" />
                              </button>
                            )}
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

      {/* Generate Invoice Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Generate Tax Invoice"
        description="Select an existing order to generate a formal tax invoice."
      >
        <form onSubmit={handleSubmitCreate} className="space-y-4">
          {formError && (
            <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-2.5 text-xs text-red-700">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <p>{formError}</p>
            </div>
          )}

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-800">
              Source Order <span className="text-rose-500">*</span>
            </label>
            <select
              required
              value={formOrderId}
              onChange={(e) => setFormOrderId(e.target.value)}
              className="w-full rounded-lg border border-border bg-white px-3 py-2 text-xs outline-none focus:border-primary transition"
            >
              <option value="">Select order...</option>
              {orders?.map((ord) => (
                <option key={ord.id} value={ord.id}>
                  {ord.order_number} ({ord.status}) - {formatCurrency(ord.total)}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-800">
              Payment Due Date
            </label>
            <input
              type="date"
              value={formDueDate}
              onChange={(e) => setFormDueDate(e.target.value)}
              className="w-full rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary transition"
            />
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-800">
              Invoice Notes / Terms
            </label>
            <textarea
              rows={2}
              value={formNotes}
              onChange={(e) => setFormNotes(e.target.value)}
              placeholder="Payment terms, bank details, or terms of service..."
              className="w-full rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary transition"
            />
          </div>

          <div className="flex items-center justify-end gap-2 border-t border-border pt-4">
            <button
              type="button"
              onClick={() => setIsCreateModalOpen(false)}
              className="rounded-lg border border-border px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-xs font-semibold text-white shadow-sm transition hover:opacity-90 disabled:opacity-50"
            >
              {createMutation.isPending && (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              )}
              Create Invoice
            </button>
          </div>
        </form>
      </Modal>

      {/* Invoice Detail Modal */}
      <Modal
        isOpen={!!selectedInvoiceForDetail}
        onClose={() => setSelectedInvoiceForDetail(null)}
        title={`Tax Invoice - ${activeInvoiceDetail?.invoice_number || selectedInvoiceForDetail?.invoice_number}`}
        description="Formal billing document details."
        maxWidth="xl"
      >
        <div className="space-y-4 text-xs">
          {/* Header Bar */}
          <div className="flex items-center justify-between border-b border-border pb-3">
            <div>
              <p className="text-slate-400">Customer</p>
              <p className="text-sm font-bold text-slate-900">
                {activeInvoiceDetail?.customer_id
                  ? customerMap.get(activeInvoiceDetail.customer_id) || "Customer"
                  : "Walk-in Customer"}
              </p>
            </div>
            <div className="text-right">
              <p className="text-slate-400">Status</p>
              <StatusBadge status={activeInvoiceDetail?.status || "DRAFT"} />
            </div>
          </div>

          {/* Line items table */}
          <div>
            <p className="mb-2 font-bold text-slate-800">Invoice Items</p>
            <div className="rounded-lg border border-border overflow-hidden">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="bg-slate-50 border-b border-border text-slate-500">
                    <th className="py-2 px-3">Description</th>
                    <th className="py-2 px-3 text-right">Qty</th>
                    <th className="py-2 px-3 text-right">Unit Price</th>
                    <th className="py-2 px-3 text-right">Tax</th>
                    <th className="py-2 px-3 text-right">Line Total</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {activeInvoiceDetail?.line_items?.map((item) => (
                    <tr key={item.id}>
                      <td className="py-2 px-3 font-semibold text-slate-900">
                        {item.description}
                      </td>
                      <td className="py-2 px-3 text-right font-mono">
                        {formatNumber(Number(item.quantity))}
                      </td>
                      <td className="py-2 px-3 text-right font-mono">
                        {formatCurrency(item.unit_price)}
                      </td>
                      <td className="py-2 px-3 text-right font-mono text-slate-500">
                        {formatCurrency(item.tax)}
                      </td>
                      <td className="py-2 px-3 text-right font-mono font-bold text-slate-950">
                        {formatCurrency(item.line_total)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Financial Breakdown */}
          <div className="flex justify-end">
            <div className="w-64 space-y-1 rounded-lg border border-border bg-slate-50 p-3 font-mono">
              <div className="flex justify-between text-slate-600">
                <span>Subtotal:</span>
                <span>{formatCurrency(activeInvoiceDetail?.subtotal || 0)}</span>
              </div>
              <div className="flex justify-between text-slate-600">
                <span>Tax Total:</span>
                <span>+{formatCurrency(activeInvoiceDetail?.tax_total || 0)}</span>
              </div>
              <div className="flex justify-between text-slate-600">
                <span>Discount:</span>
                <span>-{formatCurrency(activeInvoiceDetail?.discount_total || 0)}</span>
              </div>
              <div className="flex justify-between border-t border-slate-200 pt-1 font-bold text-slate-950 text-sm">
                <span>Invoice Total:</span>
                <span>{formatCurrency(activeInvoiceDetail?.total || 0)}</span>
              </div>
              <div className="flex justify-between text-emerald-700 font-bold">
                <span>Paid Amount:</span>
                <span>{formatCurrency(activeInvoiceDetail?.amount_paid || 0)}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between border-t border-border pt-4">
            <button
              type="button"
              onClick={() => window.print()}
              className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition"
            >
              <Printer className="h-3.5 w-3.5" />
              Print / Save PDF
            </button>
            <button
              type="button"
              onClick={() => setSelectedInvoiceForDetail(null)}
              className="rounded-lg border border-border px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition"
            >
              Close
            </button>
          </div>
        </div>
      </Modal>

      {/* Record Payment Modal */}
      <Modal
        isOpen={!!selectedInvoiceForPayment}
        onClose={() => setSelectedInvoiceForPayment(null)}
        title={`Record Payment - ${selectedInvoiceForPayment?.invoice_number}`}
        description="Register a payment against this invoice."
      >
        <form onSubmit={handleSubmitPayment} className="space-y-4">
          {paymentError && (
            <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-2.5 text-xs text-red-700">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <p>{paymentError}</p>
            </div>
          )}

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-800">
              Payment Amount (Rs.) <span className="text-rose-500">*</span>
            </label>
            <input
              type="number"
              step="0.01"
              min="0.01"
              required
              value={paymentAmount}
              onChange={(e) => setPaymentAmount(e.target.value)}
              placeholder={`Total bill: ${selectedInvoiceForPayment?.total}`}
              className="w-full rounded-lg border border-border px-3 py-2 text-xs font-mono outline-none focus:border-primary transition"
            />
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-800">
              Payment Method <span className="text-rose-500">*</span>
            </label>
            <select
              value={paymentMethod}
              onChange={(e) => setPaymentMethod(e.target.value)}
              className="w-full rounded-lg border border-border bg-white px-3 py-2 text-xs outline-none focus:border-primary transition"
            >
              <option value="CASH">Cash</option>
              <option value="CARD">Debit / Credit Card</option>
              <option value="BANK_TRANSFER">Bank Transfer</option>
              <option value="CHEQUE">Cheque</option>
              <option value="ONLINE">Online Gateway</option>
            </select>
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-800">
              Payment Reference / Cheque #
            </label>
            <input
              type="text"
              value={paymentReference}
              onChange={(e) => setPaymentReference(e.target.value)}
              placeholder="e.g. TRX-998811"
              className="w-full rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary transition"
            />
          </div>

          <div className="flex items-center justify-end gap-2 border-t border-border pt-4">
            <button
              type="button"
              onClick={() => setSelectedInvoiceForPayment(null)}
              className="rounded-lg border border-border px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={paymentMutation.isPending}
              className="flex items-center gap-1.5 rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white shadow-sm transition hover:bg-emerald-700 disabled:opacity-50"
            >
              {paymentMutation.isPending && (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              )}
              Confirm Payment
            </button>
          </div>
        </form>
      </Modal>

      {/* Confirmation Dialogs for Invoice Actions */}
      <ConfirmDialog
        isOpen={!!confirmActionInvoice}
        onClose={() => setConfirmActionInvoice(null)}
        onConfirm={() => {
          if (!confirmActionInvoice) return;
          if (confirmActionInvoice.action === "issue") {
            issueMutation.mutate(confirmActionInvoice.invoice.id);
          } else if (confirmActionInvoice.action === "void") {
            voidMutation.mutate(confirmActionInvoice.invoice.id);
          }
        }}
        title={
          confirmActionInvoice?.action === "issue"
            ? "Issue Invoice"
            : "Void Invoice"
        }
        message={
          confirmActionInvoice?.action === "issue"
            ? `Issue invoice "${confirmActionInvoice.invoice.invoice_number}" to customer? Issued invoices lock billing totals.`
            : `Void invoice "${confirmActionInvoice?.invoice.invoice_number}"? Voided invoices cannot accept payments.`
        }
        confirmText={
          confirmActionInvoice?.action === "issue" ? "Issue" : "Void Invoice"
        }
        variant={confirmActionInvoice?.action === "void" ? "danger" : "primary"}
        isLoading={issueMutation.isPending || voidMutation.isPending}
      />
    </AppShell>
  );
}
