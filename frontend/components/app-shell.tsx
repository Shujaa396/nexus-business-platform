"use client";

import React, { useState } from "react";
import AuthGuard from "./auth-guard";
import Sidebar from "./sidebar";
import Topbar from "./topbar";

export default function AppShell({
  children,
}: {
  children: React.ReactNode;
}) {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  return (
    <AuthGuard>
      <div className="flex min-h-screen bg-background">
        <Sidebar
          mobileOpen={mobileNavOpen}
          onMobileClose={() => setMobileNavOpen(false)}
        />

        <div className="flex min-w-0 flex-1 flex-col">
          <Topbar onMobileToggle={() => setMobileNavOpen((prev) => !prev)} />

          <main className="min-w-0 flex-1">{children}</main>
        </div>
      </div>
    </AuthGuard>
  );
}