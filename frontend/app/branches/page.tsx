"use client";

import React, { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertCircle,
  Building2,
  Edit2,
  Loader2,
  MapPin,
  Phone,
  Plus,
  RefreshCw,
  Search,
  Trash2,
} from "lucide-react";

import AppShell from "../../components/app-shell";
import { StatusBadge } from "../../components/ui/badge";
import { ConfirmDialog } from "../../components/ui/confirm-dialog";
import { Modal } from "../../components/ui/modal";
import {
  EmptyStateView,
  ErrorStateView,
  LoadingSpinner,
} from "../../components/ui/state-views";
import {
  createBranch,
  deleteBranch,
  listBranches,
  updateBranch,
} from "../../lib/branches";
import type { Branch, BranchCreate, BranchUpdate } from "../../types/branches";

export default function BranchesPage() {
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState("");
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingBranch, setEditingBranch] = useState<Branch | null>(null);
  const [deletingBranch, setDeletingBranch] = useState<Branch | null>(null);

  // Form states
  const [formCode, setFormCode] = useState("");
  const [formName, setFormName] = useState("");
  const [formAddress, setFormAddress] = useState("");
  const [formPhone, setFormPhone] = useState("");
  const [formError, setFormError] = useState("");

  const {
    data: branches,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ["branches"],
    queryFn: () => listBranches(),
  });

  const createMutation = useMutation({
    mutationFn: (data: BranchCreate) => createBranch(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["branches"] });
      queryClient.invalidateQueries({ queryKey: ["branch-analytics"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
      setIsCreateModalOpen(false);
      resetForm();
    },
    onError: (err: Error) => {
      setFormError(err.message || "Failed to create branch.");
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: BranchUpdate }) =>
      updateBranch(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["branches"] });
      queryClient.invalidateQueries({ queryKey: ["branch-analytics"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
      setEditingBranch(null);
      resetForm();
    },
    onError: (err: Error) => {
      setFormError(err.message || "Failed to update branch.");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteBranch(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["branches"] });
      queryClient.invalidateQueries({ queryKey: ["branch-analytics"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
      setDeletingBranch(null);
    },
  });

  const resetForm = () => {
    setFormCode("");
    setFormName("");
    setFormAddress("");
    setFormPhone("");
    setFormError("");
  };

  const handleOpenCreate = () => {
    resetForm();
    setIsCreateModalOpen(true);
  };

  const handleOpenEdit = (b: Branch) => {
    resetForm();
    setEditingBranch(b);
    setFormCode(b.code);
    setFormName(b.name);
    setFormAddress(b.address || "");
    setFormPhone(b.phone || "");
  };

  const handleSubmitCreate = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError("");
    createMutation.mutate({
      code: formCode.trim().toUpperCase(),
      name: formName.trim(),
      address: formAddress.trim() || undefined,
      phone: formPhone.trim() || undefined,
    });
  };

  const handleSubmitEdit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingBranch) return;
    setFormError("");
    updateMutation.mutate({
      id: editingBranch.id,
      data: {
        code: formCode.trim().toUpperCase() || undefined,
        name: formName.trim(),
        address: formAddress.trim() || undefined,
        phone: formPhone.trim() || undefined,
      },
    });
  };

  const filteredBranches = branches?.filter((b) =>
    searchQuery
      ? b.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        b.code.toLowerCase().includes(searchQuery.toLowerCase())
      : true,
  );

  return (
    <AppShell>
      <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8 space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-primary">
              Organization Infrastructure
            </p>
            <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-950 sm:text-3xl">
              Branches
            </h1>
            <p className="mt-1 text-xs text-slate-500">
              Manage multi-location branch codes, physical stores, and fulfillment warehouses.
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
              onClick={handleOpenCreate}
              className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3.5 py-2 text-xs font-semibold text-white shadow-sm transition hover:opacity-90"
            >
              <Plus className="h-4 w-4" />
              Add Branch
            </button>
          </div>
        </div>

        {/* Search */}
        <div className="flex items-center justify-between rounded-xl border border-border bg-white p-4 shadow-sm">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              type="search"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search branches by name or code..."
              className="w-full rounded-lg border border-border bg-slate-50 py-2 pl-9 pr-3 text-xs outline-none focus:border-primary focus:bg-white transition"
            />
          </div>
        </div>

        {/* Branches Table */}
        <div className="rounded-xl border border-border bg-white shadow-sm overflow-hidden">
          {isLoading ? (
            <div className="flex h-64 items-center justify-center">
              <LoadingSpinner message="Loading branch infrastructure..." />
            </div>
          ) : isError ? (
            <div className="p-8">
              <ErrorStateView
                message={
                  error instanceof Error
                    ? error.message
                    : "Unable to load branches."
                }
                onRetry={() => refetch()}
              />
            </div>
          ) : !filteredBranches || filteredBranches.length === 0 ? (
            <div className="p-8">
              <EmptyStateView
                title="No branches found"
                message={
                  searchQuery
                    ? "No branches match your search criteria."
                    : "No branches registered yet. Click 'Add Branch' to set up your primary location."
                }
              />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-border bg-slate-50 text-slate-500">
                    <th className="py-3.5 pl-6 pr-3 font-semibold">Branch Name</th>
                    <th className="py-3.5 px-3 font-semibold">Branch Code</th>
                    <th className="py-3.5 px-3 font-semibold">Phone Contact</th>
                    <th className="py-3.5 px-3 font-semibold">Physical Address</th>
                    <th className="py-3.5 px-3 text-center font-semibold">Status</th>
                    <th className="py-3.5 pl-3 pr-6 text-right font-semibold">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredBranches.map((branch) => (
                    <tr key={branch.id} className="hover:bg-slate-50 transition">
                      <td className="py-3.5 pl-6 pr-3 font-semibold text-slate-900">
                        <div className="flex items-center gap-2.5">
                          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-teal-50 text-teal-700 font-bold text-xs">
                            <Building2 className="h-4 w-4" />
                          </div>
                          <span>{branch.name}</span>
                        </div>
                      </td>
                      <td className="py-3.5 px-3 font-mono font-bold text-slate-800">
                        {branch.code}
                      </td>
                      <td className="py-3.5 px-3 text-slate-600">
                        {branch.phone ? (
                          <span className="inline-flex items-center gap-1">
                            <Phone className="h-3 w-3 text-slate-400" />
                            {branch.phone}
                          </span>
                        ) : (
                          "—"
                        )}
                      </td>
                      <td className="py-3.5 px-3 text-slate-500 max-w-xs truncate">
                        {branch.address ? (
                          <span className="inline-flex items-center gap-1 truncate">
                            <MapPin className="h-3 w-3 text-slate-400 shrink-0" />
                            {branch.address}
                          </span>
                        ) : (
                          "—"
                        )}
                      </td>
                      <td className="py-3.5 px-3 text-center">
                        <StatusBadge
                          status={branch.is_active ? "ACTIVE" : "INACTIVE"}
                        />
                      </td>
                      <td className="py-3.5 pl-3 pr-6 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            type="button"
                            onClick={() => handleOpenEdit(branch)}
                            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition"
                            title="Edit branch"
                          >
                            <Edit2 className="h-3.5 w-3.5" />
                          </button>
                          {branch.is_active && (
                            <button
                              type="button"
                              onClick={() => setDeletingBranch(branch)}
                              className="rounded-lg p-1.5 text-slate-400 hover:bg-rose-50 hover:text-rose-600 transition"
                              title="Deactivate branch"
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Create Branch Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Add New Branch"
        description="Register a location code and physical facility."
      >
        <form onSubmit={handleSubmitCreate} className="space-y-4">
          {formError && (
            <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-2.5 text-xs text-red-700">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <p>{formError}</p>
            </div>
          )}

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-800">
                Branch Code <span className="text-rose-500">*</span>
              </label>
              <input
                type="text"
                required
                value={formCode}
                onChange={(e) => setFormCode(e.target.value.toUpperCase())}
                placeholder="e.g. BR-01"
                className="w-full rounded-lg border border-border px-3 py-2 text-xs font-mono outline-none focus:border-primary transition"
              />
            </div>

            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-800">
                Branch Name <span className="text-rose-500">*</span>
              </label>
              <input
                type="text"
                required
                value={formName}
                onChange={(e) => setFormName(e.target.value)}
                placeholder="Main Warehouse / Store"
                className="w-full rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary transition"
              />
            </div>
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-800">
              Contact Phone
            </label>
            <input
              type="tel"
              value={formPhone}
              onChange={(e) => setFormPhone(e.target.value)}
              placeholder="+92 21 111 222 333"
              className="w-full rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary transition"
            />
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-800">
              Facility Address
            </label>
            <input
              type="text"
              value={formAddress}
              onChange={(e) => setFormAddress(e.target.value)}
              placeholder="Physical street address, city"
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
              Create Branch
            </button>
          </div>
        </form>
      </Modal>

      {/* Edit Branch Modal */}
      <Modal
        isOpen={!!editingBranch}
        onClose={() => setEditingBranch(null)}
        title="Edit Branch"
        description="Update branch code or contact specifications."
      >
        <form onSubmit={handleSubmitEdit} className="space-y-4">
          {formError && (
            <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-2.5 text-xs text-red-700">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <p>{formError}</p>
            </div>
          )}

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-800">
                Branch Code <span className="text-rose-500">*</span>
              </label>
              <input
                type="text"
                required
                value={formCode}
                onChange={(e) => setFormCode(e.target.value.toUpperCase())}
                className="w-full rounded-lg border border-border px-3 py-2 text-xs font-mono outline-none focus:border-primary transition"
              />
            </div>

            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-800">
                Branch Name <span className="text-rose-500">*</span>
              </label>
              <input
                type="text"
                required
                value={formName}
                onChange={(e) => setFormName(e.target.value)}
                className="w-full rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary transition"
              />
            </div>
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-800">
              Contact Phone
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
              Facility Address
            </label>
            <input
              type="text"
              value={formAddress}
              onChange={(e) => setFormAddress(e.target.value)}
              className="w-full rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary transition"
            />
          </div>

          <div className="flex items-center justify-end gap-2 border-t border-border pt-4">
            <button
              type="button"
              onClick={() => setEditingBranch(null)}
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

      {/* Deactivate Branch Confirmation */}
      <ConfirmDialog
        isOpen={!!deletingBranch}
        onClose={() => setDeletingBranch(null)}
        onConfirm={() => deletingBranch && deleteMutation.mutate(deletingBranch.id)}
        title="Deactivate Branch"
        message={`Are you sure you want to deactivate branch "${deletingBranch?.name}" (${deletingBranch?.code})?`}
        confirmText="Deactivate"
        variant="danger"
        isLoading={deleteMutation.isPending}
      />
    </AppShell>
  );
}
