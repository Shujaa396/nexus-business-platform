"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertCircle,
  Banknote,
  CheckCircle,
  Download,
  Eye,
  FileCheck2,
  FilePlus,
  Filter,
  Loader2,
  Package,
  Plus,
  RefreshCw,
  Search,
  ShoppingCart,
  Trash2,
  XCircle,
} from "lucide-react";

import AppShell from "../../components/app-shell";
import { formatCurrency, formatNumber } from "../../components/dashboard/stat-card";
import { StatusBadge } from "../../components/ui/badge";
import { BulkActionBar } from "../../components/ui/bulk-action-bar";
import { ConfirmDialog } from "../../components/ui/confirm-dialog";
import { Modal } from "../../components/ui/modal";
import {
  EmptyStateView,
  ErrorStateView,
  LoadingSpinner,
} from "../../components/ui/state-views";
import { exportToCSV } from "../../lib/export";
import { listBranches } from "../../lib/branches";
import { listCustomers } from "../../lib/customers";
import { createInvoice } from "../../lib/invoices";
import {
  addOrderPayment,
  cancelOrder,
  completeOrder,
  confirmOrder,
  createOrder,
  getOrderDetail,
  getOrderPayments,
  listOrders,
} from "../../lib/orders";
import { listProducts } from "../../lib/products";
import type {
  Order,
  OrderCreate,
  OrderItemCreate,
  PaymentCreate,
} from "../../types/orders";

