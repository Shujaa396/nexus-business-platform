import React from "react";
import { LucideIcon } from "lucide-react";

export function formatCurrency(value: string | number | undefined | null): string {
  if (value === undefined || value === null) return "Rs. 0.00";
  const num = typeof value === "string" ? parseFloat(value) : value;
  if (isNaN(num)) return "Rs. 0.00";
  return `Rs. ${num.toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

export function formatNumber(value: number | undefined | null): string {
  if (value === undefined || value === null) return "0";
  return value.toLocaleString("en-US");
}

type StatCardProps = {
  label: string;
  value: string | number;
  description?: string;
  icon?: LucideIcon;
  badge?: string;
  badgeType?: "default" | "success" | "warning" | "danger" | "accent";
  isLoading?: boolean;
};

export function StatCard({
  label,
  value,
  description,
  icon: Icon,
  badge,
  badgeType = "default",
  isLoading = false,
}: StatCardProps) {
  if (isLoading) {
    return (
      <article className="rounded-xl border border-border bg-white p-5 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="h-4 w-24 animate-pulse rounded bg-slate-100" />
          <div className="h-8 w-8 animate-pulse rounded-lg bg-slate-100" />
        </div>
        <div className="mt-3 h-8 w-32 animate-pulse rounded bg-slate-200" />
        <div className="mt-2 h-3 w-20 animate-pulse rounded bg-slate-100" />
      </article>
    );
  }

  const badgeStyles = {
    default: "bg-slate-100 text-slate-700",
    success: "bg-emerald-50 text-emerald-700 border-emerald-200",
    warning: "bg-amber-50 text-amber-700 border-amber-200",
    danger: "bg-rose-50 text-rose-700 border-rose-200",
    accent: "bg-teal-50 text-teal-700 border-teal-200",
  };

  return (
    <article className="group relative overflow-hidden rounded-xl border border-border bg-white p-5 shadow-sm transition hover:shadow-md">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-slate-500">{label}</p>
        {Icon && (
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-50 text-slate-600 transition group-hover:bg-primary/10 group-hover:text-primary">
            <Icon className="h-4 w-4" />
          </div>
        )}
      </div>

      <div className="mt-3 flex items-baseline gap-2">
        <p className="text-2xl font-bold tracking-tight text-slate-950">
          {value}
        </p>
        {badge && (
          <span
            className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold ${badgeStyles[badgeType]}`}
          >
            {badge}
          </span>
        )}
      </div>

      {description && (
        <p className="mt-1 text-xs text-slate-400">{description}</p>
      )}
    </article>
  );
}
