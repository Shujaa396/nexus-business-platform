"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertCircle,
  Download,
  Edit2,
  Loader2,
  Mail,
  MapPin,
  Phone,
  Plus,
  RefreshCw,
  Search,
  Trash2,
  Users,
} from "lucide-react";

import AppShell from "../../components/app-shell";
import { StatusBadge } from "../../components/ui/badge";
import { BulkActionBar } from "../../components/ui/bulk-action-bar";
import { ConfirmDialog } from "../../components/ui/confirm-dialog";
import { Modal } from "../../components/ui/modal";
import {
  EmptyStateView,
  ErrorStateView,
  LoadingSpinner,
} from "../../components/ui/state-views";
import {
  createCustomer,
  deleteCustomer,
  listCustomersPage,
  updateCustomer,
} from "../../lib/customers";
import { exportToCSV } from "../../lib/export";
import type { Customer, CustomerCreate, CustomerUpdate } from "../../types/customers";

export default function CustomersPage() {
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [page, setPage] = useState(1);
  const [selectedCustomerIds, setSelectedCustomerIds] = useState<string[]>([]);

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingCustomer, setEditingCustomer] = useState<Customer | null>(null);
  const [deletingCustomer, setDeletingCustomer] = useState<Customer | null>(null);
  const [isBulkDeactivating, setIsBulkDeactivating] = useState(false);

  // Form states
  const [formName, setFormName] = useState("");
  const [formCode, setFormCode] = useState("");
  const [formCompany, setFormCompany] = useState("");
  const [formEmail, setFormEmail] = useState("");
  const [formPhone, setFormPhone] = useState("");
  const [formAddress, setFormAddress] = useState("");
  const [formNotes, setFormNotes] = useState("");
  const [formStatus, setFormStatus] = useState("ACTIVE");
  const [formCreditLimit, setFormCreditLimit] = useState("0");
  const [formDiscount, setFormDiscount] = useState("0");
  const [formBilling, setFormBilling] = useState("");
  const [formShipping, setFormShipping] = useState("");
  const [formError, setFormError] = useState("");

  // Queries
  const {
    data: customerPage,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ["customers", searchQuery, statusFilter, page],
    queryFn: () => listCustomersPage({ q: searchQuery || undefined, status: statusFilter || undefined, page }),
  });
  const customers = customerPage?.items;

  // Mutations
  const createMutation = useMutation({
    mutationFn: (data: CustomerCreate) => createCustomer(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["customers"] });
      queryClient.invalidateQueries({ queryKey: ["customer-analytics"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
      setIsCreateModalOpen(false);
      resetForm();
    },
    onError: (err: Error) => {
      setFormError(err.message || "Failed to create customer.");
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: CustomerUpdate }) =>
      updateCustomer(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["customers"] });
      queryClient.invalidateQueries({ queryKey: ["customer-analytics"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
      setEditingCustomer(null);
      resetForm();
    },
    onError: (err: Error) => {
      setFormError(err.message || "Failed to update customer.");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteCustomer(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["customers"] });
      queryClient.invalidateQueries({ queryKey: ["customer-analytics"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
      setDeletingCustomer(null);
    },
  });

  const resetForm = () => {
    setFormName("");
    setFormCode("");
    setFormCompany("");
    setFormEmail("");
    setFormPhone("");
    setFormAddress("");
    setFormNotes("");
    setFormStatus("ACTIVE");
    setFormCreditLimit("0");
    setFormDiscount("0");
    setFormBilling("");
    setFormShipping("");
    setFormError("");
  };

  const handleOpenCreate = () => {
    resetForm();
    setIsCreateModalOpen(true);
  };

  const handleOpenEdit = (c: Customer) => {
    resetForm();
    setEditingCustomer(c);
    setFormName(c.name);
    setFormCode(c.customer_code || "");
    setFormCompany(c.company_name || "");
    setFormEmail(c.email || "");
    setFormPhone(c.phone || "");
    setFormAddress(c.address || "");
    setFormNotes(c.notes || "");
    setFormStatus(c.status);
    setFormCreditLimit(c.credit_limit);
    setFormDiscount(c.discount_percent);
    setFormBilling(c.billing_address || "");
    setFormShipping(c.shipping_address || "");
  };

  const handleSubmitCreate = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError("");
    createMutation.mutate({
      name: formName.trim(),
      customer_code: formCode.trim() || undefined,
      company_name: formCompany.trim() || undefined,
      email: formEmail.trim() || undefined,
      phone: formPhone.trim() || undefined,
      address: formAddress.trim() || undefined,
      notes: formNotes.trim() || undefined,
      status: formStatus,
      credit_limit: formCreditLimit,
      discount_percent: formDiscount,
      billing_address: formBilling.trim() || undefined,
      shipping_address: formShipping.trim() || undefined,
    });
  };

  const handleSubmitEdit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingCustomer) return;
    setFormError("");
    updateMutation.mutate({
      id: editingCustomer.id,
      data: {
        name: formName.trim(),
        customer_code: formCode.trim() || undefined,
        company_name: formCompany.trim() || undefined,
        email: formEmail.trim() || undefined,
        phone: formPhone.trim() || undefined,
        address: formAddress.trim() || undefined,
        notes: formNotes.trim() || undefined,
        status: formStatus,
        credit_limit: formCreditLimit,
        discount_percent: formDiscount,
        billing_address: formBilling.trim() || undefined,
        shipping_address: formShipping.trim() || undefined,
      },
    });
  };

  // Selection handlers
  const handleSelectAll = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.checked && customers) {
      setSelectedCustomerIds(customers.map((c) => c.id));
    } else {
      setSelectedCustomerIds([]);
    }
  };

  const handleToggleSelect = (id: string) => {
    setSelectedCustomerIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id],
    );
  };

  const handleExportAll = () => {
    if (!customers || customers.length === 0) return;
    exportToCSV(
      "customers_directory",
      customers.map((c) => ({
        Name: c.name,
        Email: c.email || "",
        Phone: c.phone || "",
        Address: c.address || "",
        Notes: c.notes || "",
        Status: c.is_active ? "Active" : "Inactive",
      })),
    );
  };

  const handleExportSelected = () => {
    const selected = customers?.filter((c) => selectedCustomerIds.includes(c.id));
    if (!selected || selected.length === 0) return;
    exportToCSV(
      "selected_customers",
      selected.map((c) => ({
        Name: c.name,
        Email: c.email || "",
        Phone: c.phone || "",
        Address: c.address || "",
        Notes: c.notes || "",
        Status: c.is_active ? "Active" : "Inactive",
      })),
    );
  };

  const handleExecuteBulkDeactivate = async () => {
    for (const id of selectedCustomerIds) {
      try {
        await deleteCustomer(id);
      } catch {
        // Continue with remaining
      }
    }
    queryClient.invalidateQueries({ queryKey: ["customers"] });
    setSelectedCustomerIds([]);
    setIsBulkDeactivating(false);
  };

  return (
    <AppShell>
      <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8 space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-primary">
              Client Directory
            </p>
            <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-950 sm:text-3xl">
              Customers
            </h1>
            <p className="mt-1 text-xs text-slate-500">
              Manage enterprise clients, corporate billing details, contact information, and account history.
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
              onClick={handleExportAll}
              disabled={!customers || customers.length === 0}
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
              Add Customer
            </button>
          </div>
        </div>

        {/* Search */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between rounded-xl border border-border bg-white p-4 shadow-sm">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              type="search"
              value={searchQuery}
              onChange={(e) => { setSearchQuery(e.target.value); setPage(1); }}
              placeholder="Search by customer name, phone, or email..."
              className="w-full rounded-lg border border-border bg-slate-50 py-2 pl-9 pr-3 text-xs outline-none focus:border-primary focus:bg-white transition"
            />
          </div>
          <select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }} className="rounded-lg border border-border bg-slate-50 px-3 py-2 text-xs text-slate-700">
            <option value="">All statuses</option><option value="ACTIVE">Active</option><option value="PROSPECT">Prospect</option><option value="INACTIVE">Inactive</option><option value="BLOCKED">Blocked</option>
          </select>
        </div>

        {/* Customers Table Card */}
        <div className="rounded-xl border border-border bg-white shadow-sm overflow-hidden">
          {isLoading ? (
            <div className="flex h-64 items-center justify-center">
              <LoadingSpinner message="Loading customer directory..." />
            </div>
          ) : isError ? (
            <div className="p-8">
              <ErrorStateView
                message={
                  error instanceof Error
                    ? error.message
                    : "Unable to load customers."
                }
                onRetry={() => refetch()}
              />
            </div>
          ) : !customers || customers.length === 0 ? (
            <div className="p-8">
              <EmptyStateView
                title="No customers found"
                message={
                  searchQuery
                    ? "No customers matched your search query."
                    : "No customers in your directory. Click 'Add Customer' to create one."
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
                          selectedCustomerIds.length === customers.length &&
                          customers.length > 0
                        }
                        onChange={handleSelectAll}
                        className="rounded border-border text-primary focus:ring-primary h-3.5 w-3.5"
                      />
                    </th>
                    <th className="py-3.5 px-3 font-semibold">Customer Name</th>
                    <th className="py-3.5 px-3 font-semibold">Email Address</th>
                    <th className="py-3.5 px-3 font-semibold">Phone</th>
                    <th className="py-3.5 px-3 font-semibold">Address</th>
                    <th className="py-3.5 px-3 text-center font-semibold">Status</th>
                    <th className="py-3.5 pl-3 pr-6 text-right font-semibold">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {customers.map((customer) => {
                    const isChecked = selectedCustomerIds.includes(customer.id);
                    return (
                      <tr
                        key={customer.id}
                        className={`transition ${
                          isChecked ? "bg-teal-50/40" : "hover:bg-slate-50"
                        }`}
                      >
                        <td className="py-3.5 pl-4 pr-2">
                          <input
                            type="checkbox"
                            checked={isChecked}
                            onChange={() => handleToggleSelect(customer.id)}
                            className="rounded border-border text-primary focus:ring-primary h-3.5 w-3.5"
                          />
                        </td>
                        <td className="py-3.5 px-3 font-semibold text-slate-900">
                          <div className="flex items-center gap-2.5">
                            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-teal-50 text-teal-700 font-bold text-xs">
                              {customer.name.charAt(0).toUpperCase()}
                            </div>
                            <div>
                              <Link href={`/customers/${customer.id}`} className="font-semibold text-slate-900 hover:text-primary">{customer.name}</Link>
                              {customer.notes && (
                                <p className="text-[10px] text-slate-400 truncate max-w-xs">
                                  {customer.notes}
                                </p>
                              )}
                            </div>
                          </div>
                        </td>
                        <td className="py-3.5 px-3 text-slate-600 font-mono">
                          {customer.email ? (
                            <div className="flex items-center gap-1.5">
                              <Mail className="h-3 w-3 text-slate-400" />
                              <span>{customer.email}</span>
                            </div>
                          ) : (
                            "—"
                          )}
                        </td>
                        <td className="py-3.5 px-3 text-slate-600 font-mono">
                          {customer.phone ? (
                            <div className="flex items-center gap-1.5">
                              <Phone className="h-3 w-3 text-slate-400" />
                              <span>{customer.phone}</span>
                            </div>
                          ) : (
                            "—"
                          )}
                        </td>
                        <td className="py-3.5 px-3 text-slate-600 max-w-xs truncate">
                          {customer.address ? (
                            <div className="flex items-center gap-1.5 truncate">
                              <MapPin className="h-3 w-3 text-slate-400 shrink-0" />
                              <span className="truncate">{customer.address}</span>
                            </div>
                          ) : (
                            "—"
                          )}
                        </td>
                        <td className="py-3.5 px-3 text-center">
                          <StatusBadge
                            status={customer.is_active ? "ACTIVE" : "INACTIVE"}
                          />
                        </td>
                        <td className="py-3.5 pl-3 pr-6 text-right">
                          <div className="flex items-center justify-end gap-1.5">
                            <button
                              type="button"
                              onClick={() => handleOpenEdit(customer)}
                              className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition"
                              title="Edit customer"
                            >
                              <Edit2 className="h-3.5 w-3.5" />
                            </button>
                            {customer.is_active && (
                              <button
                                type="button"
                                onClick={() => setDeletingCustomer(customer)}
                                className="rounded-lg p-1.5 text-slate-400 hover:bg-rose-50 hover:text-rose-600 transition"
                                title="Deactivate customer"
                              >
                                <Trash2 className="h-3.5 w-3.5" />
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
        {customerPage && customerPage.total_pages > 0 && <div className="flex items-center justify-between text-xs text-slate-500"><span>Showing page {customerPage.page} of {customerPage.total_pages} ({customerPage.total} total)</span><div className="flex gap-2"><button type="button" disabled={!customerPage.has_previous} onClick={() => setPage((current) => current - 1)} className="rounded border border-border px-3 py-1.5 disabled:opacity-40">Previous</button><button type="button" disabled={!customerPage.has_next} onClick={() => setPage((current) => current + 1)} className="rounded border border-border px-3 py-1.5 disabled:opacity-40">Next</button></div></div>}
      </div>

      {/* Floating Bulk Action Bar */}
      <BulkActionBar
        selectedCount={selectedCustomerIds.length}
        onClear={() => setSelectedCustomerIds([])}
        onBulkExport={handleExportSelected}
        onBulkDeactivate={() => setIsBulkDeactivating(true)}
        resourceName="customers"
      />

      {/* Bulk Deactivate Confirmation */}
      <ConfirmDialog
        isOpen={isBulkDeactivating}
        onClose={() => setIsBulkDeactivating(false)}
        onConfirm={handleExecuteBulkDeactivate}
        title="Bulk Deactivate Customers"
        message={`Are you sure you want to deactivate ${selectedCustomerIds.length} selected customers?`}
        confirmText="Deactivate All"
        variant="danger"
      />

      {/* Create Customer Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Add Customer"
        description="Register a new commercial or retail customer profile."
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
              Customer / Business Name <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              required
              value={formName}
              onChange={(e) => setFormName(e.target.value)}
              placeholder="e.g. Apex Corporation"
              className="w-full rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary transition"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <input value={formCode} onChange={(e) => setFormCode(e.target.value)} placeholder="Customer code (optional)" className="rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary" />
            <input value={formCompany} onChange={(e) => setFormCompany(e.target.value)} placeholder="Company name" className="rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary" />
            <select value={formStatus} onChange={(e) => setFormStatus(e.target.value)} className="rounded-lg border border-border px-3 py-2 text-xs"><option value="ACTIVE">Active</option><option value="PROSPECT">Prospect</option><option value="INACTIVE">Inactive</option><option value="BLOCKED">Blocked</option></select>
            <input type="number" min="0" value={formCreditLimit} onChange={(e) => setFormCreditLimit(e.target.value)} placeholder="Credit limit" className="rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary" />
            <input type="number" min="0" max="100" step="0.01" value={formDiscount} onChange={(e) => setFormDiscount(e.target.value)} placeholder="Discount %" className="rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary" />
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-800">
              Email Address
            </label>
            <input
              type="email"
              value={formEmail}
              onChange={(e) => setFormEmail(e.target.value)}
              placeholder="billing@apexcorp.com"
              className="w-full rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary transition"
            />
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-800">
              Phone Number
            </label>
            <input
              type="tel"
              value={formPhone}
              onChange={(e) => setFormPhone(e.target.value)}
              placeholder="+92 300 1234567"
              className="w-full rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary transition"
            />
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-800">
              Billing Address
            </label>
            <textarea
              rows={2}
              value={formAddress}
              onChange={(e) => setFormAddress(e.target.value)}
              placeholder="Street address, city, country..."
              className="w-full rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary transition"
            />
          </div>
          <textarea rows={2} value={formShipping} onChange={(e) => setFormShipping(e.target.value)} placeholder="Shipping address" className="w-full rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary transition" />

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-800">
              Internal Notes
            </label>
            <textarea
              rows={2}
              value={formNotes}
              onChange={(e) => setFormNotes(e.target.value)}
              placeholder="Credit terms, tax exemptions, account notes..."
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
              Create Customer
            </button>
          </div>
        </form>
      </Modal>

      {/* Edit Customer Modal */}
      <Modal
        isOpen={!!editingCustomer}
        onClose={() => setEditingCustomer(null)}
        title="Edit Customer"
        description={`Update contact and billing details for ${editingCustomer?.name}`}
      >
        <form onSubmit={handleSubmitEdit} className="space-y-4">
          {formError && (
            <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-2.5 text-xs text-red-700">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <p>{formError}</p>
            </div>
          )}

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-800">
              Customer / Business Name <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              required
              value={formName}
              onChange={(e) => setFormName(e.target.value)}
              className="w-full rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary transition"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <input value={formCode} onChange={(e) => setFormCode(e.target.value)} placeholder="Customer code" className="rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary" />
            <input value={formCompany} onChange={(e) => setFormCompany(e.target.value)} placeholder="Company name" className="rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary" />
            <select value={formStatus} onChange={(e) => setFormStatus(e.target.value)} className="rounded-lg border border-border px-3 py-2 text-xs"><option value="ACTIVE">Active</option><option value="PROSPECT">Prospect</option><option value="INACTIVE">Inactive</option><option value="BLOCKED">Blocked</option></select>
            <input type="number" min="0" value={formCreditLimit} onChange={(e) => setFormCreditLimit(e.target.value)} placeholder="Credit limit" className="rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary" />
            <input type="number" min="0" max="100" step="0.01" value={formDiscount} onChange={(e) => setFormDiscount(e.target.value)} placeholder="Discount %" className="rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary" />
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-800">
              Email Address
            </label>
            <input
              type="email"
              value={formEmail}
              onChange={(e) => setFormEmail(e.target.value)}
              className="w-full rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary transition"
            />
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-800">
              Phone Number
            </label>
            <input
              type="tel"
              value={formPhone}
              onChange={(e) => setFormPhone(e.target.value)}
              className="w-full rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary transition"
            />
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-800">
              Billing Address
            </label>
            <textarea
              rows={2}
              value={formAddress}
              onChange={(e) => setFormAddress(e.target.value)}
              className="w-full rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary transition"
            />
          </div>
          <textarea rows={2} value={formShipping} onChange={(e) => setFormShipping(e.target.value)} placeholder="Shipping address" className="w-full rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary transition" />

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-800">
              Internal Notes
            </label>
            <textarea
              rows={2}
              value={formNotes}
              onChange={(e) => setFormNotes(e.target.value)}
              className="w-full rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary transition"
            />
          </div>

          <div className="flex items-center justify-end gap-2 border-t border-border pt-4">
            <button
              type="button"
              onClick={() => setEditingCustomer(null)}
              className="rounded-lg border border-border px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={updateMutation.isPending}
              className="flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-xs font-semibold text-white shadow-sm transition hover:opacity-90 disabled:opacity-50"
            >
              {updateMutation.isPending && (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              )}
              Save Changes
            </button>
          </div>
        </form>
      </Modal>

      {/* Deactivate Customer Confirmation */}
      <ConfirmDialog
        isOpen={!!deletingCustomer}
        onClose={() => setDeletingCustomer(null)}
        onConfirm={() => deletingCustomer && deleteMutation.mutate(deletingCustomer.id)}
        title="Deactivate Customer"
        message={`Are you sure you want to deactivate "${deletingCustomer?.name}"? You will not be able to issue new orders to this customer.`}
        confirmText="Deactivate"
        variant="danger"
        isLoading={deleteMutation.isPending}
      />
    </AppShell>
  );
}
