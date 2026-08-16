import { apiRequest } from "./api";
import type {
  Customer,
  CustomerCreate,
  CustomerUpdate,
} from "../types/customers";

export async function listCustomers(params?: {
  page?: number;
  page_size?: number;
  q?: string;
  phone?: string;
  email?: string;
}): Promise<Customer[]> {
  const query = new URLSearchParams();
  if (params?.page) query.append("page", params.page.toString());
  if (params?.page_size) query.append("page_size", params.page_size.toString());
  if (params?.q) query.append("q", params.q);
  if (params?.phone) query.append("phone", params.phone);
  if (params?.email) query.append("email", params.email);

  const qs = query.toString() ? `?${query.toString()}` : "";
  return apiRequest<Customer[]>(`/customers${qs}`);
}

export async function getCustomer(id: string): Promise<Customer> {
  return apiRequest<Customer>(`/customers/${id}`);
}

export async function createCustomer(data: CustomerCreate): Promise<Customer> {
  return apiRequest<Customer>("/customers", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateCustomer(
  id: string,
  data: CustomerUpdate,
): Promise<Customer> {
  return apiRequest<Customer>(`/customers/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deleteCustomer(id: string): Promise<{ success: boolean }> {
  return apiRequest<{ success: boolean }>(`/customers/${id}`, {
    method: "DELETE",
  });
}
