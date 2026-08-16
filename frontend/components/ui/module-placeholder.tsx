import React from "react";
import Link from "next/link";
import { ArrowLeft, LucideIcon } from "lucide-react";

type ModulePlaceholderProps = {
  category: string;
  title: string;
  description: string;
  icon: LucideIcon;
  details: string;
};

export function ModulePlaceholder({
  category,
  title,
  description,
  icon: Icon,
  details,
}: ModulePlaceholderProps) {
  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8 space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-primary">
            {category}
          </p>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-950 sm:text-3xl">
            {title}
          </h1>
          <p className="mt-1 text-xs text-slate-500">{description}</p>
        </div>

        <Link
          href="/dashboard"
          className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-white px-3.5 py-2 text-xs font-medium text-slate-700 shadow-sm transition hover:bg-slate-50 hover:text-slate-900 self-start sm:self-auto"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back to Dashboard
        </Link>
      </div>

      <div className="flex flex-col items-center justify-center rounded-xl border border-border bg-white p-12 sm:p-16 text-center shadow-sm">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 text-primary shadow-inner">
          <Icon className="h-7 w-7" />
        </div>
        <h2 className="mt-5 text-lg font-semibold text-slate-900">
          {title} Module
        </h2>
        <p className="mt-2 text-xs leading-relaxed text-slate-500 max-w-md">
          {details}
        </p>
        <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-xs font-semibold text-white shadow-sm transition hover:opacity-90"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Go to Executive Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
