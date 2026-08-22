"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { ArrowLeft, Loader2 } from "lucide-react";
import AppShell from "../../../../components/app-shell";
import { ErrorStateView, EmptyStateView } from "../../../../components/ui/state-views";
import { getPortalOrder } from "../../../../lib/customers";

export default function PortalOrderPage() {
  const { id } = useParams<{ id: string }>();
  const query = useQuery({ queryKey: ["portal-order", id], queryFn: () => getPortalOrder(id), enabled: Boolean(id) });
  if (query.isLoading) return <AppShell><div className="flex min-h-[60vh] items-center justify-center"><Loader2 className="h-7 w-7 animate-spin text-primary" /></div></AppShell>;
  if (query.isError || !query.data) return <AppShell><div className="mx-auto max-w-5xl px-6 py-8"><ErrorStateView message="Unable to load this order." onRetry={() => query.refetch()} /></div></AppShell>;
  const order = query.data;
  return <AppShell><main className="mx-auto max-w-5xl space-y-6 px-4 py-6 sm:px-6"><Link href="/customer-portal" className="inline-flex items-center gap-2 text-sm text-slate-500"><ArrowLeft className="h-4 w-4" /> Portal</Link><header><p className="text-xs font-semibold uppercase tracking-wider text-primary">Order detail</p><h1 className="mt-1 text-3xl font-bold text-slate-950">{order.order_number}</h1><p className="mt-1 text-sm text-slate-500">{order.status} · {order.payment_status} · {new Date(order.created_at).toLocaleDateString()}</p></header><section className="rounded-xl border border-border bg-white p-5 shadow-sm"><h2 className="font-semibold">Line items</h2>{order.items?.length ? <div className="mt-3 divide-y divide-border">{order.items.map((item) => <div key={item.id} className="flex justify-between py-3 text-sm"><span>{item.product_name || item.product_sku || `Product ${item.product_id}`}<span className="ml-2 text-xs text-slate-500">{item.quantity} ordered · {item.fulfilled_quantity || "0"} fulfilled</span></span><strong>${item.line_total}</strong></div>)}</div> : <EmptyStateView title="No line items" message="This order has no visible line items." />}<div className="mt-5 space-y-1 border-t border-border pt-4 text-right text-sm"><p>Subtotal: ${order.subtotal}</p><p>Tax: ${order.tax}</p><p>Discount: ${order.discount}</p><p className="text-base font-bold">Total: ${order.total}</p></div></section></main></AppShell>;
}