"use client";

import React, { useState } from "react";
import {
  BarChart3,
  Boxes,
  Building2,
  ChevronDown,
  ClipboardList,
  FileText,
  LayoutDashboard,
  LogOut,
  Package,
  Settings,
  Shield,
  ShoppingCart,
  Users,
  Wallet,
  X,
  Truck,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "../hooks/use-auth";

const navigation = [
  {
    title: "MAIN",
    items: [
      {
        label: "Dashboard",
        href: "/dashboard",
        icon: LayoutDashboard,
      },
    ],
  },
  {
    title: "SALES",
    items: [
      {
        label: "Orders",
        href: "/orders",
        icon: ShoppingCart,
      },
      {
        label: "Invoices",
        href: "/invoices",
        icon: FileText,
      },
      {
        label: "Payments",
        href: "/payments",
        icon: Wallet,
      },
      {
        label: "Purchase Orders",
        href: "/purchase-orders",
        icon: ClipboardList,
      },
    ],
  },
  {
    title: "CATALOG",
    items: [
      {
        label: "Products",
        href: "/products",
        icon: Package,
      },
      {
        label: "Inventory",
        href: "/inventory",
        icon: Boxes,
      },
      {
        label: "Warehouses",
        href: "/warehouses",
        icon: Boxes,
      },
      {
        label: "Categories",
        href: "/categories",
        icon: ClipboardList,
      },
      {
        label: "Suppliers",
        href: "/suppliers",
        icon: Truck,
      },
    ],
  },
  {
    title: "CUSTOMERS",
    items: [
      {
        label: "Customers",
        href: "/customers",
        icon: Users,
      },
      {
        label: "Branches",
        href: "/branches",
        icon: Building2,
      },
    ],
  },
  {
    title: "COMPLIANCE & AUDIT",
    items: [
      {
        label: "Analytics",
        href: "/analytics",
        icon: BarChart3,
      },
      {
        label: "Reports",
        href: "/reports",
        icon: FileText,
      },
      {
        label: "Audit Logs",
        href: "/audit-logs",
        icon: Shield,
      },
    ],
  },
];

export default function Sidebar({
  mobileOpen = false,
  onMobileClose,
}: {
  mobileOpen?: boolean;
  onMobileClose?: () => void;
}) {
  const pathname = usePathname();
  const { user, organization, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);

  const userInitial = user?.full_name ? user.full_name.charAt(0).toUpperCase() : "A";
  const orgName = organization?.name || "NEXUS Platform";

  const content = (
    <div className="flex h-full flex-col bg-white">
      <div className="flex h-16 items-center justify-between border-b border-border px-6">
        <Link
          href="/dashboard"
          onClick={onMobileClose}
          className="flex items-center gap-3"
        >
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-sm font-bold text-white shadow-sm">
            N
          </div>

          <div>
            <p className="text-lg font-bold tracking-tight text-slate-950">
              NEXUS
            </p>
            <p className="text-[10px] font-medium uppercase tracking-widest text-slate-400 truncate max-w-[130px]">
              {orgName}
            </p>
          </div>
        </Link>

        {onMobileClose && (
          <button
            type="button"
            onClick={onMobileClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700 lg:hidden"
            aria-label="Close navigation"
          >
            <X className="h-5 w-5" />
          </button>
        )}
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-5">
        {navigation.map((group) => (
          <div key={group.title} className="mb-6">
            <p className="mb-2 px-3 text-[10px] font-semibold tracking-widest text-slate-400">
              {group.title}
            </p>

            <div className="space-y-1">
              {group.items.map((item) => {
                const Icon = item.icon;
                const active =
                  pathname === item.href ||
                  (item.href !== "/dashboard" && pathname.startsWith(`${item.href}`));

                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={onMobileClose}
                    className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${
                      active
                        ? "bg-primary/10 text-primary font-semibold"
                        : "text-slate-600 hover:bg-slate-50 hover:text-slate-950"
                    }`}
                  >
                    <Icon className="h-4 w-4 shrink-0" />
                    <span>{item.label}</span>

                    {active && (
                      <span className="ml-auto h-1.5 w-1.5 rounded-full bg-primary" />
                    )}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      <div className="border-t border-border p-3">
        <Link
          href="/settings"
          onClick={onMobileClose}
          className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${
            pathname.startsWith("/settings")
              ? "bg-primary/10 text-primary font-semibold"
              : "text-slate-600 hover:bg-slate-50 hover:text-slate-950"
          }`}
        >
          <Settings className="h-4 w-4" />
          Settings
        </Link>

        <div className="relative mt-2">
          <button
            type="button"
            onClick={() => setMenuOpen(!menuOpen)}
            className="flex w-full items-center gap-3 rounded-lg bg-slate-50 p-2.5 text-left transition hover:bg-slate-100"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/15 text-xs font-semibold text-primary">
              {userInitial}
            </div>

            <div className="min-w-0 flex-1">
              <p className="truncate text-xs font-semibold text-slate-900">
                {user?.full_name || "Administrator"}
              </p>
              <p className="truncate text-[10px] text-slate-500">
                {user?.email || "Platform Admin"}
              </p>
            </div>

            <ChevronDown
              className={`h-4 w-4 text-slate-400 transition-transform ${
                menuOpen ? "rotate-180" : ""
              }`}
            />
          </button>

          {menuOpen && (
            <div className="absolute bottom-full left-0 mb-2 w-full rounded-lg border border-border bg-white p-1.5 shadow-lg">
              <button
                type="button"
                onClick={() => {
                  setMenuOpen(false);
                  logout();
                }}
                className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-xs font-medium text-rose-600 hover:bg-rose-50 transition"
              >
                <LogOut className="h-4 w-4" />
                Sign out
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden w-64 shrink-0 border-r border-border lg:block">
        {content}
      </aside>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 flex lg:hidden">
          <div
            className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm transition-opacity"
            onClick={onMobileClose}
          />
          <div className="relative flex w-full max-w-xs flex-1 flex-col border-r border-border bg-white shadow-2xl">
            {content}
          </div>
        </div>
      )}
    </>
  );
}