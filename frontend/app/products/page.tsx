"use client";

import React, { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertCircle,
  Download,
  Edit2,
  Filter,
  Loader2,
  Package,
  Plus,
  RefreshCw,
  Search,
  Trash2,
} from "lucide-react";

import AppShell from "../../components/app-shell";
import { formatCurrency } from "../../components/dashboard/stat-card";
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
import {
  createProduct,
  deleteProduct,
  listCategories,
  listProducts,
  updateProduct,
} from "../../lib/products";
import type { Product, ProductCreate, ProductUpdate } from "../../types/products";

export default function ProductsPage() {
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("");
  const [selectedProductIds, setSelectedProductIds] = useState<string[]>([]);

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [deletingProduct, setDeletingProduct] = useState<Product | null>(null);
  const [isBulkDeactivating, setIsBulkDeactivating] = useState(false);

  // Form states
  const [formSku, setFormSku] = useState("");
  const [formName, setFormName] = useState("");
  const [formDesc, setFormDesc] = useState("");
  const [formUnit, setFormUnit] = useState("pcs");
  const [formCost, setFormCost] = useState("");
  const [formPrice, setFormPrice] = useState("");
  const [formTax, setFormTax] = useState("0");
  const [formCategoryId, setFormCategoryId] = useState("");
  const [formError, setFormError] = useState("");

  // Queries
  const {
    data: products,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ["products", searchQuery, selectedCategory],
    queryFn: () =>
      listProducts({
        q: searchQuery || undefined,
        category_id: selectedCategory || undefined,
      }),
  });

  const { data: categories } = useQuery({
    queryKey: ["categories"],
    queryFn: () => listCategories(),
  });

  // Mutations
  const createMutation = useMutation({
    mutationFn: (data: ProductCreate) => createProduct(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["products"] });
      queryClient.invalidateQueries({ queryKey: ["product-analytics"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
      setIsCreateModalOpen(false);
      resetForm();
    },
    onError: (err: Error) => {
      setFormError(err.message || "Failed to create product.");
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: ProductUpdate }) =>
      updateProduct(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["products"] });
      queryClient.invalidateQueries({ queryKey: ["product-analytics"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
      setEditingProduct(null);
      resetForm();
    },
    onError: (err: Error) => {
      setFormError(err.message || "Failed to update product.");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteProduct(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["products"] });
      queryClient.invalidateQueries({ queryKey: ["product-analytics"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
      setDeletingProduct(null);
    },
  });

  const resetForm = () => {
    setFormSku("");
    setFormName("");
    setFormDesc("");
    setFormUnit("pcs");
    setFormCost("");
    setFormPrice("");
    setFormTax("0");
    setFormCategoryId("");
    setFormError("");
  };

  const handleOpenCreate = () => {
    resetForm();
    setIsCreateModalOpen(true);
  };

  const handleOpenEdit = (p: Product) => {
    resetForm();
    setEditingProduct(p);
    setFormSku(p.sku);
    setFormName(p.name);
    setFormDesc(p.description || "");
    setFormUnit(p.unit);
    setFormCost(p.cost_price.toString());
    setFormPrice(p.selling_price.toString());
    setFormTax((Number(p.tax_rate) * 100).toString());
    setFormCategoryId(p.category_id || "");
  };

  const handleSubmitCreate = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError("");
    const cost = parseFloat(formCost);
    const price = parseFloat(formPrice);
    const tax = parseFloat(formTax) / 100;

    if (isNaN(cost) || isNaN(price)) {
      setFormError("Please enter valid prices.");
      return;
    }

    createMutation.mutate({
      sku: formSku.trim(),
      name: formName.trim(),
      description: formDesc.trim() || undefined,
      unit: formUnit.trim(),
      cost_price: cost,
      selling_price: price,
      tax_rate: isNaN(tax) ? 0 : tax,
      category_id: formCategoryId || undefined,
    });
  };

  const handleSubmitEdit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingProduct) return;
    setFormError("");
    const cost = parseFloat(formCost);
    const price = parseFloat(formPrice);
    const tax = parseFloat(formTax) / 100;

    updateMutation.mutate({
      id: editingProduct.id,
      data: {
        name: formName.trim(),
        description: formDesc.trim() || undefined,
        unit: formUnit.trim(),
        cost_price: isNaN(cost) ? undefined : cost,
        selling_price: isNaN(price) ? undefined : price,
        tax_rate: isNaN(tax) ? undefined : tax,
        category_id: formCategoryId || undefined,
      },
    });
  };

  // Selection handlers
  const handleSelectAll = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.checked && products) {
      setSelectedProductIds(products.map((p) => p.id));
    } else {
      setSelectedProductIds([]);
    }
  };

  const handleToggleSelect = (id: string) => {
    setSelectedProductIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id],
    );
  };

  const handleExportAll = () => {
    if (!products || products.length === 0) return;
    exportToCSV(
      "products_catalog",
      products.map((p) => ({
        SKU: p.sku,
        Name: p.name,
        Category: p.category_id ? categoryMap.get(p.category_id) || "" : "",
        Unit: p.unit,
        CostPrice: p.cost_price,
        SellingPrice: p.selling_price,
        TaxRate: p.tax_rate,
        Status: p.is_active ? "Active" : "Inactive",
      })),
    );
  };

  const handleExportSelected = () => {
    const selected = products?.filter((p) => selectedProductIds.includes(p.id));
    if (!selected || selected.length === 0) return;
    exportToCSV(
      "selected_products",
      selected.map((p) => ({
        SKU: p.sku,
        Name: p.name,
        Category: p.category_id ? categoryMap.get(p.category_id) || "" : "",
        Unit: p.unit,
        CostPrice: p.cost_price,
        SellingPrice: p.selling_price,
        TaxRate: p.tax_rate,
        Status: p.is_active ? "Active" : "Inactive",
      })),
    );
  };

  const handleExecuteBulkDeactivate = async () => {
    for (const id of selectedProductIds) {
      try {
        await deleteProduct(id);
      } catch {
        // Continue with remaining
      }
    }
    queryClient.invalidateQueries({ queryKey: ["products"] });
    setSelectedProductIds([]);
    setIsBulkDeactivating(false);
  };

  const categoryMap = new Map(categories?.map((c) => [c.id, c.name]) || []);

  return (
    <AppShell>
      <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8 space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-primary">
              Catalog Management
            </p>
            <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-950 sm:text-3xl">
              Products
            </h1>
            <p className="mt-1 text-xs text-slate-500">
              Manage catalog products, SKU codes, pricing, and category classifications.
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
              disabled={!products || products.length === 0}
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
              Add Product
            </button>
          </div>
        </div>

        {/* Filters & Search */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between rounded-xl border border-border bg-white p-4 shadow-sm">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              type="search"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by product name or SKU..."
              className="w-full rounded-lg border border-border bg-slate-50 py-2 pl-9 pr-3 text-xs outline-none focus:border-primary focus:bg-white transition"
            />
          </div>

          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-slate-400" />
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="rounded-lg border border-border bg-white px-3 py-2 text-xs text-slate-700 outline-none focus:border-primary transition"
            >
              <option value="">All Categories</option>
              {categories?.map((cat) => (
                <option key={cat.id} value={cat.id}>
                  {cat.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Products Table Card */}
        <div className="rounded-xl border border-border bg-white shadow-sm overflow-hidden">
          {isLoading ? (
            <div className="flex h-64 items-center justify-center">
              <LoadingSpinner message="Loading products catalog..." />
            </div>
          ) : isError ? (
            <div className="p-8">
              <ErrorStateView
                message={
                  error instanceof Error
                    ? error.message
                    : "Unable to load products."
                }
                onRetry={() => refetch()}
              />
            </div>
          ) : !products || products.length === 0 ? (
            <div className="p-8">
              <EmptyStateView
                title="No products found"
                message={
                  searchQuery || selectedCategory
                    ? "No products matched your search filters."
                    : "Your catalog is empty. Click 'Add Product' to get started."
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
                          selectedProductIds.length === products.length &&
                          products.length > 0
                        }
                        onChange={handleSelectAll}
                        className="rounded border-border text-primary focus:ring-primary h-3.5 w-3.5"
                      />
                    </th>
                    <th className="py-3.5 px-3 font-semibold">SKU</th>
                    <th className="py-3.5 px-3 font-semibold">Product Name</th>
                    <th className="py-3.5 px-3 font-semibold">Category</th>
                    <th className="py-3.5 px-3 font-semibold">Unit</th>
                    <th className="py-3.5 px-3 text-right font-semibold">Cost Price</th>
                    <th className="py-3.5 px-3 text-right font-semibold">Selling Price</th>
                    <th className="py-3.5 px-3 text-center font-semibold">Status</th>
                    <th className="py-3.5 pl-3 pr-6 text-right font-semibold">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {products.map((product) => {
                    const isChecked = selectedProductIds.includes(product.id);
                    return (
                      <tr
                        key={product.id}
                        className={`transition ${
                          isChecked ? "bg-teal-50/40" : "hover:bg-slate-50"
                        }`}
                      >
                        <td className="py-3.5 pl-4 pr-2">
                          <input
                            type="checkbox"
                            checked={isChecked}
                            onChange={() => handleToggleSelect(product.id)}
                            className="rounded border-border text-primary focus:ring-primary h-3.5 w-3.5"
                          />
                        </td>
                        <td className="py-3.5 px-3 font-mono font-medium text-slate-900">
                          {product.sku}
                        </td>
                        <td className="py-3.5 px-3 font-semibold text-slate-900">
                          <div className="flex items-center gap-2">
                            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/10 text-primary">
                              <Package className="h-3.5 w-3.5" />
                            </div>
                            <div>
                              <p className="font-semibold text-slate-900">{product.name}</p>
                              {product.description && (
                                <p className="text-[10px] text-slate-400 truncate max-w-xs">
                                  {product.description}
                                </p>
                              )}
                            </div>
                          </div>
                        </td>
                        <td className="py-3.5 px-3 text-slate-600">
                          {product.category_id
                            ? categoryMap.get(product.category_id) || "—"
                            : "—"}
                        </td>
                        <td className="py-3.5 px-3 text-slate-600 font-mono">
                          {product.unit}
                        </td>
                        <td className="py-3.5 px-3 text-right font-medium text-slate-600">
                          {formatCurrency(product.cost_price)}
                        </td>
                        <td className="py-3.5 px-3 text-right font-bold text-slate-950">
                          {formatCurrency(product.selling_price)}
                        </td>
                        <td className="py-3.5 px-3 text-center">
                          <StatusBadge
                            status={product.is_active ? "ACTIVE" : "INACTIVE"}
                          />
                        </td>
                        <td className="py-3.5 pl-3 pr-6 text-right">
                          <div className="flex items-center justify-end gap-1.5">
                            <button
                              type="button"
                              onClick={() => handleOpenEdit(product)}
                              className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition"
                              title="Edit product"
                            >
                              <Edit2 className="h-3.5 w-3.5" />
                            </button>
                            {product.is_active && (
                              <button
                                type="button"
                                onClick={() => setDeletingProduct(product)}
                                className="rounded-lg p-1.5 text-slate-400 hover:bg-rose-50 hover:text-rose-600 transition"
                                title="Deactivate product"
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
      </div>

      {/* Floating Bulk Action Bar */}
      <BulkActionBar
        selectedCount={selectedProductIds.length}
        onClear={() => setSelectedProductIds([])}
        onBulkExport={handleExportSelected}
        onBulkDeactivate={() => setIsBulkDeactivating(true)}
        resourceName="products"
      />

      {/* Bulk Deactivate Confirmation */}
      <ConfirmDialog
        isOpen={isBulkDeactivating}
        onClose={() => setIsBulkDeactivating(false)}
        onConfirm={handleExecuteBulkDeactivate}
        title="Bulk Deactivate Products"
        message={`Are you sure you want to deactivate ${selectedProductIds.length} selected products?`}
        confirmText="Deactivate All"
        variant="danger"
      />

      {/* Create Product Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Add New Product"
        description="Enter product specifications and catalog details."
        maxWidth="lg"
      >
        <form onSubmit={handleSubmitCreate} className="space-y-4">
          {formError && (
            <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-2.5 text-xs text-red-700">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <p>{formError}</p>
            </div>
          )}

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-800">
                SKU <span className="text-rose-500">*</span>
              </label>
              <input
                type="text"
                required
                value={formSku}
                onChange={(e) => setFormSku(e.target.value)}
                placeholder="PROD-001"
                className="w-full rounded-lg border border-border px-3 py-2 text-xs font-mono outline-none focus:border-primary transition"
              />
            </div>

            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-800">
                Product Name <span className="text-rose-500">*</span>
              </label>
              <input
                type="text"
                required
                value={formName}
                onChange={(e) => setFormName(e.target.value)}
                placeholder="Premium Widget"
                className="w-full rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary transition"
              />
            </div>

            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-800">
                Category
              </label>
              <select
                value={formCategoryId}
                onChange={(e) => setFormCategoryId(e.target.value)}
                className="w-full rounded-lg border border-border bg-white px-3 py-2 text-xs outline-none focus:border-primary transition"
              >
                <option value="">Select category...</option>
                {categories?.map((cat) => (
                  <option key={cat.id} value={cat.id}>
                    {cat.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-800">
                Unit of Measure <span className="text-rose-500">*</span>
              </label>
              <input
                type="text"
                required
                value={formUnit}
                onChange={(e) => setFormUnit(e.target.value)}
                placeholder="pcs, kg, box"
                className="w-full rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary transition"
              />
            </div>

            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-800">
                Cost Price (Rs.) <span className="text-rose-500">*</span>
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                required
                value={formCost}
                onChange={(e) => setFormCost(e.target.value)}
                placeholder="100.00"
                className="w-full rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary transition"
              />
            </div>

            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-800">
                Selling Price (Rs.) <span className="text-rose-500">*</span>
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                required
                value={formPrice}
                onChange={(e) => setFormPrice(e.target.value)}
                placeholder="150.00"
                className="w-full rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary transition"
              />
            </div>

            <div className="sm:col-span-2">
              <label className="mb-1 block text-xs font-semibold text-slate-800">
                Tax Rate (%)
              </label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="100"
                value={formTax}
                onChange={(e) => setFormTax(e.target.value)}
                placeholder="0"
                className="w-full rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary transition"
              />
            </div>

            <div className="sm:col-span-2">
              <label className="mb-1 block text-xs font-semibold text-slate-800">
                Description
              </label>
              <textarea
                rows={2}
                value={formDesc}
                onChange={(e) => setFormDesc(e.target.value)}
                placeholder="Optional product description..."
                className="w-full rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary transition"
              />
            </div>
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
              Create Product
            </button>
          </div>
        </form>
      </Modal>

      {/* Edit Product Modal */}
      <Modal
        isOpen={!!editingProduct}
        onClose={() => setEditingProduct(null)}
        title="Edit Product"
        description={`Modify product specifications for SKU ${editingProduct?.sku}`}
        maxWidth="lg"
      >
        <form onSubmit={handleSubmitEdit} className="space-y-4">
          {formError && (
            <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-2.5 text-xs text-red-700">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <p>{formError}</p>
            </div>
          )}

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-800">
                SKU (Read Only)
              </label>
              <input
                type="text"
                disabled
                value={formSku}
                className="w-full rounded-lg border border-slate-200 bg-slate-100 px-3 py-2 text-xs font-mono text-slate-500 cursor-not-allowed"
              />
            </div>

            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-800">
                Product Name <span className="text-rose-500">*</span>
              </label>
              <input
                type="text"
                required
                value={formName}
                onChange={(e) => setFormName(e.target.value)}
                className="w-full rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary transition"
              />
            </div>

            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-800">
                Category
              </label>
              <select
                value={formCategoryId}
                onChange={(e) => setFormCategoryId(e.target.value)}
                className="w-full rounded-lg border border-border bg-white px-3 py-2 text-xs outline-none focus:border-primary transition"
              >
                <option value="">Select category...</option>
                {categories?.map((cat) => (
                  <option key={cat.id} value={cat.id}>
                    {cat.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-800">
                Unit of Measure <span className="text-rose-500">*</span>
              </label>
              <input
                type="text"
                required
                value={formUnit}
                onChange={(e) => setFormUnit(e.target.value)}
                className="w-full rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary transition"
              />
            </div>

            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-800">
                Cost Price (Rs.) <span className="text-rose-500">*</span>
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                required
                value={formCost}
                onChange={(e) => setFormCost(e.target.value)}
                className="w-full rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary transition"
              />
            </div>

            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-800">
                Selling Price (Rs.) <span className="text-rose-500">*</span>
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                required
                value={formPrice}
                onChange={(e) => setFormPrice(e.target.value)}
                className="w-full rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary transition"
              />
            </div>

            <div className="sm:col-span-2">
              <label className="mb-1 block text-xs font-semibold text-slate-800">
                Tax Rate (%)
              </label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="100"
                value={formTax}
                onChange={(e) => setFormTax(e.target.value)}
                className="w-full rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary transition"
              />
            </div>

            <div className="sm:col-span-2">
              <label className="mb-1 block text-xs font-semibold text-slate-800">
                Description
              </label>
              <textarea
                rows={2}
                value={formDesc}
                onChange={(e) => setFormDesc(e.target.value)}
                className="w-full rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary transition"
              />
            </div>
          </div>

          <div className="flex items-center justify-end gap-2 border-t border-border pt-4">
            <button
              type="button"
              onClick={() => setEditingProduct(null)}
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

      {/* Deactivate Product Confirmation */}
      <ConfirmDialog
        isOpen={!!deletingProduct}
        onClose={() => setDeletingProduct(null)}
        onConfirm={() => deletingProduct && deleteMutation.mutate(deletingProduct.id)}
        title="Deactivate Product"
        message={`Are you sure you want to deactivate "${deletingProduct?.name}" (SKU: ${deletingProduct?.sku})? Deactivated products will no longer be available for new orders.`}
        confirmText="Deactivate"
        variant="danger"
        isLoading={deleteMutation.isPending}
      />
    </AppShell>
  );
}
