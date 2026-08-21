"use client";

import { useState } from "react";
import type { ReactNode } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertCircle,
  Check,
  Eye,
  FilePlus,
  Filter,
  Loader2,
  Plus,
  RefreshCw,
  Search,
  Send,
  Truck,
  XCircle,
} from "lucide-react";

import AppShell from "../../components/app-shell";
import { formatCurrency } from "../../components/dashboard/stat-card";
import { StatusBadge } from "../../components/ui/badge";
import { ConfirmDialog } from "../../components/ui/confirm-dialog";
import { Modal } from "../../components/ui/modal";
import { EmptyStateView, ErrorStateView, LoadingSpinner } from "../../components/ui/state-views";
import { listBranches } from "../../lib/branches";
import { listProducts } from "../../lib/products";
import { listSuppliers } from "../../lib/suppliers";
import {
  approvePurchaseOrder,
  cancelPurchaseOrder,
  createPurchaseOrder,
  getPurchaseOrder,
  listPurchaseOrders,
  receivePurchaseOrder,
  submitPurchaseOrder,
  updatePurchaseOrder,
} from "../../lib/purchase-orders";
import type { Branch } from "../../types/branches";
import type { Product } from "../../types/products";
import type { Supplier } from "../../types/suppliers";
import type {
  PurchaseOrder,
  PurchaseOrderCreate,
  PurchaseOrderStatus,
  ReceivePurchaseOrder,
} from "../../types/purchase-orders";

const statuses: PurchaseOrderStatus[] = ["DRAFT", "SUBMITTED", "APPROVED", "PARTIALLY_RECEIVED", "RECEIVED", "CANCELLED"];

type FormItem = { product_id: string; quantity: string; unit_cost: string };

