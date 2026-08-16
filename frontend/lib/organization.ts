import { apiRequest } from "./api";
import type {
  Member,
  MemberCreate,
  MemberRoleUpdate,
  OrganizationUpdate,
} from "../types/organization";
import type { Organization } from "../types/auth";

export async function getOrganizationProfile(): Promise<Organization> {
  return apiRequest<Organization>("/organization");
}

export async function updateOrganizationProfile(
  data: OrganizationUpdate,
): Promise<Organization> {
  return apiRequest<Organization>("/organization", {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function listOrganizationMembers(): Promise<Member[]> {
  return apiRequest<Member[]>("/organization/members");
}

export async function addOrganizationMember(
  data: MemberCreate,
): Promise<Member> {
  return apiRequest<Member>("/organization/members", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateMemberRole(
  userId: string,
  data: MemberRoleUpdate,
): Promise<Member> {
  return apiRequest<Member>(`/organization/members/${userId}/role`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deactivateMember(
  userId: string,
): Promise<{ status: string; message: string }> {
  return apiRequest<{ status: string; message: string }>(
    `/organization/members/${userId}`,
    {
      method: "DELETE",
    },
  );
}
