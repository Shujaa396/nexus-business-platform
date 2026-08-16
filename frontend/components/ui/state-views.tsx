import React from "react";
import { AlertCircle, Inbox, RefreshCw } from "lucide-react";

export function LoadingSpinner({
  message = "Loading...",
  className = "",
}: {
  message?: string;
  className?: string;
}) {
  return (
    <div
      className={`flex flex-col items-center justify-center p-8 text-center ${className}`}
    >
      <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      {message && (
        <p className="mt-3 text-xs font-medium text-slate-500">{message}</p>
      )}
    </div>
  );
}

export function LoadingSkeleton({
  count = 3,
  className = "",
}: {
  count?: number;
  className?: string;
}) {
  return (
    <div className={`space-y-3 ${className}`}>
      {Array.from({ length: count }).map((_, index) => (
        <div
          key={index}
          className="h-12 w-full animate-pulse rounded-lg bg-slate-100"
        />
      ))}
    </div>
  );
}

export function ErrorStateView({
  message = "Unable to load data.",
  onRetry,
  className = "",
}: {
  message?: string;
  onRetry?: () => void;
  className?: string;
}) {
  return (
    <div
      className={`flex flex-col items-center justify-center p-6 text-center ${className}`}
    >
      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-red-50 text-red-600">
        <AlertCircle className="h-5 w-5" />
      </div>
      <p className="mt-2 text-sm font-medium text-slate-800">{message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-3 inline-flex items-center gap-1.5 rounded-lg border border-border bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50 hover:text-slate-900"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Retry
        </button>
      )}
    </div>
  );
}

export function EmptyStateView({
  title = "No data available",
  message = "There is no information to display at this time.",
  className = "",
}: {
  title?: string;
  message?: string;
  className?: string;
}) {
  return (
    <div
      className={`flex flex-col items-center justify-center p-8 text-center ${className}`}
    >
      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-100 text-slate-400">
        <Inbox className="h-5 w-5" />
      </div>
      <p className="mt-2 text-sm font-medium text-slate-700">{title}</p>
      <p className="mt-1 text-xs text-slate-400 max-w-xs">{message}</p>
    </div>
  );
}
