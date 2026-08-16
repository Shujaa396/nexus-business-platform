"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import type { Organization, User } from "../types/auth";
import {
  clearAuthSession,
  getMe,
  getStoredAccessToken,
  getStoredOrganization,
  getStoredUser,
} from "../lib/auth";

type AuthContextType = {
  user: User | null;
  organization: Organization | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  logout: () => void;
  updateSession: () => void;
};

const AuthContext = createContext<AuthContextType>({
  user: null,
  organization: null,
  isAuthenticated: false,
  isLoading: true,
  logout: () => {},
  updateSession: () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const loadSession = async () => {
    const token = getStoredAccessToken();
    if (token) {
      // Immediate local state initialization
      const localUser = getStoredUser();
      const localOrg = getStoredOrganization();
      setUser(localUser);
      setOrganization(localOrg);
      setIsLoading(false);

      // Background verification via /auth/me
      try {
        const me = await getMe(token);
        if (me) {
          const updatedUser: User = {
            id: me.id,
            email: me.email,
            full_name: me.full_name,
            is_active: me.is_active,
            is_superadmin: me.is_superadmin,
          };
          setUser(updatedUser);
          localStorage.setItem("nexus_user", JSON.stringify(updatedUser));

          if (me.organization_id && me.organization_name) {
            const updatedOrg: Organization = {
              id: me.organization_id,
              name: me.organization_name,
              slug: localOrg?.slug || "",
              is_active: true,
            };
            setOrganization(updatedOrg);
            localStorage.setItem("nexus_organization", JSON.stringify(updatedOrg));
          }
        }
      } catch {
        // Handled by apiRequest token refresh or keeps local session if offline
      }
    } else {
      setUser(null);
      setOrganization(null);
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadSession();
  }, []);

  const logout = () => {
    clearAuthSession();
    setUser(null);
    setOrganization(null);
    router.push("/login");
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        organization,
        isAuthenticated: !!user && !!getStoredAccessToken(),
        isLoading,
        logout,
        updateSession: loadSession,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
