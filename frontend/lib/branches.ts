import { apiRequest } from "./api";
import type { Branch, BranchCreate, BranchUpdate } from "../types/branches";

export async function listBranches(params?: {
  page?: number;
  page_size?: number;
}): Promise<Branch[]> {
  const query = new URLSearchParams();
  if (params?.page) query.append("page", params.page.toString());
  if (params?.page_size) query.append("page_size", params.page_size.toString());

  const qs = query.toString() ? `?${query.toString()}` : "";
  return apiRequest<Branch[]>(`/branches${qs}`);
}

export async function getBranch(id: string): Promise<Branch> {
  return apiRequest<Branch>(`/branches/${id}`);
}

export async function createBranch(data: BranchCreate): Promise<Branch> {
  return apiRequest<Branch>("/branches", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateBranch(
  id: string,
  data: BranchUpdate,
): Promise<Branch> {
  return apiRequest<Branch>(`/branches/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deleteBranch(id: string): Promise<{ status: string }> {
  return apiRequest<{ status: string }>(`/branches/${id}`, {
    method: "DELETE",
  });
}
