"use client";

import React, { useState } from "react";
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
  Truck,
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
  createSupplier,
  deleteSupplier,
  listSuppliers,
  updateSupplier,
} from "../../lib/suppliers";
import { exportToCSV } from "../../lib/export";
import type { Supplier, SupplierCreate, SupplierUpdate } from "../../types/suppliers";

export default function SuppliersPage() {
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedSupplierIds, setSelectedSupplierIds] = useState<string[]>([]);

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingSupplier, setEditingSupplier] = useState<Supplier | null>(null);
  const [deletingSupplier, setDeletingSupplier] = useState<Supplier | null>(null);
  const [isBulkDeactivating, setIsBulkDeactivating] = useState(false);

  // Form states
  const [formName, setFormName] = useState("");
  const [formEmail, setFormEmail] = useState("");
  const [formPhone, setFormPhone] = useState("");
  const [formAddress, setFormAddress] = useState("");
  const [formNotes, setFormNotes] = useState("");
  const [formError, setFormError] = useState("");
  const [deleteError, setDeleteError] = useState("");

  // Queries
  const {
    data: suppliers,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ["suppliers", searchQuery],
    queryFn: () => listSuppliers({ q: searchQuery || undefined }),
  });

  // Mutations
  const createMutation = useMutation({
    mutationFn: (data: SupplierCreate) => createSupplier(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["suppliers"] });
      setIsCreateModalOpen(false);
      resetForm();
    },
    onError: (err: any) => {
      setFormError(err.message || "Failed to create supplier. Make sure you have Admin or Manager permissions.");
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: SupplierUpdate }) =>
      updateSupplier(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["suppliers"] });
      setEditingSupplier(null);
      resetForm();
    },
    onError: (err: any) => {
      setFormError(err.message || "Failed to update supplier. Make sure you have Admin or Manager permissions.");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteSupplier(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["suppliers"] });
      setDeletingSupplier(null);
      setDeleteError("");
    },
    onError: (err: Error) => setDeleteError(err.message || "Failed to deactivate supplier."),
  });

  const resetForm = () => {
    setFormName("");
    setFormEmail("");
    setFormPhone("");
    setFormAddress("");
    setFormNotes("");
    setFormError("");
  };

  const handleOpenCreate = () => {
    resetForm();
    setIsCreateModalOpen(true);
  };

  const handleOpenEdit = (s: Supplier) => {
    resetForm();
    setEditingSupplier(s);
    setFormName(s.name);
    setFormEmail(s.email || "");
    setFormPhone(s.phone || "");
    setFormAddress(s.address || "");
    setFormNotes(s.notes || "");
  };

  const handleSubmitCreate = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError("");
    if (!formName.trim()) {
      setFormError("Supplier name is required.");
      return;
    }
    createMutation.mutate({
      name: formName.trim(),
      email: formEmail.trim() || undefined,
      phone: formPhone.trim() || undefined,
      address: formAddress.trim() || undefined,
      notes: formNotes.trim() || undefined,
    });
  };

  const handleSubmitEdit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingSupplier) return;
    setFormError("");
    if (!formName.trim()) {
      setFormError("Supplier name is required.");
      return;
    }
    updateMutation.mutate({
      id: editingSupplier.id,
      data: {
        name: formName.trim(),
        email: formEmail.trim() || undefined,
        phone: formPhone.trim() || undefined,
        address: formAddress.trim() || undefined,
        notes: formNotes.trim() || undefined,
      },
    });
  };

  // Selection handlers
  const handleSelectAll = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.checked && suppliers) {
      setSelectedSupplierIds(suppliers.map((s) => s.id));
    } else {
      setSelectedSupplierIds([]);
    }
  };

  const handleToggleSelect = (id: string) => {
    setSelectedSupplierIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id],
    );
  };

  const handleExportAll = () => {
    if (!suppliers || suppliers.length === 0) return;
    exportToCSV(
      "suppliers_directory",
      suppliers.map((s) => ({
        Name: s.name,
        Email: s.email || "",
        Phone: s.phone || "",
        Address: s.address || "",
        Notes: s.notes || "",
        Status: s.is_active ? "Active" : "Inactive",
      })),
    );
  };

  const handleExportSelected = () => {
    const selected = suppliers?.filter((s) => selectedSupplierIds.includes(s.id));
    if (!selected || selected.length === 0) return;
    exportToCSV(
      "selected_suppliers",
      selected.map((s) => ({
        Name: s.name,
        Email: s.email || "",
        Phone: s.phone || "",
        Address: s.address || "",
        Notes: s.notes || "",
        Status: s.is_active ? "Active" : "Inactive",
      })),
    );
  };

  const handleExecuteBulkDeactivate = async () => {
    for (const id of selectedSupplierIds) {
      try {
        await deleteSupplier(id);
      } catch {
        // Continue with remaining
      }
    }
    queryClient.invalidateQueries({ queryKey: ["suppliers"] });
    setSelectedSupplierIds([]);
    setIsBulkDeactivating(false);
  };

  return (
    <AppShell>
      <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8 space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-primary">
              Global Supply
            </p>
            <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-950 sm:text-3xl">
              Suppliers
            </h1>
            <p className="mt-1 text-xs text-slate-500">
              Manage product vendors, contact persons, tax registration details, and supply inventory chains.
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
              disabled={!suppliers || suppliers.length === 0}
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
              Add Supplier
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
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by supplier name, email, or notes..."
              className="w-full rounded-lg border border-border bg-slate-50 py-2 pl-9 pr-3 text-xs outline-none focus:border-primary focus:bg-white transition"
            />
          </div>
        </div>

        {/* Suppliers Table Card */}
        <div className="rounded-xl border border-border bg-white shadow-sm overflow-hidden">
          {isLoading ? (
            <div className="flex h-64 items-center justify-center">
              <LoadingSpinner message="Loading suppliers..." />
            </div>
          ) : isError ? (
            <div className="p-8">
              <ErrorStateView
                message={
                  error instanceof Error
                    ? error.message
                    : "Unable to load suppliers."
                }
                onRetry={() => refetch()}
              />
            </div>
          ) : !suppliers || suppliers.length === 0 ? (
            <div className="p-8">
              <EmptyStateView
                title="No suppliers found"
                message="Get started by adding a supplier vendor profile to associate with catalog products."
              />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-border bg-slate-50 text-slate-500 font-semibold uppercase tracking-wider">
                    <th className="py-3 px-4 w-12 text-center">
                      <input
                        type="checkbox"
                        checked={
                          suppliers.length > 0 &&
                          selectedSupplierIds.length === suppliers.length
                        }
                        onChange={handleSelectAll}
                        className="rounded border-slate-300 focus:ring-primary"
                      />
                    </th>
                    <th className="py-3.5 px-4 font-semibold">Vendor Info</th>
                    <th className="py-3.5 px-4 font-semibold">Contact</th>
                    <th className="py-3.5 px-4 font-semibold">Address</th>
                    <th className="py-3.5 px-4 font-semibold">Notes</th>
                    <th className="py-3.5 px-4 font-semibold">Status</th>
                    <th className="py-3.5 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border text-slate-700 bg-white">
                  {suppliers.map((s) => {
                    const isSelected = selectedSupplierIds.includes(s.id);
                    return (
                      <tr
                        key={s.id}
                        className={`hover:bg-slate-50 transition ${
                          isSelected ? "bg-primary/5" : ""
                        }`}
                      >
                        <td className="py-3.5 px-4 text-center">
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => handleToggleSelect(s.id)}
                            className="rounded border-slate-300 focus:ring-primary"
                          />
                        </td>
                        <td className="py-3.5 px-4">
                          <div className="flex items-center gap-3">
                            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
                              <Truck className="h-4 w-4" />
                            </div>
                            <div>
                              <p className="font-semibold text-slate-900">{s.name}</p>
                              <p className="text-[10px] text-slate-400">ID: {s.id.slice(0, 8)}...</p>
                            </div>
                          </div>
                        </td>
                        <td className="py-3.5 px-4 space-y-1">
                          {s.email && (
                            <div className="flex items-center gap-1.5 text-slate-600">
                              <Mail className="h-3 w-3 text-slate-400" />
                              <span>{s.email}</span>
                            </div>
                          )}
                          {s.phone && (
                            <div className="flex items-center gap-1.5 text-slate-600">
                              <Phone className="h-3 w-3 text-slate-400" />
                              <span>{s.phone}</span>
                            </div>
                          )}
                          {!s.email && !s.phone && (
                            <span className="text-slate-400 italic">No contact info</span>
                          )}
                        </td>
                        <td className="py-3.5 px-4">
                          {s.address ? (
                            <div className="flex items-start gap-1 text-slate-600 max-w-xs">
                              <MapPin className="h-3.5 w-3.5 text-slate-400 shrink-0 mt-0.5" />
                              <span className="truncate">{s.address}</span>
                            </div>
                          ) : (
                            <span className="text-slate-400 italic">No address</span>
                          )}
                        </td>
                        <td className="py-3.5 px-4">
                          <span className="text-slate-600 block max-w-xs truncate" title={s.notes || ""}>
                            {s.notes || <span className="text-slate-400 italic">-</span>}
                          </span>
                        </td>
                        <td className="py-3.5 px-4">
                          <StatusBadge status={s.is_active ? "Active" : "Inactive"} />
                        </td>
                        <td className="py-3.5 px-4 text-right">
                          <div className="flex items-center justify-end gap-1.5">
                            <button
                              type="button"
                              onClick={() => handleOpenEdit(s)}
                              className="rounded p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-900 transition"
                              title="Edit Supplier"
                            >
                              <Edit2 className="h-3.5 w-3.5" />
                            </button>
                            <button
                              type="button"
                              onClick={() => setDeletingSupplier(s)}
                              className="rounded p-1.5 text-rose-500 hover:bg-rose-50 hover:text-rose-700 transition"
                              title="Deactivate Supplier"
                            >
                              <Trash2 className="h-3.5 w-3.5" />
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

        {/* Bulk Action Bar */}
        {selectedSupplierIds.length > 0 && (
          <BulkActionBar
            selectedCount={selectedSupplierIds.length}
            onClear={() => setSelectedSupplierIds([])}
            onBulkExport={handleExportSelected}
            onBulkDeactivate={() => setIsBulkDeactivating(true)}
            resourceName="suppliers"
          />
        )}

        {/* Create Supplier Modal */}
        <Modal
          isOpen={isCreateModalOpen}
          onClose={() => setIsCreateModalOpen(false)}
          title="Add New Supplier"
          description="Create a profile for a new inventory supplier vendor."
        >
          <form onSubmit={handleSubmitCreate} className="space-y-4 text-slate-700 text-xs">
            {formError && (
              <div className="flex items-start gap-2.5 rounded-lg bg-rose-50 p-3 text-rose-800">
                <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                <span className="font-medium">{formError}</span>
              </div>
            )}

            <div className="space-y-1">
              <label htmlFor="create-name" className="font-semibold text-slate-900">
                Supplier / Vendor Name <span className="text-rose-500">*</span>
              </label>
              <input
                id="create-name"
                type="text"
                required
                value={formName}
                onChange={(e) => setFormName(e.target.value)}
                placeholder="e.g. Acme Corporation"
                className="w-full rounded-lg border border-border px-3 py-2 outline-none focus:border-primary focus:ring-1 focus:ring-primary"
              />
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-1">
                <label htmlFor="create-email" className="font-semibold text-slate-900">Email Address</label>
                <input
                  id="create-email"
                  type="email"
                  value={formEmail}
                  onChange={(e) => setFormEmail(e.target.value)}
                  placeholder="vendor@company.com"
                  className="w-full rounded-lg border border-border px-3 py-2 outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                />
              </div>

              <div className="space-y-1">
                <label htmlFor="create-phone" className="font-semibold text-slate-900">Phone Number</label>
                <input
                  id="create-phone"
                  type="text"
                  value={formPhone}
                  onChange={(e) => setFormPhone(e.target.value)}
                  placeholder="+1 (555) 000-0000"
                  className="w-full rounded-lg border border-border px-3 py-2 outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label htmlFor="create-address" className="font-semibold text-slate-900">Physical Address</label>
              <textarea
                id="create-address"
                rows={2}
                value={formAddress}
                onChange={(e) => setFormAddress(e.target.value)}
                placeholder="HQ Address or logistics facility"
                className="w-full rounded-lg border border-border px-3 py-2 outline-none focus:border-primary focus:ring-1 focus:ring-primary resize-none"
              />
            </div>

            <div className="space-y-1">
              <label htmlFor="create-notes" className="font-semibold text-slate-900">Internal Notes / Specifications</label>
              <textarea
                id="create-notes"
                rows={2}
                value={formNotes}
                onChange={(e) => setFormNotes(e.target.value)}
                placeholder="Product groups, payment terms, or lead times..."
                className="w-full rounded-lg border border-border px-3 py-2 outline-none focus:border-primary focus:ring-1 focus:ring-primary resize-none"
              />
            </div>

            <div className="flex justify-end gap-2 border-t border-border pt-4 mt-6">
              <button
                type="button"
                onClick={() => setIsCreateModalOpen(false)}
                className="rounded-lg border border-border bg-white px-4 py-2 font-medium hover:bg-slate-50 transition"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={createMutation.isPending}
                className="rounded-lg bg-primary px-4 py-2 font-semibold text-white shadow-sm hover:opacity-90 transition disabled:opacity-50 flex items-center gap-1.5"
              >
                {createMutation.isPending && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                Add Supplier
              </button>
            </div>
          </form>
        </Modal>

        {/* Edit Supplier Modal */}
        <Modal
          isOpen={!!editingSupplier}
          onClose={() => setEditingSupplier(null)}
          title="Edit Supplier Profile"
          description="Update notes, physical address, or contact parameters for this vendor."
        >
          <form onSubmit={handleSubmitEdit} className="space-y-4 text-slate-700 text-xs">
            {formError && (
              <div className="flex items-start gap-2.5 rounded-lg bg-rose-50 p-3 text-rose-800">
                <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                <span className="font-medium">{formError}</span>
              </div>
            )}

            <div className="space-y-1">
              <label htmlFor="edit-name" className="font-semibold text-slate-900">
                Supplier / Vendor Name <span className="text-rose-500">*</span>
              </label>
              <input
                id="edit-name"
                type="text"
                required
                value={formName}
                onChange={(e) => setFormName(e.target.value)}
                placeholder="e.g. Acme Corporation"
                className="w-full rounded-lg border border-border px-3 py-2 outline-none focus:border-primary focus:ring-1 focus:ring-primary"
              />
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-1">
                <label htmlFor="edit-email" className="font-semibold text-slate-900">Email Address</label>
                <input
                  id="edit-email"
                  type="email"
                  value={formEmail}
                  onChange={(e) => setFormEmail(e.target.value)}
                  placeholder="vendor@company.com"
                  className="w-full rounded-lg border border-border px-3 py-2 outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                />
              </div>

              <div className="space-y-1">
                <label htmlFor="edit-phone" className="font-semibold text-slate-900">Phone Number</label>
                <input
                  id="edit-phone"
                  type="text"
                  value={formPhone}
                  onChange={(e) => setFormPhone(e.target.value)}
                  placeholder="+1 (555) 000-0000"
                  className="w-full rounded-lg border border-border px-3 py-2 outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label htmlFor="edit-address" className="font-semibold text-slate-900">Physical Address</label>
              <textarea
                id="edit-address"
                rows={2}
                value={formAddress}
                onChange={(e) => setFormAddress(e.target.value)}
                placeholder="HQ Address or logistics facility"
                className="w-full rounded-lg border border-border px-3 py-2 outline-none focus:border-primary focus:ring-1 focus:ring-primary resize-none"
              />
            </div>

            <div className="space-y-1">
              <label htmlFor="edit-notes" className="font-semibold text-slate-900">Internal Notes / Specifications</label>
              <textarea
                id="edit-notes"
                rows={2}
                value={formNotes}
                onChange={(e) => setFormNotes(e.target.value)}
                placeholder="Product groups, payment terms, or lead times..."
                className="w-full rounded-lg border border-border px-3 py-2 outline-none focus:border-primary focus:ring-1 focus:ring-primary resize-none"
              />
            </div>

            <div className="flex justify-end gap-2 border-t border-border pt-4 mt-6">
              <button
                type="button"
                onClick={() => setEditingSupplier(null)}
                className="rounded-lg border border-border bg-white px-4 py-2 font-medium hover:bg-slate-50 transition"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={updateMutation.isPending}
                className="rounded-lg bg-primary px-4 py-2 font-semibold text-white shadow-sm hover:opacity-90 transition disabled:opacity-50 flex items-center gap-1.5"
              >
                {updateMutation.isPending && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                Save Changes
              </button>
            </div>
          </form>
        </Modal>

        {/* Deactivate Supplier Dialog */}
        <ConfirmDialog
          isOpen={!!deletingSupplier}
          title="Deactivate Supplier"
          message={
            deleteError ||
            `Are you sure you want to deactivate ${deletingSupplier?.name}? This vendor's listing will be set to inactive state, but existing order records linking to it will not be deleted.`
          }
          confirmText="Deactivate"
          cancelText="Cancel"
          variant="danger"
          onConfirm={() => {
            if (deletingSupplier) {
              setDeleteError("");
              deleteMutation.mutate(deletingSupplier.id);
            }
          }}
          onClose={() => {
            setDeletingSupplier(null);
            setDeleteError("");
          }}
        />

        {/* Bulk Deactivate Dialog */}
        <ConfirmDialog
          isOpen={isBulkDeactivating}
          title="Deactivate Selected Suppliers"
          message={`Are you sure you want to deactivate ${selectedSupplierIds.length} selected suppliers?`}
          confirmText="Deactivate All"
          cancelText="Cancel"
          variant="danger"
          onConfirm={handleExecuteBulkDeactivate}
          onClose={() => setIsBulkDeactivating(false)}
        />
      </div>
    </AppShell>
  );
}