export default function OrdersPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [searchOrderNumber, setSearchOrderNumber] = useState("");
  const [selectedStatus, setSelectedStatus] = useState<string>("");
  const [selectedPaymentStatus, setSelectedPaymentStatus] = useState<string>("");
  const [selectedOrderIds, setSelectedOrderIds] = useState<string[]>([]);

  // Modals
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [selectedOrderForDetail, setSelectedOrderForDetail] = useState<Order | null>(null);
  const [selectedOrderForPayment, setSelectedOrderForPayment] = useState<Order | null>(null);
  const [confirmActionOrder, setConfirmActionOrder] = useState<{
    order: Order;
    action: "confirm" | "complete" | "cancel" | "invoice";
  } | null>(null);

  // Order Create Form State
  const [formBranchId, setFormBranchId] = useState("");
  const [formCustomerId, setFormCustomerId] = useState("");
  const [formNotes, setFormNotes] = useState("");
  const [formItems, setFormItems] = useState<
    Array<{
      product_id: string;
      quantity: number;
      unit_price: number;
    }>
  >([]);
  const [formError, setFormError] = useState("");

  // Payment Form State
  const [paymentAmount, setPaymentAmount] = useState("");
  const [paymentMethod, setPaymentMethod] = useState("CASH");
  const [paymentReference, setPaymentReference] = useState("");
  const [paymentError, setPaymentError] = useState("");

  // Queries
  const {
    data: orders,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ["orders", searchOrderNumber, selectedStatus, selectedPaymentStatus],
    queryFn: () =>
      listOrders({
        order_number: searchOrderNumber || undefined,
        status: selectedStatus || undefined,
        payment_status: selectedPaymentStatus || undefined,
      }),
  });

  const { data: branches } = useQuery({
    queryKey: ["branches"],
    queryFn: () => listBranches(),
  });

  const { data: customers } = useQuery({
    queryKey: ["customers"],
    queryFn: () => listCustomers({ page_size: 100 }),
  });

  const { data: products } = useQuery({
    queryKey: ["products"],
    queryFn: () => listProducts({ page_size: 100 }),
  });

  // Query detail for active selected order
  const { data: activeOrderDetail } = useQuery({
    queryKey: ["order-detail", selectedOrderForDetail?.id],
    queryFn: () =>
      selectedOrderForDetail ? getOrderDetail(selectedOrderForDetail.id) : null,
    enabled: !!selectedOrderForDetail,
  });

  const { data: activeOrderPayments } = useQuery({
    queryKey: ["order-payments", selectedOrderForDetail?.id],
    queryFn: () =>
      selectedOrderForDetail ? getOrderPayments(selectedOrderForDetail.id) : [],
    enabled: !!selectedOrderForDetail,
  });

  // Mutations
  const createOrderMutation = useMutation({
    mutationFn: (data: OrderCreate) => createOrder(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
      queryClient.invalidateQueries({ queryKey: ["sales-analytics"] });
      setIsCreateModalOpen(false);
      resetCreateForm();
    },
    onError: (err: Error) => {
      setFormError(err.message || "Failed to create order.");
    },
  });

  const confirmMutation = useMutation({
    mutationFn: (orderId: string) => confirmOrder(orderId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      queryClient.invalidateQueries({ queryKey: ["inventory"] });
      setConfirmActionOrder(null);
      if (selectedOrderForDetail) {
        queryClient.invalidateQueries({
          queryKey: ["order-detail", selectedOrderForDetail.id],
        });
      }
    },
  });

  const completeMutation = useMutation({
    mutationFn: (orderId: string) => completeOrder(orderId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
      setConfirmActionOrder(null);
      if (selectedOrderForDetail) {
        queryClient.invalidateQueries({
          queryKey: ["order-detail", selectedOrderForDetail.id],
        });
      }
    },
  });

  const cancelMutation = useMutation({
    mutationFn: (orderId: string) => cancelOrder(orderId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      queryClient.invalidateQueries({ queryKey: ["inventory"] });
      setConfirmActionOrder(null);
      if (selectedOrderForDetail) {
        queryClient.invalidateQueries({
          queryKey: ["order-detail", selectedOrderForDetail.id],
        });
      }
    },
  });

  const paymentMutation = useMutation({
    mutationFn: ({
      orderId,
      data,
    }: {
      orderId: string;
      data: PaymentCreate;
    }) => addOrderPayment(orderId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      queryClient.invalidateQueries({ queryKey: ["payments"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
      if (selectedOrderForDetail) {
        queryClient.invalidateQueries({
          queryKey: ["order-detail", selectedOrderForDetail.id],
        });
        queryClient.invalidateQueries({
          queryKey: ["order-payments", selectedOrderForDetail.id],
        });
      }
      setSelectedOrderForPayment(null);
      setPaymentAmount("");
      setPaymentReference("");
    },
    onError: (err: Error) => {
      setPaymentError(err.message || "Failed to record payment.");
    },
  });

  const invoiceMutation = useMutation({
    mutationFn: (orderId: string) => createInvoice({ order_id: orderId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["invoices"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
      setConfirmActionOrder(null);
      router.push("/invoices");
    },
  });

  const resetCreateForm = () => {
    setFormBranchId(branches?.[0]?.id || "");
    setFormCustomerId("");
    setFormNotes("");
    setFormItems([]);
    setFormError("");
  };

  const handleOpenCreate = () => {
    resetCreateForm();
    if (products && products.length > 0) {
      setFormItems([
        {
          product_id: products[0].id,
          quantity: 1,
          unit_price: Number(products[0].selling_price),
        },
      ]);
    }
    setIsCreateModalOpen(true);
  };

  const handleAddItemRow = () => {
    if (products && products.length > 0) {
      setFormItems((prev) => [
        ...prev,
        {
          product_id: products[0].id,
          quantity: 1,
          unit_price: Number(products[0].selling_price),
        },
      ]);
    }
  };

  const handleRemoveItemRow = (index: number) => {
    setFormItems((prev) => prev.filter((_, idx) => idx !== index));
  };

  const handleItemChange = (
    index: number,
    field: "product_id" | "quantity" | "unit_price",
    value: string | number,
  ) => {
    setFormItems((prev) => {
      const updated = [...prev];
      if (field === "product_id") {
        const prod = products?.find((p) => p.id === value);
        updated[index] = {
          ...updated[index],
          product_id: value as string,
          unit_price: prod ? Number(prod.selling_price) : updated[index].unit_price,
        };
      } else {
        updated[index] = {
          ...updated[index],
          [field]: Number(value),
        };
      }
      return updated;
    });
  };

  const handleSubmitCreateOrder = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError("");

    if (!formBranchId) {
      setFormError("Please select a branch.");
      return;
    }
    if (formItems.length === 0) {
      setFormError("Order must contain at least one item.");
      return;
    }

    const payloadItems: OrderItemCreate[] = formItems.map((it) => ({
      product_id: it.product_id,
      quantity: Number(it.quantity),
      unit_price: Number(it.unit_price),
    }));

    createOrderMutation.mutate({
      branch_id: formBranchId,
      customer_id: formCustomerId || undefined,
      items: payloadItems,
      notes: formNotes || undefined,
    });
  };

  const handleSubmitPayment = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedOrderForPayment) return;
    setPaymentError("");

    const amt = parseFloat(paymentAmount);
    if (isNaN(amt) || amt <= 0) {
      setPaymentError("Payment amount must be greater than 0.");
      return;
    }

    paymentMutation.mutate({
      orderId: selectedOrderForPayment.id,
      data: {
        amount: amt,
        payment_method: paymentMethod,
        reference: paymentReference || undefined,
      },
    });
  };

  const branchMap = new Map(branches?.map((b) => [b.id, b.name]) || []);
  const customerMap = new Map(customers?.map((c) => [c.id, c.name]) || []);
  const productMap = new Map(products?.map((p) => [p.id, p]) || []);

  const formEstimatedTotal = formItems.reduce(
    (acc, it) => acc + Number(it.quantity || 0) * Number(it.unit_price || 0),
    0,
  );

  const handleSelectAllOrders = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.checked && orders) {
      setSelectedOrderIds(orders.map((o) => o.id));
    } else {
      setSelectedOrderIds([]);
    }
  };

  const handleToggleSelectOrder = (id: string) => {
    setSelectedOrderIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id],
    );
  };

  const handleExportAllOrders = () => {
    if (!orders || orders.length === 0) return;
    exportToCSV(
      "orders_registry",
      orders.map((o) => ({
        OrderNumber: o.order_number,
        Customer: o.customer_id ? customerMap.get(o.customer_id) || "Customer" : "Walk-in",
        Branch: branchMap.get(o.branch_id) || "Branch",
        Subtotal: o.subtotal,
        Discount: o.discount_total,
        Tax: o.tax_total,
        Total: o.total,
        OrderStatus: o.status,
        PaymentStatus: o.payment_status,
        Date: new Date(o.created_at).toISOString().split("T")[0],
      })),
    );
  };

  const handleExportSelectedOrders = () => {
    const selected = orders?.filter((o) => selectedOrderIds.includes(o.id));
    if (!selected || selected.length === 0) return;
    exportToCSV(
      "selected_orders",
      selected.map((o) => ({
        OrderNumber: o.order_number,
        Customer: o.customer_id ? customerMap.get(o.customer_id) || "Customer" : "Walk-in",
        Branch: branchMap.get(o.branch_id) || "Branch",
        Subtotal: o.subtotal,
        Discount: o.discount_total,
        Tax: o.tax_total,
        Total: o.total,
        OrderStatus: o.status,
        PaymentStatus: o.payment_status,
        Date: new Date(o.created_at).toISOString().split("T")[0],
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
              Sales & Fulfillment
            </p>
            <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-950 sm:text-3xl">
              Orders
            </h1>
            <p className="mt-1 text-xs text-slate-500">
              Process customer orders, lifecycle statuses, payments, and invoice creation.
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
              onClick={handleExportAllOrders}
              disabled={!orders || orders.length === 0}
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
              Create Order
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between rounded-xl border border-border bg-white p-4 shadow-sm">
          <div className="relative flex-1 max-w-xs">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              type="search"
              value={searchOrderNumber}
              onChange={(e) => setSearchOrderNumber(e.target.value)}
              placeholder="Search by order number..."
              className="w-full rounded-lg border border-border bg-slate-50 py-2 pl-9 pr-3 text-xs outline-none focus:border-primary focus:bg-white transition"
            />
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-1.5">
              <Filter className="h-4 w-4 text-slate-400" />
              <select
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
                className="rounded-lg border border-border bg-white px-3 py-2 text-xs text-slate-700 outline-none focus:border-primary transition"
              >
                <option value="">All Statuses</option>
                <option value="DRAFT">DRAFT</option>
                <option value="CONFIRMED">CONFIRMED</option>
                <option value="COMPLETED">COMPLETED</option>
                <option value="CANCELLED">CANCELLED</option>
              </select>
            </div>

            <select
              value={selectedPaymentStatus}
              onChange={(e) => setSelectedPaymentStatus(e.target.value)}
              className="rounded-lg border border-border bg-white px-3 py-2 text-xs text-slate-700 outline-none focus:border-primary transition"
            >
              <option value="">All Payment Statuses</option>
              <option value="UNPAID">UNPAID</option>
              <option value="PARTIAL">PARTIAL</option>
              <option value="PAID">PAID</option>
            </select>
          </div>
        </div>

        {/* Orders Table */}
        <div className="rounded-xl border border-border bg-white shadow-sm overflow-hidden">
          {isLoading ? (
            <div className="flex h-64 items-center justify-center">
              <LoadingSpinner message="Loading orders registry..." />
            </div>
          ) : isError ? (
            <div className="p-8">
              <ErrorStateView
                message={
                  error instanceof Error
                    ? error.message
                    : "Unable to load orders."
                }
                onRetry={() => refetch()}
              />
            </div>
          ) : !orders || orders.length === 0 ? (
            <div className="p-8">
              <EmptyStateView
                title="No orders found"
                message={
                  searchOrderNumber || selectedStatus || selectedPaymentStatus
                    ? "No orders matched your filters."
                    : "No orders created yet. Click 'Create Order' to start sales processing."
                }
              />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-border bg-slate-50 text-slate-500">
                    <th className="py-3.5 pl-4 pr-2 w-8">
                      <input
                        type="checkbox"
                        checked={
                          selectedOrderIds.length === orders.length &&
                          orders.length > 0
                        }
                        onChange={handleSelectAllOrders}
                        className="rounded border-border text-primary focus:ring-primary h-3.5 w-3.5"
                      />
                    </th>
                    <th className="py-3.5 px-3 font-semibold">Order Number</th>
                    <th className="py-3.5 px-3 font-semibold">Customer</th>
                    <th className="py-3.5 px-3 font-semibold">Branch</th>
                    <th className="py-3.5 px-3 text-right font-semibold">Total Amount</th>
                    <th className="py-3.5 px-3 text-center font-semibold">Order Status</th>
                    <th className="py-3.5 px-3 text-center font-semibold">Payment Status</th>
                    <th className="py-3.5 px-3 font-semibold">Date</th>
                    <th className="py-3.5 pl-3 pr-6 text-right font-semibold">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {orders.map((order) => {
                    const isChecked = selectedOrderIds.includes(order.id);
                    const custName = order.customer_id
                      ? customerMap.get(order.customer_id) || "Customer"
                      : "Walk-in Customer";
                    const branchName = branchMap.get(order.branch_id) || "Branch";

                    return (
                      <tr
                        key={order.id}
                        className={`transition ${
                          isChecked ? "bg-teal-50/40" : "hover:bg-slate-50"
                        }`}
                      >
                        <td className="py-3.5 pl-4 pr-2">
                          <input
                            type="checkbox"
                            checked={isChecked}
                            onChange={() => handleToggleSelectOrder(order.id)}
                            className="rounded border-border text-primary focus:ring-primary h-3.5 w-3.5"
                          />
                        </td>
                        <td className="py-3.5 px-3 font-mono font-bold text-slate-900">
                          <div className="flex items-center gap-2">
                            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-teal-50 text-teal-700">
                              <ShoppingCart className="h-3.5 w-3.5" />
                            </div>
                            <span>{order.order_number}</span>
                          </div>
                        </td>
                        <td className="py-3.5 px-3 font-semibold text-slate-800">
                          {custName}
                        </td>
                        <td className="py-3.5 px-3 text-slate-600">
                          {branchName}
                        </td>
                        <td className="py-3.5 px-3 text-right font-bold text-slate-950">
                          {formatCurrency(order.total)}
                        </td>
                        <td className="py-3.5 px-3 text-center">
                          <StatusBadge status={order.status} />
                        </td>
                        <td className="py-3.5 px-3 text-center">
                          <StatusBadge status={order.payment_status} />
                        </td>
                        <td className="py-3.5 px-3 text-slate-500 font-mono text-[11px]">
                          {new Date(order.created_at).toLocaleDateString()}
                        </td>
                        <td className="py-3.5 pl-3 pr-6 text-right">
                          <div className="flex items-center justify-end gap-1.5">
                            <button
                              type="button"
                              onClick={() => setSelectedOrderForDetail(order)}
                              className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-900 transition"
                              title="View Order Details"
                            >
                              <Eye className="h-3.5 w-3.5" />
                            </button>
                            {order.status === "DRAFT" && (
                              <button
                                type="button"
                                onClick={() =>
                                  setConfirmActionOrder({ order, action: "confirm" })
                                }
                                className="rounded-lg p-1.5 text-blue-600 hover:bg-blue-50 transition"
                                title="Confirm Order"
                              >
                                <CheckCircle className="h-3.5 w-3.5" />
                              </button>
                            )}
                            {order.status === "CONFIRMED" && (
                              <>
                                <button
                                  type="button"
                                  onClick={() => {
                                    setSelectedOrderForPayment(order);
                                    setPaymentAmount(order.total.toString());
                                  }}
                                  className="rounded-lg p-1.5 text-emerald-600 hover:bg-emerald-50 transition"
                                  title="Record Payment"
                                >
                                  <Banknote className="h-3.5 w-3.5" />
                                </button>
                                <button
                                  type="button"
                                  onClick={() =>
                                    setConfirmActionOrder({ order, action: "invoice" })
                                  }
                                  className="rounded-lg p-1.5 text-purple-600 hover:bg-purple-50 transition"
                                  title="Generate Invoice"
                                >
                                  <FilePlus className="h-3.5 w-3.5" />
                                </button>
                                <button
                                  type="button"
                                  onClick={() =>
                                    setConfirmActionOrder({ order, action: "complete" })
                                  }
                                  className="rounded-lg p-1.5 text-teal-600 hover:bg-teal-50 transition"
                                  title="Complete Order"
                                >
                                  <FileCheck2 className="h-3.5 w-3.5" />
                                </button>
                              </>
                            )}
                            {(order.status === "DRAFT" || order.status === "CONFIRMED") && (
                              <button
                                type="button"
                                onClick={() =>
                                  setConfirmActionOrder({ order, action: "cancel" })
                                }
                                className="rounded-lg p-1.5 text-rose-500 hover:bg-rose-50 transition"
                                title="Cancel Order"
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

      {/* Floating Bulk Action Bar */}
      <BulkActionBar
        selectedCount={selectedOrderIds.length}
        onClear={() => setSelectedOrderIds([])}
        onBulkExport={handleExportSelectedOrders}
        resourceName="orders"
      />

      {/* Create Order Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Create New Sales Order"
        description="Select branch, customer, and line items."
        maxWidth="2xl"
      >
        <form onSubmit={handleSubmitCreateOrder} className="space-y-4">
          {formError && (
            <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-2.5 text-xs text-red-700">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <p>{formError}</p>
            </div>
          )}

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-800">
                Fulfillment Branch <span className="text-rose-500">*</span>
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
                Customer (Optional)
              </label>
              <select
                value={formCustomerId}
                onChange={(e) => setFormCustomerId(e.target.value)}
                className="w-full rounded-lg border border-border bg-white px-3 py-2 text-xs outline-none focus:border-primary transition"
              >
                <option value="">Walk-in Customer</option>
                {customers?.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} {c.phone ? `(${c.phone})` : ""}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Line Items */}
          <div className="space-y-2 border-t border-border pt-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold uppercase tracking-wider text-slate-700">
                Order Line Items
              </label>
              <button
                type="button"
                onClick={handleAddItemRow}
                className="inline-flex items-center gap-1 text-xs font-semibold text-primary hover:underline"
              >
                <Plus className="h-3.5 w-3.5" />
                Add Item
              </button>
            </div>

            <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
              {formItems.map((item, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 p-2 text-xs"
                >
                  <div className="flex-1">
                    <select
                      value={item.product_id}
                      onChange={(e) =>
                        handleItemChange(idx, "product_id", e.target.value)
                      }
                      className="w-full rounded border border-border bg-white p-1.5 text-xs outline-none focus:border-primary"
                    >
                      {products?.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.name} ({p.sku}) - {formatCurrency(p.selling_price)}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="w-20">
                    <input
                      type="number"
                      min="1"
                      value={item.quantity}
                      onChange={(e) =>
                        handleItemChange(idx, "quantity", e.target.value)
                      }
                      placeholder="Qty"
                      className="w-full rounded border border-border bg-white p-1.5 text-xs text-center outline-none focus:border-primary"
                    />
                  </div>

                  <div className="w-24 text-right font-mono font-bold text-slate-800">
                    {formatCurrency(item.quantity * item.unit_price)}
                  </div>

                  <button
                    type="button"
                    onClick={() => handleRemoveItemRow(idx)}
                    className="rounded p-1 text-slate-400 hover:bg-rose-50 hover:text-rose-600 transition"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              ))}
            </div>

            <div className="flex items-center justify-between border-t border-slate-200 pt-2 text-xs font-bold text-slate-950">
              <span>Estimated Subtotal:</span>
              <span className="font-mono text-sm">
                {formatCurrency(formEstimatedTotal)}
              </span>
            </div>
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-800">
              Order Notes / Instructions
            </label>
            <textarea
              rows={2}
              value={formNotes}
              onChange={(e) => setFormNotes(e.target.value)}
              placeholder="Delivery instructions, customer PO reference..."
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
              disabled={createOrderMutation.isPending}
              className="flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-xs font-semibold text-white shadow-sm transition hover:opacity-90 disabled:opacity-50"
            >
              {createOrderMutation.isPending && (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              )}
              Create Order
            </button>
          </div>
        </form>
      </Modal>

      {/* Order Detail Modal */}
      <Modal
        isOpen={!!selectedOrderForDetail}
        onClose={() => setSelectedOrderForDetail(null)}
        title={`Order Details - ${activeOrderDetail?.order_number || selectedOrderForDetail?.order_number}`}
        description="Comprehensive summary of line items, financial totals, and transaction audit."
        maxWidth="xl"
      >
        <div className="space-y-4 text-xs">
          {/* Top Info */}
          <div className="grid grid-cols-2 gap-3 rounded-lg border border-border bg-slate-50 p-3">
            <div>
              <p className="text-slate-400">Customer</p>
              <p className="font-bold text-slate-900">
                {activeOrderDetail?.customer_id
                  ? customerMap.get(activeOrderDetail.customer_id) || "Customer"
                  : "Walk-in Customer"}
              </p>
            </div>
            <div>
              <p className="text-slate-400">Branch</p>
              <p className="font-bold text-slate-900">
                {activeOrderDetail?.branch_id
                  ? branchMap.get(activeOrderDetail.branch_id) || "Branch"
                  : "—"}
              </p>
            </div>
            <div>
              <p className="text-slate-400">Order Status</p>
              <StatusBadge status={activeOrderDetail?.status || "DRAFT"} />
            </div>
            <div>
              <p className="text-slate-400">Payment Status</p>
              <StatusBadge
                status={activeOrderDetail?.payment_status || "UNPAID"}
              />
            </div>
          </div>

          {/* Line items table */}
          <div>
            <p className="mb-2 font-bold text-slate-800">Items Ordered</p>
            <div className="rounded-lg border border-border overflow-hidden">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="bg-slate-50 border-b border-border text-slate-500">
                    <th className="py-2 px-3">Product</th>
                    <th className="py-2 px-3 text-right">Qty</th>
                    <th className="py-2 px-3 text-right">Unit Price</th>
                    <th className="py-2 px-3 text-right">Line Total</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {activeOrderDetail?.items?.map((item) => {
                    const prod = productMap.get(item.product_id);
                    return (
                      <tr key={item.id}>
                        <td className="py-2 px-3 font-semibold text-slate-900">
                          {prod?.name || "Item"}
                        </td>
                        <td className="py-2 px-3 text-right font-mono">
                          {formatNumber(Number(item.quantity))}
                        </td>
                        <td className="py-2 px-3 text-right font-mono">
                          {formatCurrency(item.unit_price)}
                        </td>
                        <td className="py-2 px-3 text-right font-mono font-bold text-slate-950">
                          {formatCurrency(item.line_total)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Order Financials */}
          <div className="flex justify-end">
            <div className="w-64 space-y-1 rounded-lg border border-border bg-slate-50 p-3 font-mono">
              <div className="flex justify-between text-slate-600">
                <span>Subtotal:</span>
                <span>{formatCurrency(activeOrderDetail?.subtotal || 0)}</span>
              </div>
              <div className="flex justify-between text-slate-600">
                <span>Discount:</span>
                <span>-{formatCurrency(activeOrderDetail?.discount_total || 0)}</span>
              </div>
              <div className="flex justify-between text-slate-600">
                <span>Tax:</span>
                <span>+{formatCurrency(activeOrderDetail?.tax_total || 0)}</span>
              </div>
              <div className="flex justify-between border-t border-slate-200 pt-1 font-bold text-slate-950 text-sm">
                <span>Total:</span>
                <span>{formatCurrency(activeOrderDetail?.total || 0)}</span>
              </div>
            </div>
          </div>

          {/* Payments list for this order */}
          {activeOrderPayments && activeOrderPayments.length > 0 && (
            <div className="border-t border-border pt-3">
              <p className="mb-2 font-bold text-slate-800">Recorded Payments</p>
              <div className="space-y-1.5">
                {activeOrderPayments.map((p) => (
                  <div
                    key={p.id}
                    className="flex items-center justify-between rounded-lg border border-emerald-200 bg-emerald-50/50 p-2 text-xs"
                  >
                    <div className="flex items-center gap-2">
                      <Banknote className="h-3.5 w-3.5 text-emerald-600" />
                      <span className="font-semibold text-slate-800">
                        {p.payment_method}
                      </span>
                      {p.reference && (
                        <span className="text-[10px] text-slate-400 font-mono">
                          Ref: {p.reference}
                        </span>
                      )}
                    </div>
                    <span className="font-mono font-bold text-emerald-700">
                      {formatCurrency(p.amount)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex justify-end border-t border-border pt-4">
            <button
              type="button"
              onClick={() => setSelectedOrderForDetail(null)}
              className="rounded-lg border border-border px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition"
            >
              Close
            </button>
          </div>
        </div>
      </Modal>

      {/* Record Payment Modal */}
      <Modal
        isOpen={!!selectedOrderForPayment}
        onClose={() => setSelectedOrderForPayment(null)}
        title={`Record Payment - ${selectedOrderForPayment?.order_number}`}
        description="Register customer payment against this sales order."
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
              placeholder={`Max total: ${selectedOrderForPayment?.total}`}
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
              Transaction Reference / Note
            </label>
            <input
              type="text"
              value={paymentReference}
              onChange={(e) => setPaymentReference(e.target.value)}
              placeholder="e.g. Bank slip #, POS receipt #"
              className="w-full rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary transition"
            />
          </div>

          <div className="flex items-center justify-end gap-2 border-t border-border pt-4">
            <button
              type="button"
              onClick={() => setSelectedOrderForPayment(null)}
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

      {/* Confirmation Dialogs for Order Actions */}
      <ConfirmDialog
        isOpen={!!confirmActionOrder}
        onClose={() => setConfirmActionOrder(null)}
        onConfirm={() => {
          if (!confirmActionOrder) return;
          if (confirmActionOrder.action === "confirm") {
            confirmMutation.mutate(confirmActionOrder.order.id);
          } else if (confirmActionOrder.action === "complete") {
            completeMutation.mutate(confirmActionOrder.order.id);
          } else if (confirmActionOrder.action === "cancel") {
            cancelMutation.mutate(confirmActionOrder.order.id);
          } else if (confirmActionOrder.action === "invoice") {
            invoiceMutation.mutate(confirmActionOrder.order.id);
          }
        }}
        title={
          confirmActionOrder?.action === "confirm"
            ? "Confirm Order"
            : confirmActionOrder?.action === "complete"
            ? "Complete Order"
            : confirmActionOrder?.action === "invoice"
            ? "Generate Invoice"
            : "Cancel Order"
        }
        message={
          confirmActionOrder?.action === "confirm"
            ? `Confirm order "${confirmActionOrder.order.order_number}"? This will reserve branch stock and progress the order.`
            : confirmActionOrder?.action === "complete"
            ? `Mark order "${confirmActionOrder.order.order_number}" as COMPLETED?`
            : confirmActionOrder?.action === "invoice"
            ? `Generate a formal tax invoice from order "${confirmActionOrder.order.order_number}"?`
            : `Cancel order "${confirmActionOrder?.order.order_number}"? Cancelled orders release any reserved inventory.`
        }
        confirmText={
          confirmActionOrder?.action === "confirm"
            ? "Confirm Order"
            : confirmActionOrder?.action === "complete"
            ? "Complete"
            : confirmActionOrder?.action === "invoice"
            ? "Create Invoice"
            : "Cancel Order"
        }
        variant={confirmActionOrder?.action === "cancel" ? "danger" : "primary"}
        isLoading={
          confirmMutation.isPending ||
          completeMutation.isPending ||
          cancelMutation.isPending ||
          invoiceMutation.isPending
        }
      />
    </AppShell>
  );
}
