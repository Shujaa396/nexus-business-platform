"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { ArrowLeft, Loader2 } from "lucide-react";
import AppShell from "../../../../components/app-shell";
import { ErrorStateView, EmptyStateView } from "../../../../components/ui/state-views";
import { getPortalInvoice } from "../../../../lib/customers";

export default function PortalInvoicePage() {
  const { id } = useParams<{ id: string }>();
  const query = useQuery({ queryKey: ["portal-invoice", id], queryFn: () => getPortalInvoice(id), enabled: Boolean(id) });
  if (query.isLoading) return <AppShell><div className="flex min-h-[60vh] items-center justify-center"><Loader2 className="h-7 w-7 animate-spin text-primary" /></div></AppShell>;
  if (query.isError || !query.data) return <AppShell><div className="mx-auto max-w-5xl px-6 py-8"><ErrorStateView message="Unable to load this invoice." onRetry={() => query.refetch()} /></div></AppShell>;
  const invoice = query.data.invoice;
  return <AppShell><main className="mx-auto max-w-5xl space-y-6 px-4 py-6 sm:px-6"><Link href="/customer-portal" className="inline-flex items-center gap-2 text-sm text-slate-500"><ArrowLeft className="h-4 w-4" /> Portal</Link><header><p className="text-xs font-semibold uppercase tracking-wider text-primary">Invoice detail</p><h1 className="mt-1 text-3xl font-bold text-slate-950">{invoice.invoice_number}</h1><p className="mt-1 text-sm text-slate-500">{invoice.status} · Issued {invoice.issued_date ? new Date(invoice.issued_date).toLocaleDateString() : "Not issued"}</p></header><section className="rounded-xl border border-border bg-white p-5 shadow-sm"><h2 className="font-semibold">Line items</h2>{invoice.line_items?.length ? <div className="mt-3 divide-y divide-border">{invoice.line_items.map((item) => <div key={item.id} className="flex justify-between py-3 text-sm"><span>{item.product_name}<span className="ml-2 text-xs text-slate-500">{item.quantity}</span></span><strong>${item.line_total}</strong></div>)}</div> : <EmptyStateView title="No line items" message="This invoice has no visible line items." />}<div className="mt-5 space-y-1 border-t border-border pt-4 text-right text-sm"><p>Subtotal: ${invoice.subtotal}</p><p>Tax: ${invoice.tax}</p><p>Discount: ${invoice.discount}</p><p>Paid: ${invoice.amount_paid}</p><p className="text-base font-bold">Outstanding: ${(Number(invoice.total) - Number(invoice.amount_paid)).toFixed(2)}</p></div></section><section className="rounded-xl border border-border bg-white p-5 shadow-sm"><h2 className="font-semibold">Payments</h2>{query.data.payments.length ? query.data.payments.map((payment) => <div key={payment.id} className="flex justify-between border-b border-border py-3 text-sm"><span>{payment.order_number} · {payment.payment_method} · {payment.status}</span><strong>${payment.amount}</strong></div>) : <EmptyStateView title="No payments" message="No payments recorded." />}</section></main></AppShell>;
}