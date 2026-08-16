import React from "react";

export function StatusBadge({ status }: { status: string }) {
  const normalized = status.toUpperCase();

  const styles: Record<string, string> = {
    // Orders & Invoices & Payments
    COMPLETED: "bg-emerald-50 text-emerald-700 border-emerald-200",
    PAID: "bg-emerald-50 text-emerald-700 border-emerald-200",
    CONFIRMED: "bg-teal-50 text-teal-700 border-teal-200",
    ISSUED: "bg-blue-50 text-blue-700 border-blue-200",
    PARTIAL: "bg-amber-50 text-amber-700 border-amber-200",
    DRAFT: "bg-slate-100 text-slate-700 border-slate-200",
    UNPAID: "bg-amber-50 text-amber-700 border-amber-200",
    CANCELLED: "bg-rose-50 text-rose-700 border-rose-200",
    VOID: "bg-rose-50 text-rose-700 border-rose-200",
    REFUNDED: "bg-purple-50 text-purple-700 border-purple-200",
    ACTIVE: "bg-emerald-50 text-emerald-700 border-emerald-200",
    INACTIVE: "bg-slate-100 text-slate-500 border-slate-200",
  };

  const style =
    styles[normalized] || "bg-slate-100 text-slate-700 border-slate-200";

  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-[11px] font-semibold tracking-tight ${style}`}
    >
      {status}
    </span>
  );
}
