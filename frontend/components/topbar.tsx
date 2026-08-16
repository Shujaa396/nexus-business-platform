"use client";

import React, { useState } from "react";
import { Bell, ChevronDown, LogOut, Menu, Search, User as UserIcon } from "lucide-react";
import { useAuth } from "../hooks/use-auth";

export default function Topbar({
  onMobileToggle,
}: {
  onMobileToggle?: () => void;
}) {
  const { user, organization, logout } = useAuth();
  const [profileOpen, setProfileOpen] = useState(false);

  const userInitial = user?.full_name ? user.full_name.charAt(0).toUpperCase() : "A";

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center border-b border-border bg-white/95 px-4 backdrop-blur-sm sm:px-6">
      <button
        type="button"
        onClick={onMobileToggle}
        className="mr-3 rounded-lg p-2 text-slate-500 hover:bg-slate-100 lg:hidden"
        aria-label="Open navigation"
      >
        <Menu className="h-5 w-5" />
      </button>

      <div className="relative hidden max-w-md flex-1 sm:block">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />

        <input
          type="search"
          placeholder="Search products, orders, customers..."
          className="h-10 w-full rounded-lg border border-border bg-slate-50 pl-10 pr-4 text-sm outline-none transition placeholder:text-slate-400 focus:border-primary focus:bg-white"
        />
      </div>

      <div className="ml-auto flex items-center gap-2">
        <button
          type="button"
          className="relative rounded-lg p-2.5 text-slate-500 hover:bg-slate-100"
          aria-label="Notifications"
        >
          <Bell className="h-5 w-5" />
          <span className="absolute right-2 top-2 h-2 w-2 rounded-full bg-accent" />
        </button>

        <div className="hidden h-8 w-px bg-border sm:block" />

        <div className="relative">
          <button
            type="button"
            onClick={() => setProfileOpen(!profileOpen)}
            className="flex items-center gap-2.5 rounded-lg p-1.5 transition hover:bg-slate-50"
          >
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/10 text-sm font-semibold text-primary">
              {userInitial}
            </div>

            <div className="hidden text-left sm:block">
              <p className="text-sm font-semibold leading-none text-slate-900 truncate max-w-[130px]">
                {user?.full_name || "Administrator"}
              </p>
              <p className="mt-1 text-[11px] leading-none text-slate-500 truncate max-w-[130px]">
                {organization?.name || "Business Workspace"}
              </p>
            </div>

            <ChevronDown
              className={`hidden sm:block h-3.5 w-3.5 text-slate-400 transition-transform ${
                profileOpen ? "rotate-180" : ""
              }`}
            />
          </button>

          {profileOpen && (
            <div className="absolute right-0 mt-2 w-56 rounded-xl border border-border bg-white p-1.5 shadow-xl z-50">
              <div className="border-b border-border px-3 py-2">
                <p className="text-xs font-semibold text-slate-900 truncate">
                  {user?.full_name || "User"}
                </p>
                <p className="text-[11px] text-slate-500 truncate">
                  {user?.email || "user@example.com"}
                </p>
              </div>

              <div className="mt-1 space-y-0.5">
                <button
                  type="button"
                  onClick={() => {
                    setProfileOpen(false);
                    logout();
                  }}
                  className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-xs font-medium text-rose-600 hover:bg-rose-50 transition"
                >
                  <LogOut className="h-4 w-4" />
                  Sign out
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}