export default function PurchaseOrdersPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [supplierId, setSupplierId] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [page, setPage] = useState(1);
  const [formOpen, setFormOpen] = useState(false);
  const [editingOrder, setEditingOrder] = useState<PurchaseOrder | null>(null);
  const [detailId, setDetailId] = useState<string | null>(null);
  const [confirmAction, setConfirmAction] = useState<{ order: PurchaseOrder; action: "submit" | "approve" | "cancel" } | null>(null);
  const [receiveOrder, setReceiveOrder] = useState<PurchaseOrder | null>(null);
  const [formError, setFormError] = useState("");
  const [receiveError, setReceiveError] = useState("");
  const [formSupplierId, setFormSupplierId] = useState("");
  const [formBranchId, setFormBranchId] = useState("");
  const [formExpectedDate, setFormExpectedDate] = useState("");
  const [formNotes, setFormNotes] = useState("");
  const [formTax, setFormTax] = useState("0");
  const [formDiscount, setFormDiscount] = useState("0");
  const [formItems, setFormItems] = useState<FormItem[]>([]);
  const [receiveReference, setReceiveReference] = useState("");
  const [receiveItems, setReceiveItems] = useState<Record<string, string>>({});

  const ordersQuery = useQuery({
    queryKey: ["purchase-orders", page, search, status, supplierId, dateFrom, dateTo],
    queryFn: () => listPurchaseOrders({
      page,
      page_size: 20,
      purchase_order_number: search || undefined,
      status: status || undefined,
      supplier_id: supplierId || undefined,
      date_from: dateFrom ? `${dateFrom}T00:00:00Z` : undefined,
      date_to: dateTo ? `${dateTo}T23:59:59Z` : undefined,
    }),
  });
  const suppliersQuery = useQuery({ queryKey: ["suppliers"], queryFn: () => listSuppliers({ page_size: 100 }) });
  const branchesQuery = useQuery({ queryKey: ["branches"], queryFn: () => listBranches() });
  const productsQuery = useQuery({ queryKey: ["products"], queryFn: () => listProducts({ page_size: 100 }) });
  const detailQuery = useQuery({ queryKey: ["purchase-order", detailId], queryFn: () => getPurchaseOrder(detailId as string), enabled: !!detailId });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["purchase-orders"] });
    queryClient.invalidateQueries({ queryKey: ["purchase-order"] });
    queryClient.invalidateQueries({ queryKey: ["inventory"] });
    queryClient.invalidateQueries({ queryKey: ["analytics-dashboard"] });
  };
  const createMutation = useMutation({ mutationFn: (payload: PurchaseOrderCreate) => createPurchaseOrder(payload), onSuccess: () => { invalidate(); closeForm(); }, onError: (error: Error) => setFormError(error.message) });
  const updateMutation = useMutation({ mutationFn: ({ id, payload }: { id: string; payload: PurchaseOrderCreate }) => updatePurchaseOrder(id, payload), onSuccess: () => { invalidate(); closeForm(); }, onError: (error: Error) => setFormError(error.message) });
  const submitMutation = useMutation({ mutationFn: submitPurchaseOrder, onSuccess: () => { invalidate(); setConfirmAction(null); } });
  const approveMutation = useMutation({ mutationFn: approvePurchaseOrder, onSuccess: () => { invalidate(); setConfirmAction(null); } });
  const cancelMutation = useMutation({ mutationFn: cancelPurchaseOrder, onSuccess: () => { invalidate(); setConfirmAction(null); } });
  const receiveMutation = useMutation({ mutationFn: ({ id, payload }: { id: string; payload: ReceivePurchaseOrder }) => receivePurchaseOrder(id, payload), onSuccess: () => { invalidate(); setReceiveOrder(null); setReceiveError(""); }, onError: (error: Error) => setReceiveError(error.message) });

  const suppliers = suppliersQuery.data ?? [];
  const branches = branchesQuery.data ?? [];
  const products = productsQuery.data ?? [];
  const orders = ordersQuery.data ?? [];
  const supplierMap = new Map(suppliers.map((supplier) => [supplier.id, supplier.name]));
  const branchMap = new Map(branches.map((branch) => [branch.id, branch.name]));
  const productMap = new Map(products.map((product) => [product.id, product]));
  const formSubtotal = formItems.reduce((total, item) => total + Number(item.quantity || 0) * Number(item.unit_cost || 0), 0);
  const formTotal = formSubtotal + Number(formTax || 0) - Number(formDiscount || 0);

  function closeForm() {
    setFormOpen(false);
    setEditingOrder(null);
    setFormError("");
  }
  function openCreate() {
    setEditingOrder(null);
    setFormSupplierId(suppliers[0]?.id ?? "");
    setFormBranchId(branches[0]?.id ?? "");
    setFormExpectedDate("");
    setFormNotes("");
    setFormTax("0");
    setFormDiscount("0");
    setFormItems(products[0] ? [{ product_id: products[0].id, quantity: "1", unit_cost: String(products[0].cost_price) }] : []);
    setFormError("");
    setFormOpen(true);
  }
  function openEdit(order: PurchaseOrder) {
    setEditingOrder(order);
    setFormSupplierId(order.supplier_id);
    setFormBranchId(order.branch_id);
    setFormExpectedDate(order.expected_delivery_date?.slice(0, 10) ?? "");
    setFormNotes(order.notes ?? "");
    setFormTax(String(order.tax));
    setFormDiscount(String(order.discount));
    setFormItems(order.items.map((item) => ({ product_id: item.product_id, quantity: String(item.quantity), unit_cost: String(item.unit_cost) })));
    setFormError("");
    setFormOpen(true);
  }
  function addItem() {
    if (products[0]) setFormItems((items) => [...items, { product_id: products[0].id, quantity: "1", unit_cost: String(products[0].cost_price) }]);
  }
  function changeItem(index: number, field: keyof FormItem, value: string) {
    setFormItems((items) => items.map((item, itemIndex) => {
      if (itemIndex !== index) return item;
      if (field === "product_id") {
        const product = products.find((entry) => entry.id === value);
        return { ...item, product_id: value, unit_cost: product ? String(product.cost_price) : item.unit_cost };
      }
      return { ...item, [field]: value };
    }));
  }
  function submitForm(event: React.FormEvent) {
    event.preventDefault();
    setFormError("");
    if (!formSupplierId || !formBranchId || formItems.length === 0) { setFormError("Supplier, branch, and at least one product are required."); return; }
    if (formItems.some((item) => Number(item.quantity) <= 0 || Number(item.unit_cost) < 0)) { setFormError("Quantities must be greater than zero and unit costs cannot be negative."); return; }
    const payload: PurchaseOrderCreate = { supplier_id: formSupplierId, branch_id: formBranchId, expected_delivery_date: formExpectedDate ? `${formExpectedDate}T23:59:59Z` : undefined, tax: Number(formTax || 0), discount: Number(formDiscount || 0), notes: formNotes || undefined, items: formItems.map((item) => ({ product_id: item.product_id, quantity: Number(item.quantity), unit_cost: Number(item.unit_cost) })) };
    if (editingOrder) updateMutation.mutate({ id: editingOrder.id, payload }); else createMutation.mutate(payload);
  }
  function openReceive(order: PurchaseOrder) {
    setReceiveOrder(order);
    setReceiveReference("");
    setReceiveItems(Object.fromEntries(order.items.map((item) => [item.id, "0"])));
    setReceiveError("");
  }
  function submitReceive(event: React.FormEvent) {
    event.preventDefault();
    if (!receiveOrder || !receiveReference.trim()) { setReceiveError("Receipt reference is required."); return; }
    const items = receiveOrder.items.map((item) => ({ item_id: item.id, quantity: Number(receiveItems[item.id] || 0) })).filter((item) => item.quantity > 0);
    if (!items.length) { setReceiveError("Enter a quantity for at least one item."); return; }
    receiveMutation.mutate({ id: receiveOrder.id, payload: { receipt_reference: receiveReference.trim(), items } });
  }
  function actionLabel(action: "submit" | "approve" | "cancel") { return action === "submit" ? "Submit" : action === "approve" ? "Approve" : "Cancel"; }

  return (
    <AppShell>
      <div className="mx-auto w-full max-w-7xl space-y-6 px-4 py-6 sm:px-6 lg:px-8">
        <header className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"><div><p className="text-xs font-semibold uppercase tracking-wider text-primary">Procurement & Inventory</p><h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-950 sm:text-3xl">Purchase Orders</h1><p className="mt-1 text-xs text-slate-500">Create, approve, and receive supplier orders into branch inventory.</p></div><div className="flex items-center gap-2"><button type="button" onClick={() => ordersQuery.refetch()} className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-white px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"><RefreshCw className="h-3.5 w-3.5" /> Refresh</button><button type="button" onClick={openCreate} className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3.5 py-2 text-xs font-semibold text-white hover:opacity-90"><Plus className="h-4 w-4" /> Create Purchase Order</button></div></header>

        <section className="flex flex-col gap-3 rounded-xl border border-border bg-white p-4 shadow-sm lg:flex-row lg:items-center"><div className="relative flex-1"><Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" /><input value={search} onChange={(event) => { setSearch(event.target.value); setPage(1); }} placeholder="Search purchase order number..." className="w-full rounded-lg border border-border bg-slate-50 py-2 pl-9 pr-3 text-xs outline-none focus:border-primary" /></div><Filter className="hidden h-4 w-4 text-slate-400 lg:block" /><select value={status} onChange={(event) => { setStatus(event.target.value); setPage(1); }} className="rounded-lg border border-border bg-white px-3 py-2 text-xs text-slate-700"><option value="">All statuses</option>{statuses.map((value) => <option key={value} value={value}>{value}</option>)}</select><select value={supplierId} onChange={(event) => { setSupplierId(event.target.value); setPage(1); }} className="rounded-lg border border-border bg-white px-3 py-2 text-xs text-slate-700"><option value="">All suppliers</option>{suppliers.map((supplier) => <option key={supplier.id} value={supplier.id}>{supplier.name}</option>)}</select><input type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} className="rounded-lg border border-border px-3 py-2 text-xs text-slate-700" /><input type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)} className="rounded-lg border border-border px-3 py-2 text-xs text-slate-700" /></section>

        <section className="overflow-hidden rounded-xl border border-border bg-white shadow-sm">{ordersQuery.isLoading ? <LoadingSpinner message="Loading purchase orders..." /> : ordersQuery.isError ? <ErrorStateView message={ordersQuery.error instanceof Error ? ordersQuery.error.message : "Unable to load purchase orders."} onRetry={() => ordersQuery.refetch()} /> : orders.length === 0 ? <EmptyStateView title="No purchase orders found" message="Create a purchase order to connect supplier purchasing with inventory receiving." /> : <div className="overflow-x-auto"><table className="w-full text-left text-xs"><thead className="border-b border-border bg-slate-50 text-[10px] uppercase tracking-wider text-slate-500"><tr><th className="px-4 py-3">PO Number</th><th className="px-4 py-3">Supplier</th><th className="px-4 py-3">Branch</th><th className="px-4 py-3">Order Date</th><th className="px-4 py-3">Expected</th><th className="px-4 py-3">Status</th><th className="px-4 py-3 text-right">Total</th><th className="px-4 py-3 text-right">Actions</th></tr></thead><tbody className="divide-y divide-border">{orders.map((order) => <tr key={order.id} className="hover:bg-slate-50"><td className="px-4 py-3 font-semibold text-slate-900">{order.purchase_order_number}</td><td className="px-4 py-3">{supplierMap.get(order.supplier_id) ?? "Supplier"}</td><td className="px-4 py-3">{branchMap.get(order.branch_id) ?? "Branch"}</td><td className="px-4 py-3">{new Date(order.order_date).toLocaleDateString()}</td><td className="px-4 py-3">{order.expected_delivery_date ? new Date(order.expected_delivery_date).toLocaleDateString() : "-"}</td><td className="px-4 py-3"><StatusBadge status={order.status} /></td><td className="px-4 py-3 text-right font-semibold">{formatCurrency(order.total)}</td><td className="px-4 py-3"><div className="flex justify-end gap-1"><button type="button" title="View details" onClick={() => setDetailId(order.id)} className="rounded p-1.5 text-slate-500 hover:bg-slate-100"><Eye className="h-4 w-4" /></button>{order.status === "DRAFT" && <><button type="button" title="Edit draft" onClick={() => openEdit(order)} className="rounded p-1.5 text-slate-500 hover:bg-slate-100"><FilePlus className="h-4 w-4" /></button><button type="button" title="Submit" onClick={() => setConfirmAction({ order, action: "submit" })} className="rounded p-1.5 text-primary hover:bg-primary/10"><Send className="h-4 w-4" /></button></>}{order.status === "SUBMITTED" && <button type="button" title="Approve" onClick={() => setConfirmAction({ order, action: "approve" })} className="rounded p-1.5 text-emerald-600 hover:bg-emerald-50"><Check className="h-4 w-4" /></button>}{(order.status === "APPROVED" || order.status === "PARTIALLY_RECEIVED") && <button type="button" title="Receive stock" onClick={() => openReceive(order)} className="rounded p-1.5 text-teal-600 hover:bg-teal-50"><Truck className="h-4 w-4" /></button>}{(order.status === "DRAFT" || order.status === "SUBMITTED" || order.status === "APPROVED") && <button type="button" title="Cancel" onClick={() => setConfirmAction({ order, action: "cancel" })} className="rounded p-1.5 text-rose-500 hover:bg-rose-50"><XCircle className="h-4 w-4" /></button>}</div></td></tr>)}</tbody></table></div>}{<div className="flex items-center justify-between border-t border-border px-4 py-3 text-xs text-slate-500"><span>Page {page}</span><div className="flex gap-2"><button type="button" disabled={page === 1} onClick={() => setPage((value) => Math.max(1, value - 1))} className="rounded-lg border border-border px-3 py-1.5 disabled:opacity-40">Previous</button><button type="button" disabled={orders.length < 20} onClick={() => setPage((value) => value + 1)} className="rounded-lg border border-border px-3 py-1.5 disabled:opacity-40">Next</button></div></div>}</section>

        <Modal isOpen={formOpen} onClose={closeForm} title={editingOrder ? "Edit Draft Purchase Order" : "Create Purchase Order"} description="Totals are recalculated by the NEXUS backend before saving." maxWidth="xl"><form onSubmit={submitForm} className="space-y-4 text-xs">{formError && <ErrorBanner message={formError} />}<div className="grid gap-3 sm:grid-cols-2"><Field label="Supplier"><select value={formSupplierId} onChange={(event) => setFormSupplierId(event.target.value)} className="input"><option value="">Select supplier</option>{suppliers.map((supplier) => <option key={supplier.id} value={supplier.id}>{supplier.name}</option>)}</select></Field><Field label="Receiving branch"><select value={formBranchId} onChange={(event) => setFormBranchId(event.target.value)} className="input"><option value="">Select branch</option>{branches.map((branch) => <option key={branch.id} value={branch.id}>{branch.name}</option>)}</select></Field><Field label="Expected delivery"><input type="date" value={formExpectedDate} onChange={(event) => setFormExpectedDate(event.target.value)} className="input" /></Field><Field label="Notes"><input value={formNotes} onChange={(event) => setFormNotes(event.target.value)} className="input" placeholder="Optional purchasing notes" /></Field></div><div className="overflow-x-auto rounded-lg border border-border"><table className="w-full min-w-[560px] text-left"><thead className="bg-slate-50 text-[10px] uppercase text-slate-500"><tr><th className="px-3 py-2">Product</th><th className="px-3 py-2">Quantity</th><th className="px-3 py-2">Unit cost</th><th className="px-3 py-2">Subtotal</th><th /></tr></thead><tbody className="divide-y divide-border">{formItems.map((item, index) => <tr key={`${item.product_id}-${index}`}><td className="px-3 py-2"><select value={item.product_id} onChange={(event) => changeItem(index, "product_id", event.target.value)} className="input"><option value="">Select product</option>{products.map((product) => <option key={product.id} value={product.id}>{product.name} ({product.sku})</option>)}</select></td><td className="px-3 py-2"><input type="number" min="0.0001" step="0.0001" value={item.quantity} onChange={(event) => changeItem(index, "quantity", event.target.value)} className="input w-24" /></td><td className="px-3 py-2"><input type="number" min="0" step="0.01" value={item.unit_cost} onChange={(event) => changeItem(index, "unit_cost", event.target.value)} className="input w-28" /></td><td className="px-3 py-2 font-semibold">{formatCurrency(Number(item.quantity || 0) * Number(item.unit_cost || 0))}</td><td className="px-3 py-2"><button type="button" onClick={() => setFormItems((items) => items.filter((_, itemIndex) => itemIndex !== index))} className="text-rose-500">Remove</button></td></tr>)}</tbody></table></div><button type="button" onClick={addItem} className="inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-2 font-semibold text-slate-700 hover:bg-slate-50"><Plus className="h-3.5 w-3.5" /> Add product</button><div className="grid gap-3 sm:grid-cols-3"><Field label="Subtotal"><p className="input bg-slate-50">{formatCurrency(formSubtotal)}</p></Field><Field label="Tax"><input type="number" min="0" step="0.01" value={formTax} onChange={(event) => setFormTax(event.target.value)} className="input" /></Field><Field label="Discount"><input type="number" min="0" step="0.01" value={formDiscount} onChange={(event) => setFormDiscount(event.target.value)} className="input" /></Field></div><div className="flex items-center justify-between border-t border-border pt-4"><strong className="text-sm text-slate-950">Preview total: {formatCurrency(formTotal)}</strong><div className="flex gap-2"><button type="button" onClick={closeForm} className="rounded-lg border border-border px-4 py-2 font-semibold">Cancel</button><button type="submit" disabled={createMutation.isPending || updateMutation.isPending} className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 font-semibold text-white disabled:opacity-50">{(createMutation.isPending || updateMutation.isPending) && <Loader2 className="h-3.5 w-3.5 animate-spin" />} Save Draft</button></div></div></form></Modal>

        <Modal isOpen={!!detailId} onClose={() => setDetailId(null)} title={detailQuery.data?.purchase_order_number ?? "Purchase Order Details"} description="Purchase order history and receiving status." maxWidth="lg">{detailQuery.isLoading ? <LoadingSpinner message="Loading details..." /> : detailQuery.data ? <div className="space-y-4 text-xs"><div className="grid grid-cols-2 gap-3 rounded-lg bg-slate-50 p-4"><p><span className="text-slate-500">Supplier</span><br /><strong>{supplierMap.get(detailQuery.data.supplier_id) ?? "Supplier"}</strong></p><p><span className="text-slate-500">Branch</span><br /><strong>{branchMap.get(detailQuery.data.branch_id) ?? "Branch"}</strong></p><p><span className="text-slate-500">Status</span><br /><StatusBadge status={detailQuery.data.status} /></p><p><span className="text-slate-500">Total</span><br /><strong>{formatCurrency(detailQuery.data.total)}</strong></p></div><div className="divide-y divide-border rounded-lg border border-border">{detailQuery.data.items.map((item) => <div key={item.id} className="flex items-center justify-between px-3 py-3"><span>{productMap.get(item.product_id)?.name ?? "Product"}</span><span>{item.received_quantity} / {item.quantity} received</span><strong>{formatCurrency(item.subtotal)}</strong></div>)}</div></div> : <ErrorStateView message="Unable to load purchase order details." />}</Modal>

        <Modal isOpen={!!receiveOrder} onClose={() => setReceiveOrder(null)} title="Receive Purchased Stock" description="Enter only the quantities received on this receipt." maxWidth="lg"><form onSubmit={submitReceive} className="space-y-4 text-xs">{receiveError && <ErrorBanner message={receiveError} />}<Field label="Receipt reference"><input required value={receiveReference} onChange={(event) => setReceiveReference(event.target.value)} className="input" placeholder="GRN-2026-001" /></Field><div className="space-y-2">{receiveOrder?.items.map((item) => { const remaining = Number(item.quantity) - Number(item.received_quantity); return <div key={item.id} className="grid grid-cols-[1fr_auto_auto] items-center gap-3 rounded-lg border border-border p-3"><span>{productMap.get(item.product_id)?.name ?? "Product"}</span><span className="text-slate-500">{item.received_quantity} received / {remaining} remaining</span><input type="number" min="0" max={remaining} step="0.0001" value={receiveItems[item.id] ?? "0"} onChange={(event) => setReceiveItems((values) => ({ ...values, [item.id]: event.target.value }))} className="input w-28" /></div>; })}</div><div className="flex justify-end gap-2"><button type="button" onClick={() => setReceiveOrder(null)} className="rounded-lg border border-border px-4 py-2 font-semibold">Cancel</button><button type="submit" disabled={receiveMutation.isPending} className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 font-semibold text-white disabled:opacity-50">{receiveMutation.isPending && <Loader2 className="h-3.5 w-3.5 animate-spin" />} Receive Stock</button></div></form></Modal>

        <ConfirmDialog isOpen={!!confirmAction} onClose={() => setConfirmAction(null)} title={`${actionLabel(confirmAction?.action ?? "submit")} Purchase Order`} message={`Are you sure you want to ${actionLabel(confirmAction?.action ?? "submit").toLowerCase()} ${confirmAction?.order.purchase_order_number ?? "this purchase order"}?`} confirmText={actionLabel(confirmAction?.action ?? "submit")} cancelText="Keep Order" variant={confirmAction?.action === "cancel" ? "danger" : "primary"} onConfirm={() => { if (!confirmAction) return; if (confirmAction.action === "submit") submitMutation.mutate(confirmAction.order.id); if (confirmAction.action === "approve") approveMutation.mutate(confirmAction.order.id); if (confirmAction.action === "cancel") cancelMutation.mutate(confirmAction.order.id); }} isLoading={submitMutation.isPending || approveMutation.isPending || cancelMutation.isPending} />
      </div>
      <style jsx>{`.input { width: 100%; border: 1px solid rgb(226 232 240); border-radius: 0.5rem; background: white; padding: 0.5rem 0.75rem; color: rgb(51 65 85); outline: none; } .input:focus { border-color: hsl(var(--primary)); }`}</style>
    </AppShell>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return <label className="block space-y-1"><span className="font-semibold text-slate-700">{label}</span>{children}</label>;
}

function ErrorBanner({ message }: { message: string }) {
  return <div className="flex items-start gap-2 rounded-lg bg-rose-50 p-3 text-rose-700"><AlertCircle className="mt-0.5 h-4 w-4 shrink-0" /><span>{message}</span></div>;
}
