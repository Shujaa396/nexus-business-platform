"use client";

import { useQuery } from "@tanstack/react-query";
import { FileText, Loader2, ShoppingCart, Wallet, type LucideIcon } from "lucide-react";

import AppShell from "../../components/app-shell";
import { ErrorStateView, EmptyStateView } from "../../components/ui/state-views";
import { getCustomerPortal } from "../../lib/customers";
import Link from "next/link";

export default function CustomerPortalPage() {
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["customer-portal"],
    queryFn: getCustomerPortal,
  });

  if (isLoading) {
    return <AppShell><div className="flex min-h-[60vh] items-center justify-center"><Loader2 className="h-7 w-7 animate-spin text-primary" /></div></AppShell>;
  }
  if (isError || !data) {
    return <AppShell><div className="mx-auto max-w-5xl px-6 py-8"><ErrorStateView message={error instanceof Error ? error.message : "Unable to load your account."} onRetry={() => refetch()} /></div></AppShell>;
  }

  const { customer, summary } = data;
  const metrics: Array<{ icon: LucideIcon; label: string; value: number | string }> = [
    { icon: ShoppingCart, label: "Orders", value: summary.order_count },
    { icon: FileText, label: "Invoices", value: summary.invoice_count },
    { icon: Wallet, label: "Paid", value: `$${summary.paid_total}` },
    { icon: Wallet, label: "Outstanding", value: `$${summary.outstanding_balance}` },
  ];
  return (
    <AppShell>
      <main className="mx-auto w-full max-w-6xl space-y-6 px-4 py-6 sm:px-6 lg:px-8">
        <header>
          <p className="text-xs font-semibold uppercase tracking-wider text-primary">Customer portal</p>
          <h1 className="mt-1 text-3xl font-bold tracking-tight text-slate-950">{customer.company_name || customer.name}</h1>
          <p className="mt-1 text-sm text-slate-500">{customer.email || "Account overview"}</p>
        </header>

        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {metrics.map(({ icon: Icon, label, value }) => <div key={label} className="rounded-xl border border-border bg-white p-5 shadow-sm"><Icon className="h-5 w-5 text-primary" /><p className="mt-4 text-xs font-medium uppercase tracking-wider text-slate-500">{label}</p><p className="mt-1 text-2xl font-bold text-slate-950">{value}</p></div>)}
        </section>

        <section className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-xl border border-border bg-white p-5 shadow-sm"><h2 className="text-base font-semibold text-slate-950">Recent orders</h2>{data.orders.length === 0 ? <EmptyStateView title="No orders yet" message="Your order history will appear here." /> : <div className="mt-4 divide-y divide-border">{data.orders.slice(0, 8).map((order) => <Link href={`/customer-portal/orders/${order.id}`} key={order.id} className="flex items-center justify-between py-3 text-sm hover:bg-slate-50"><div><p className="font-medium text-slate-900">{order.order_number}</p><p className="text-xs text-slate-500">{order.status} · {order.payment_status}</p></div><span className="font-semibold text-slate-900">${order.total}</span></Link>)}</div>}</div>
          <div className="rounded-xl border border-border bg-white p-5 shadow-sm"><h2 className="text-base font-semibold text-slate-950">Invoices</h2>{data.invoices.length === 0 ? <EmptyStateView title="No invoices yet" message="Your invoices will appear here." /> : <div className="mt-4 divide-y divide-border">{data.invoices.slice(0, 8).map((invoice) => <Link href={`/customer-portal/invoices/${invoice.id}`} key={invoice.id} className="flex items-center justify-between py-3 text-sm hover:bg-slate-50"><div><p className="font-medium text-slate-900">{invoice.invoice_number}</p><p className="text-xs text-slate-500">{invoice.status}</p></div><span className="font-semibold text-slate-900">${invoice.amount_paid} / ${invoice.total}</span></Link>)}</div>}</div>
        </section>
        <section className="grid gap-6 lg:grid-cols-3">
          <div className="rounded-xl border border-border bg-white p-5 shadow-sm"><h2 className="font-semibold text-slate-950">Contacts</h2>{data.contacts.length ? <div className="mt-3 divide-y divide-border">{data.contacts.map((contact) => <div key={contact.id} className="py-3 text-sm"><p className="font-medium">{contact.name}{contact.is_primary ? " · Primary" : ""}</p><p className="text-xs text-slate-500">{contact.job_title || contact.email || contact.phone || "No contact details"}</p></div>)}</div> : <EmptyStateView title="No contacts" message="No contacts are available." />}</div>
          <div className="rounded-xl border border-border bg-white p-5 shadow-sm"><h2 className="font-semibold text-slate-950">Addresses</h2>{data.addresses.length ? <div className="mt-3 divide-y divide-border">{data.addresses.map((address) => <div key={address.id} className="py-3 text-sm"><p className="font-medium">{address.address_type}{address.is_primary ? " · Primary" : ""}</p><p className="text-xs text-slate-500">{address.line1}, {address.city || address.country || ""}</p></div>)}</div> : <EmptyStateView title="No addresses" message="No addresses are available." />}</div>
          <div className="rounded-xl border border-border bg-white p-5 shadow-sm"><h2 className="font-semibold text-slate-950">Payment history</h2>{data.payments.length ? <div className="mt-3 divide-y divide-border">{data.payments.map((payment) => <div key={payment.id} className="flex justify-between py-3 text-sm"><div><p className="font-medium">{payment.payment_method} · {payment.order_number}</p><p className="text-xs text-slate-500">{payment.invoice_number ? `Invoice ${payment.invoice_number} · ` : "Order payment · "}{new Date(payment.created_at).toLocaleDateString()} · {payment.status}</p></div><strong>${payment.amount}</strong></div>)}</div> : <EmptyStateView title="No payments" message="No payments are available." />}</div>
        </section>
      </main>
    </AppShell>
  );
}