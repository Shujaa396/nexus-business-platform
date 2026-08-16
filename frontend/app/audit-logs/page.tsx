"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Clock,
  Download,
  Filter,
  RefreshCw,
  Search,
  Shield,
  User,
} from "lucide-react";

import AppShell from "../../components/app-shell";
import {
  EmptyStateView,
  ErrorStateView,
  LoadingSpinner,
} from "../../components/ui/state-views";
import { listAuditLogs } from "../../lib/audit";
import { exportToCSV } from "../../lib/export";
import type { AuditLog } from "../../types/audit";

export default function AuditLogsPage() {
  const [selectedEntity, setSelectedEntity] = useState<string>("");
  const [selectedAction, setSelectedAction] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState("");

  const {
    data: logs,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ["audit-logs", selectedEntity, selectedAction],
    queryFn: () =>
      listAuditLogs({
        entity_type: selectedEntity || undefined,
        action: selectedAction || undefined,
      }),
  });

  const filteredLogs = logs?.filter((log) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      (log.user_email && log.user_email.toLowerCase().includes(q)) ||
      log.action.toLowerCase().includes(q) ||
      log.entity_type.toLowerCase().includes(q) ||
      (log.details && log.details.toLowerCase().includes(q))
    );
  });

  const handleExport = () => {
    if (!filteredLogs || filteredLogs.length === 0) return;
    exportToCSV("audit_logs", filteredLogs, [
      { key: "created_at", label: "Timestamp" },
      { key: "user_email", label: "User Email" },
      { key: "action", label: "Action" },
      { key: "entity_type", label: "Entity Type" },
      { key: "entity_id", label: "Entity ID" },
      { key: "details", label: "Details" },
      { key: "ip_address", label: "IP Address" },
    ]);
  };

  return (
    <AppShell>
      <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8 space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-primary">
              Compliance & Security
            </p>
            <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-950 sm:text-3xl">
              Audit Logs
            </h1>
            <p className="mt-1 text-xs text-slate-500">
              Immutable chronological record of business events, member activities, and data mutations.
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
              onClick={handleExport}
              disabled={!filteredLogs || filteredLogs.length === 0}
              className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3.5 py-2 text-xs font-semibold text-white shadow-sm transition hover:opacity-90 disabled:opacity-50"
            >
              <Download className="h-4 w-4" />
              Export Audit Trail
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between rounded-xl border border-border bg-white p-4 shadow-sm">
          <div className="relative flex-1 max-w-xs">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              type="search"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by user, action, or details..."
              className="w-full rounded-lg border border-border bg-slate-50 py-2 pl-9 pr-3 text-xs outline-none focus:border-primary focus:bg-white transition"
            />
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-1.5">
              <Filter className="h-4 w-4 text-slate-400" />
              <select
                value={selectedEntity}
                onChange={(e) => setSelectedEntity(e.target.value)}
                className="rounded-lg border border-border bg-white px-3 py-2 text-xs text-slate-700 outline-none focus:border-primary transition"
              >
                <option value="">All Entity Types</option>
                <option value="PRODUCT">PRODUCT</option>
                <option value="ORDER">ORDER</option>
                <option value="INVOICE">INVOICE</option>
                <option value="PAYMENT">PAYMENT</option>
                <option value="MEMBERSHIP">MEMBERSHIP</option>
                <option value="ORGANIZATION">ORGANIZATION</option>
                <option value="CATEGORY">CATEGORY</option>
                <option value="BRANCH">BRANCH</option>
                <option value="CUSTOMER">CUSTOMER</option>
              </select>
            </div>

            <select
              value={selectedAction}
              onChange={(e) => setSelectedAction(e.target.value)}
              className="rounded-lg border border-border bg-white px-3 py-2 text-xs text-slate-700 outline-none focus:border-primary transition"
            >
              <option value="">All Actions</option>
              <option value="CREATE">CREATE</option>
              <option value="UPDATE">UPDATE</option>
              <option value="DELETE">DELETE</option>
              <option value="CONFIRM">CONFIRM</option>
              <option value="COMPLETE">COMPLETE</option>
              <option value="CANCEL">CANCEL</option>
              <option value="ISSUE">ISSUE</option>
              <option value="VOID">VOID</option>
              <option value="REFUND">REFUND</option>
            </select>
          </div>
        </div>

        {/* Audit Table */}
        <div className="rounded-xl border border-border bg-white shadow-sm overflow-hidden">
          {isLoading ? (
            <div className="flex h-64 items-center justify-center">
              <LoadingSpinner message="Loading audit trail records..." />
            </div>
          ) : isError ? (
            <div className="p-8">
              <ErrorStateView
                message={
                  error instanceof Error
                    ? error.message
                    : "Unable to load audit logs."
                }
                onRetry={() => refetch()}
              />
            </div>
          ) : !filteredLogs || filteredLogs.length === 0 ? (
            <div className="p-8">
              <EmptyStateView
                title="No audit records found"
                message="No logs match your filter criteria or no actions have been logged yet."
              />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-border bg-slate-50 text-slate-500">
                    <th className="py-3.5 pl-6 pr-3 font-semibold">Timestamp</th>
                    <th className="py-3.5 px-3 font-semibold">User</th>
                    <th className="py-3.5 px-3 font-semibold">Action</th>
                    <th className="py-3.5 px-3 font-semibold">Entity</th>
                    <th className="py-3.5 px-3 font-semibold">Details</th>
                    <th className="py-3.5 pl-3 pr-6 font-semibold">IP Address</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredLogs.map((log) => (
                    <tr key={log.id} className="hover:bg-slate-50 transition">
                      <td className="py-3.5 pl-6 pr-3 font-mono text-slate-500 text-[11px] whitespace-nowrap">
                        <div className="flex items-center gap-1.5">
                          <Clock className="h-3 w-3 text-slate-400" />
                          <span>{new Date(log.created_at).toLocaleString()}</span>
                        </div>
                      </td>
                      <td className="py-3.5 px-3 font-semibold text-slate-800 whitespace-nowrap">
                        <div className="flex items-center gap-1.5">
                          <User className="h-3.5 w-3.5 text-slate-400" />
                          <span>{log.user_email || "System"}</span>
                        </div>
                      </td>
                      <td className="py-3.5 px-3 whitespace-nowrap">
                        <span
                          className={`inline-block rounded-md px-2 py-0.5 text-[10px] font-bold tracking-tight ${
                            log.action.includes("CREATE") ||
                            log.action.includes("ADD")
                              ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                              : log.action.includes("DELETE") ||
                                log.action.includes("VOID") ||
                                log.action.includes("CANCEL")
                              ? "bg-rose-50 text-rose-700 border border-rose-200"
                              : log.action.includes("REFUND")
                              ? "bg-purple-50 text-purple-700 border border-purple-200"
                              : "bg-blue-50 text-blue-700 border border-blue-200"
                          }`}
                        >
                          {log.action}
                        </span>
                      </td>
                      <td className="py-3.5 px-3 font-mono text-slate-700 font-semibold whitespace-nowrap">
                        {log.entity_type}
                      </td>
                      <td className="py-3.5 px-3 text-slate-600 max-w-md truncate">
                        {log.details || "—"}
                      </td>
                      <td className="py-3.5 pl-3 pr-6 font-mono text-slate-400 text-[11px] whitespace-nowrap">
                        {log.ip_address || "internal"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
