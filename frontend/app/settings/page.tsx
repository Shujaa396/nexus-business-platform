"use client";

import React, { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertCircle,
  Building,
  CheckCircle2,
  Edit2,
  Key,
  Loader2,
  LogOut,
  Mail,
  Plus,
  RefreshCw,
  Server,
  Shield,
  Trash2,
  User,
  UserCheck,
  UserPlus,
  Users,
} from "lucide-react";

import AppShell from "../../components/app-shell";
import { StatusBadge } from "../../components/ui/badge";
import { ConfirmDialog } from "../../components/ui/confirm-dialog";
import { Modal } from "../../components/ui/modal";
import {
  EmptyStateView,
  ErrorStateView,
  LoadingSpinner,
} from "../../components/ui/state-views";
import { useAuth } from "../../hooks/use-auth";
import {
  addOrganizationMember,
  deactivateMember,
  listOrganizationMembers,
  updateMemberRole,
  updateOrganizationProfile,
} from "../../lib/organization";
import type {
  Member,
  MemberCreate,
  MemberRoleUpdate,
  OrganizationUpdate,
} from "../../types/organization";

type SettingsTab = "organization" | "team" | "security";

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const { user, organization, logout, updateSession } = useAuth();
  const [activeTab, setActiveTab] = useState<SettingsTab>("organization");

  // Success notifications
  const [feedbackMessage, setFeedbackMessage] = useState("");

  // Org form state
  const [orgName, setOrgName] = useState(organization?.name || "");
  const [orgEmail, setOrgEmail] = useState("");
  const [orgPhone, setOrgPhone] = useState("");
  const [orgAddress, setOrgAddress] = useState("");
  const [orgTaxNumber, setOrgTaxNumber] = useState("");
  const [orgFormError, setOrgFormError] = useState("");

  // Member modal states
  const [isAddMemberOpen, setIsAddMemberOpen] = useState(false);
  const [editingMember, setEditingMember] = useState<Member | null>(null);
  const [deactivatingMember, setDeactivatingMember] = useState<Member | null>(null);

  // Member form states
  const [newMemberEmail, setNewMemberEmail] = useState("");
  const [newMemberName, setNewMemberName] = useState("");
  const [newMemberPassword, setNewMemberPassword] = useState("");
  const [newMemberRole, setNewMemberRole] = useState("staff");
  const [memberFormError, setMemberFormError] = useState("");

  // Queries
  const {
    data: members,
    isLoading: isLoadingMembers,
    isError: isMembersError,
    error: membersError,
    refetch: refetchMembers,
  } = useQuery({
    queryKey: ["org-members"],
    queryFn: () => listOrganizationMembers(),
  });

  // Mutations
  const updateOrgMutation = useMutation({
    mutationFn: (data: OrganizationUpdate) => updateOrganizationProfile(data),
    onSuccess: () => {
      setFeedbackMessage("Organization settings updated successfully.");
      updateSession();
      setTimeout(() => setFeedbackMessage(""), 3500);
    },
    onError: (err: Error) => {
      setOrgFormError(err.message || "Failed to update organization profile.");
    },
  });

  const addMemberMutation = useMutation({
    mutationFn: (data: MemberCreate) => addOrganizationMember(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["org-members"] });
      setIsAddMemberOpen(false);
      resetMemberForm();
      setFeedbackMessage("New team member added successfully.");
      setTimeout(() => setFeedbackMessage(""), 3500);
    },
    onError: (err: Error) => {
      setMemberFormError(err.message || "Failed to add team member.");
    },
  });

  const updateRoleMutation = useMutation({
    mutationFn: ({ userId, data }: { userId: string; data: MemberRoleUpdate }) =>
      updateMemberRole(userId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["org-members"] });
      setEditingMember(null);
      setFeedbackMessage("Member role updated successfully.");
      setTimeout(() => setFeedbackMessage(""), 3500);
    },
    onError: (err: Error) => {
      setMemberFormError(err.message || "Failed to update member role.");
    },
  });

  const deactivateMemberMutation = useMutation({
    mutationFn: (userId: string) => deactivateMember(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["org-members"] });
      setDeactivatingMember(null);
      setFeedbackMessage("Member deactivated successfully.");
      setTimeout(() => setFeedbackMessage(""), 3500);
    },
  });

  const resetMemberForm = () => {
    setNewMemberEmail("");
    setNewMemberName("");
    setNewMemberPassword("");
    setNewMemberRole("staff");
    setMemberFormError("");
  };

  const handleSaveOrg = (e: React.FormEvent) => {
    e.preventDefault();
    setOrgFormError("");
    updateOrgMutation.mutate({
      name: orgName.trim() || undefined,
      email: orgEmail.trim() || undefined,
      phone: orgPhone.trim() || undefined,
      address: orgAddress.trim() || undefined,
      tax_number: orgTaxNumber.trim() || undefined,
    });
  };

  const handleAddMemberSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setMemberFormError("");
    if (!newMemberEmail || !newMemberPassword || !newMemberName) {
      setMemberFormError("All required fields must be filled.");
      return;
    }
    addMemberMutation.mutate({
      email: newMemberEmail.trim(),
      full_name: newMemberName.trim(),
      password: newMemberPassword,
      role_name: newMemberRole,
    });
  };

  const handleUpdateRoleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingMember) return;
    setMemberFormError("");
    updateRoleMutation.mutate({
      userId: editingMember.user_id,
      data: { role_name: newMemberRole },
    });
  };

  return (
    <AppShell>
      <div className="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6 lg:px-8 space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-primary">
              Enterprise Configuration
            </p>
            <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-950 sm:text-3xl">
              Settings & Organization
            </h1>
            <p className="mt-1 text-xs text-slate-500">
              Manage organization profile, team members, RBAC permissions, and security.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => {
                updateSession();
                refetchMembers();
              }}
              className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-white px-3 py-2 text-xs font-medium text-slate-700 shadow-sm transition hover:bg-slate-50"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Sync Session
            </button>
            <button
              type="button"
              onClick={logout}
              className="inline-flex items-center gap-1.5 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs font-semibold text-rose-700 shadow-sm transition hover:bg-rose-100"
            >
              <LogOut className="h-3.5 w-3.5" />
              Sign Out
            </button>
          </div>
        </div>

        {/* Global Feedback Banner */}
        {feedbackMessage && (
          <div className="flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-xs font-semibold text-emerald-800 animate-in fade-in">
            <CheckCircle2 className="h-4 w-4 shrink-0" />
            <span>{feedbackMessage}</span>
          </div>
        )}

        {/* Tabs */}
        <div className="flex flex-wrap gap-1 border-b border-border pb-1">
          <button
            onClick={() => setActiveTab("organization")}
            className={`flex items-center gap-2 rounded-lg px-3.5 py-2 text-xs font-semibold transition ${
              activeTab === "organization"
                ? "bg-primary text-white shadow-sm"
                : "text-slate-600 hover:bg-slate-100"
            }`}
          >
            <Building className="h-4 w-4" />
            Organization Profile
          </button>
          <button
            onClick={() => setActiveTab("team")}
            className={`flex items-center gap-2 rounded-lg px-3.5 py-2 text-xs font-semibold transition ${
              activeTab === "team"
                ? "bg-primary text-white shadow-sm"
                : "text-slate-600 hover:bg-slate-100"
            }`}
          >
            <Users className="h-4 w-4" />
            Team & Roles
          </button>
          <button
            onClick={() => setActiveTab("security")}
            className={`flex items-center gap-2 rounded-lg px-3.5 py-2 text-xs font-semibold transition ${
              activeTab === "security"
                ? "bg-primary text-white shadow-sm"
                : "text-slate-600 hover:bg-slate-100"
            }`}
          >
            <Shield className="h-4 w-4" />
            Security & Permissions
          </button>
        </div>

        {/* TAB 1: ORGANIZATION PROFILE */}
        {activeTab === "organization" && (
          <div className="rounded-xl border border-border bg-white p-6 shadow-sm space-y-6">
            <div>
              <h3 className="text-sm font-bold text-slate-950">
                Tenant Identity & Business Information
              </h3>
              <p className="text-xs text-slate-500">
                Details appear on official invoices, billing receipts, and reports.
              </p>
            </div>

            <form onSubmit={handleSaveOrg} className="space-y-4 max-w-2xl">
              {orgFormError && (
                <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-2.5 text-xs text-red-700">
                  <AlertCircle className="h-4 w-4 shrink-0" />
                  <p>{orgFormError}</p>
                </div>
              )}

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-1 block text-xs font-semibold text-slate-800">
                    Organization Legal Name
                  </label>
                  <input
                    type="text"
                    required
                    value={orgName}
                    onChange={(e) => setOrgName(e.target.value)}
                    placeholder="e.g. Acme Global Enterprises"
                    className="w-full rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary transition"
                  />
                </div>

                <div>
                  <label className="mb-1 block text-xs font-semibold text-slate-800">
                    Tenant Slug (System Identifier)
                  </label>
                  <input
                    type="text"
                    disabled
                    value={organization?.slug || ""}
                    className="w-full rounded-lg border border-slate-200 bg-slate-100 px-3 py-2 text-xs font-mono text-slate-500 cursor-not-allowed"
                  />
                </div>

                <div>
                  <label className="mb-1 block text-xs font-semibold text-slate-800">
                    Contact Email
                  </label>
                  <input
                    type="email"
                    value={orgEmail}
                    onChange={(e) => setOrgEmail(e.target.value)}
                    placeholder="billing@acmeglobal.com"
                    className="w-full rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary transition"
                  />
                </div>

                <div>
                  <label className="mb-1 block text-xs font-semibold text-slate-800">
                    Contact Phone
                  </label>
                  <input
                    type="tel"
                    value={orgPhone}
                    onChange={(e) => setOrgPhone(e.target.value)}
                    placeholder="+92 21 111 222 333"
                    className="w-full rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary transition"
                  />
                </div>

                <div className="sm:col-span-2">
                  <label className="mb-1 block text-xs font-semibold text-slate-800">
                    National Tax / NTN / Registration Number
                  </label>
                  <input
                    type="text"
                    value={orgTaxNumber}
                    onChange={(e) => setOrgTaxNumber(e.target.value)}
                    placeholder="NTN-99887711"
                    className="w-full rounded-lg border border-border px-3 py-2 text-xs font-mono outline-none focus:border-primary transition"
                  />
                </div>

                <div className="sm:col-span-2">
                  <label className="mb-1 block text-xs font-semibold text-slate-800">
                    Headquarters / Billing Address
                  </label>
                  <textarea
                    rows={2}
                    value={orgAddress}
                    onChange={(e) => setOrgAddress(e.target.value)}
                    placeholder="Office address, City, Country"
                    className="w-full rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary transition"
                  />
                </div>
              </div>

              <div className="flex justify-end pt-2">
                <button
                  type="submit"
                  disabled={updateOrgMutation.isPending}
                  className="flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-xs font-semibold text-white shadow-sm transition hover:opacity-90 disabled:opacity-50"
                >
                  {updateOrgMutation.isPending && (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  )}
                  Save Organization Profile
                </button>
              </div>
            </form>
          </div>
        )}

        {/* TAB 2: TEAM & ROLES */}
        {activeTab === "team" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-950">
                  Organization Members
                </h3>
                <p className="text-xs text-slate-500">
                  Manage user access, role assignments, and tenant membership status.
                </p>
              </div>

              <button
                type="button"
                onClick={() => {
                  resetMemberForm();
                  setIsAddMemberOpen(true);
                }}
                className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3.5 py-2 text-xs font-semibold text-white shadow-sm transition hover:opacity-90"
              >
                <UserPlus className="h-4 w-4" />
                Add Member
              </button>
            </div>

            {/* Members Table */}
            <div className="rounded-xl border border-border bg-white shadow-sm overflow-hidden">
              {isLoadingMembers ? (
                <div className="flex h-48 items-center justify-center">
                  <LoadingSpinner message="Loading team members..." />
                </div>
              ) : isMembersError ? (
                <div className="p-8">
                  <ErrorStateView
                    message={
                      membersError instanceof Error
                        ? membersError.message
                        : "Unable to load team members."
                    }
                    onRetry={() => refetchMembers()}
                  />
                </div>
              ) : !members || members.length === 0 ? (
                <div className="p-8">
                  <EmptyStateView
                    title="No team members found"
                    message="No additional members in this organization."
                  />
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-border bg-slate-50 text-slate-500">
                        <th className="py-3.5 pl-6 pr-3 font-semibold">User</th>
                        <th className="py-3.5 px-3 font-semibold">Email</th>
                        <th className="py-3.5 px-3 font-semibold">Assigned Role</th>
                        <th className="py-3.5 px-3 text-center font-semibold">Status</th>
                        <th className="py-3.5 px-3 font-semibold">Joined Date</th>
                        <th className="py-3.5 pl-3 pr-6 text-right font-semibold">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {members.map((mem) => (
                        <tr key={mem.membership_id} className="hover:bg-slate-50 transition">
                          <td className="py-3.5 pl-6 pr-3 font-semibold text-slate-900">
                            <div className="flex items-center gap-2">
                              <div className="flex h-7 w-7 items-center justify-center rounded-full bg-teal-50 text-teal-700 font-bold text-xs">
                                {mem.full_name.charAt(0).toUpperCase()}
                              </div>
                              <span>{mem.full_name}</span>
                            </div>
                          </td>
                          <td className="py-3.5 px-3 font-mono text-slate-600">
                            {mem.email}
                          </td>
                          <td className="py-3.5 px-3">
                            <span
                              className={`inline-block rounded-md px-2.5 py-0.5 text-[11px] font-bold uppercase ${
                                mem.role_name === "admin"
                                  ? "bg-purple-50 text-purple-700 border border-purple-200"
                                  : mem.role_name === "manager"
                                  ? "bg-blue-50 text-blue-700 border border-blue-200"
                                  : "bg-slate-100 text-slate-700 border border-slate-200"
                              }`}
                            >
                              {mem.role_name}
                            </span>
                          </td>
                          <td className="py-3.5 px-3 text-center">
                            <StatusBadge
                              status={mem.is_active ? "ACTIVE" : "INACTIVE"}
                            />
                          </td>
                          <td className="py-3.5 px-3 font-mono text-[11px] text-slate-500">
                            {new Date(mem.joined_at).toLocaleDateString()}
                          </td>
                          <td className="py-3.5 pl-3 pr-6 text-right">
                            <div className="flex items-center justify-end gap-1.5">
                              <button
                                type="button"
                                onClick={() => {
                                  setEditingMember(mem);
                                  setNewMemberRole(mem.role_name);
                                }}
                                className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition"
                                title="Change Role"
                              >
                                <Edit2 className="h-3.5 w-3.5" />
                              </button>
                              {mem.user_id !== user?.id && mem.is_active && (
                                <button
                                  type="button"
                                  onClick={() => setDeactivatingMember(mem)}
                                  className="rounded-lg p-1.5 text-slate-400 hover:bg-rose-50 hover:text-rose-600 transition"
                                  title="Deactivate Member"
                                >
                                  <Trash2 className="h-3.5 w-3.5" />
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 3: SECURITY & PERMISSIONS */}
        {activeTab === "security" && (
          <div className="space-y-6">
            <div className="rounded-xl border border-border bg-white p-6 shadow-sm space-y-4">
              <h3 className="text-sm font-bold text-slate-950">
                Active Session & Identity
              </h3>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 text-xs">
                <div>
                  <p className="text-slate-400 font-medium">Logged In As</p>
                  <p className="font-semibold text-slate-900 mt-0.5">
                    {user?.full_name} ({user?.email})
                  </p>
                </div>
                <div>
                  <p className="text-slate-400 font-medium">Organization UUID</p>
                  <p className="font-mono text-slate-700 mt-0.5 truncate">
                    {organization?.id}
                  </p>
                </div>
              </div>
            </div>

            {/* Role Matrix Overview */}
            <div className="rounded-xl border border-border bg-white shadow-sm overflow-hidden">
              <div className="border-b border-border bg-slate-50 px-6 py-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                  Role-Based Permission Matrix (RBAC)
                </h3>
              </div>
              <div className="p-6">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="text-slate-400 border-b border-slate-100">
                      <th className="py-2">Permission Scope</th>
                      <th className="py-2 text-center font-bold text-purple-700">Admin</th>
                      <th className="py-2 text-center font-bold text-blue-700">Manager</th>
                      <th className="py-2 text-center font-bold text-slate-700">Staff</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    <tr>
                      <td className="py-2.5 font-medium text-slate-800">Dashboard & Analytics View</td>
                      <td className="py-2.5 text-center text-emerald-600 font-bold">✓</td>
                      <td className="py-2.5 text-center text-emerald-600 font-bold">✓</td>
                      <td className="py-2.5 text-center text-emerald-600 font-bold">✓</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 font-medium text-slate-800">Create & Manage Orders / Sales</td>
                      <td className="py-2.5 text-center text-emerald-600 font-bold">✓</td>
                      <td className="py-2.5 text-center text-emerald-600 font-bold">✓</td>
                      <td className="py-2.5 text-center text-emerald-600 font-bold">✓</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 font-medium text-slate-800">Product & Inventory Adjustments</td>
                      <td className="py-2.5 text-center text-emerald-600 font-bold">✓</td>
                      <td className="py-2.5 text-center text-emerald-600 font-bold">✓</td>
                      <td className="py-2.5 text-center text-slate-400">View Only</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 font-medium text-slate-800">Invoices, Billing & Payments Refund</td>
                      <td className="py-2.5 text-center text-emerald-600 font-bold">✓</td>
                      <td className="py-2.5 text-center text-emerald-600 font-bold">✓</td>
                      <td className="py-2.5 text-center text-slate-400">View Only</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 font-medium text-slate-800">Audit Logs & Compliance Trail</td>
                      <td className="py-2.5 text-center text-emerald-600 font-bold">✓</td>
                      <td className="py-2.5 text-center text-emerald-600 font-bold">✓</td>
                      <td className="py-2.5 text-center text-rose-500 font-bold">✗</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 font-medium text-slate-800">Team Management & Role Modification</td>
                      <td className="py-2.5 text-center text-emerald-600 font-bold">✓</td>
                      <td className="py-2.5 text-center text-rose-500 font-bold">✗</td>
                      <td className="py-2.5 text-center text-rose-500 font-bold">✗</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 font-medium text-slate-800">Organization Settings & Profile</td>
                      <td className="py-2.5 text-center text-emerald-600 font-bold">✓</td>
                      <td className="py-2.5 text-center text-rose-500 font-bold">✗</td>
                      <td className="py-2.5 text-center text-rose-500 font-bold">✗</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Add Member Modal */}
      <Modal
        isOpen={isAddMemberOpen}
        onClose={() => setIsAddMemberOpen(false)}
        title="Invite Team Member"
        description="Add a new user to your organization with specific role privileges."
      >
        <form onSubmit={handleAddMemberSubmit} className="space-y-4">
          {memberFormError && (
            <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-2.5 text-xs text-red-700">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <p>{memberFormError}</p>
            </div>
          )}

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-800">
              Full Name <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              required
              value={newMemberName}
              onChange={(e) => setNewMemberName(e.target.value)}
              placeholder="e.g. Jane Doe"
              className="w-full rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary transition"
            />
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-800">
              Email Address <span className="text-rose-500">*</span>
            </label>
            <input
              type="email"
              required
              value={newMemberEmail}
              onChange={(e) => setNewMemberEmail(e.target.value)}
              placeholder="jane@company.com"
              className="w-full rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary transition"
            />
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-800">
              Initial Password <span className="text-rose-500">*</span>
            </label>
            <input
              type="password"
              required
              value={newMemberPassword}
              onChange={(e) => setNewMemberPassword(e.target.value)}
              placeholder="Temporary password"
              className="w-full rounded-lg border border-border px-3 py-2 text-xs outline-none focus:border-primary transition"
            />
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-800">
              Assigned Role <span className="text-rose-500">*</span>
            </label>
            <select
              value={newMemberRole}
              onChange={(e) => setNewMemberRole(e.target.value)}
              className="w-full rounded-lg border border-border bg-white px-3 py-2 text-xs outline-none focus:border-primary transition"
            >
              <option value="staff">Staff (Basic operational privileges)</option>
              <option value="manager">Manager (Operational & reports management)</option>
              <option value="admin">Admin (Full organization & team control)</option>
            </select>
          </div>

          <div className="flex items-center justify-end gap-2 border-t border-border pt-4">
            <button
              type="button"
              onClick={() => setIsAddMemberOpen(false)}
              className="rounded-lg border border-border px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={addMemberMutation.isPending}
              className="flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-xs font-semibold text-white shadow-sm transition hover:opacity-90 disabled:opacity-50"
            >
              {addMemberMutation.isPending && (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              )}
              Add Member
            </button>
          </div>
        </form>
      </Modal>

      {/* Edit Role Modal */}
      <Modal
        isOpen={!!editingMember}
        onClose={() => setEditingMember(null)}
        title="Change Member Role"
        description={`Update role permissions for ${editingMember?.full_name} (${editingMember?.email})`}
      >
        <form onSubmit={handleUpdateRoleSubmit} className="space-y-4">
          {memberFormError && (
            <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-2.5 text-xs text-red-700">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <p>{memberFormError}</p>
            </div>
          )}

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-800">
              Select New Role <span className="text-rose-500">*</span>
            </label>
            <select
              value={newMemberRole}
              onChange={(e) => setNewMemberRole(e.target.value)}
              className="w-full rounded-lg border border-border bg-white px-3 py-2 text-xs outline-none focus:border-primary transition"
            >
              <option value="staff">Staff (Basic operational privileges)</option>
              <option value="manager">Manager (Operational & reports management)</option>
              <option value="admin">Admin (Full organization & team control)</option>
            </select>
          </div>

          <div className="flex items-center justify-end gap-2 border-t border-border pt-4">
            <button
              type="button"
              onClick={() => setEditingMember(null)}
              className="rounded-lg border border-border px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={updateRoleMutation.isPending}
              className="flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-xs font-semibold text-white shadow-sm transition hover:opacity-90 disabled:opacity-50"
            >
              {updateRoleMutation.isPending && (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              )}
              Update Role
            </button>
          </div>
        </form>
      </Modal>

      {/* Deactivate Member Confirmation */}
      <ConfirmDialog
        isOpen={!!deactivatingMember}
        onClose={() => setDeactivatingMember(null)}
        onConfirm={() =>
          deactivatingMember &&
          deactivateMemberMutation.mutate(deactivatingMember.user_id)
        }
        title="Deactivate Member"
        message={`Are you sure you want to deactivate "${deactivatingMember?.full_name}" (${deactivatingMember?.email})? They will no longer be able to log into this organization.`}
        confirmText="Deactivate Member"
        variant="danger"
        isLoading={deactivateMemberMutation.isPending}
      />
    </AppShell>
  );
}
