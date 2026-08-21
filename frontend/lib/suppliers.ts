import { apiRequest } from "./api";
import type {
  Supplier,
  SupplierCreate,
  SupplierUpdate,
} from "../types/suppliers";

export async function listSuppliers(params?: {
  page?: number;
  page_size?: number;
  q?: string;
}): Promise<Supplier[]> {
  const query = new URLSearchParams();
  if (params?.page) query.append("page", params.page.toString());
  if (params?.page_size) query.append("page_size", params.page_size.toString());
  if (params?.q) query.append("q", params.q);

  const qs = query.toString() ? `?${query.toString()}` : "";
  return apiRequest<Supplier[]>(`/suppliers${qs}`);
}

export async function getSupplier(id: string): Promise<Supplier> {
  return apiRequest<Supplier>(`/suppliers/${id}`);
}

export async function createSupplier(data: SupplierCreate): Promise<Supplier> {
  return apiRequest<Supplier>("/suppliers", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateSupplier(
  id: string,
  data: SupplierUpdate,
): Promise<Supplier> {
  return apiRequest<Supplier>(`/suppliers/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deleteSupplier(id: string): Promise<{ status: string }> {
  return apiRequest<{ status: string }>(`/suppliers/${id}`, {
    method: "DELETE",
  });
}
