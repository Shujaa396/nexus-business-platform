import { apiRequest } from "./api";
import type {
  Customer,
  CustomerCreate,
  CustomerUpdate,
  CustomerPortalData,
  CustomerSummary,
  CustomerPage,
  CustomerOrderDetail,
  CustomerInvoiceDetail,
  CustomerInvoicePortalDetail,
  CustomerContact,
  CustomerAddress,
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

export async function listCustomersPage(params?: {
  page?: number;
  page_size?: number;
  q?: string;
  status?: string;
}): Promise<CustomerPage> {
  const query = new URLSearchParams({ paginated: "true" });
  if (params?.page) query.set("page", params.page.toString());
  if (params?.page_size) query.set("page_size", params.page_size.toString());
  if (params?.q) query.set("q", params.q);
  if (params?.status) query.set("status_filter", params.status);
  return apiRequest<CustomerPage>(`/customers?${query.toString()}`);
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

export async function getCustomerPortal(): Promise<CustomerPortalData> {
  return apiRequest<CustomerPortalData>("/customers/portal/me");
}

export async function getCustomerSummary(id: string): Promise<CustomerSummary> {
  return apiRequest<CustomerSummary>(`/customers/${id}/summary`);
}

export async function getCustomerOrders(id: string): Promise<CustomerPortalData["orders"]> {
  return apiRequest<CustomerPortalData["orders"]>(`/customers/${id}/orders`);
}

export async function getCustomerInvoices(id: string): Promise<CustomerPortalData["invoices"]> {
  return apiRequest<CustomerPortalData["invoices"]>(`/customers/${id}/invoices`);
}

export async function getCustomerPayments(id: string): Promise<CustomerPortalData["payments"]> {
  return apiRequest<CustomerPortalData["payments"]>(`/customers/${id}/payments`);
}

export async function getCustomerContacts(id: string): Promise<CustomerPortalData["contacts"]> {
  return apiRequest<CustomerPortalData["contacts"]>(`/customers/${id}/contacts`);
}

export async function getCustomerAddresses(id: string): Promise<CustomerPortalData["addresses"]> {
  return apiRequest<CustomerPortalData["addresses"]>(`/customers/${id}/addresses`);
}

export async function getPortalOrder(id: string): Promise<CustomerOrderDetail> {
  return apiRequest<CustomerOrderDetail>(`/customers/portal/orders/${id}`);
}

export async function getPortalInvoice(id: string): Promise<CustomerInvoicePortalDetail> {
  return apiRequest<CustomerInvoicePortalDetail>(`/customers/portal/invoices/${id}`);
}

export async function createCustomerContact(id: string, data: Omit<CustomerContact, "id" | "customer_id" | "created_at" | "updated_at">): Promise<CustomerContact> {
  return apiRequest<CustomerContact>(`/customers/${id}/contacts`, { method: "POST", body: JSON.stringify(data) });
}

export async function updateCustomerContact(id: string, contactId: string, data: Omit<CustomerContact, "id" | "customer_id" | "created_at" | "updated_at">): Promise<CustomerContact> {
  return apiRequest<CustomerContact>(`/customers/${id}/contacts/${contactId}`, { method: "PATCH", body: JSON.stringify(data) });
}

export async function deleteCustomerContact(id: string, contactId: string): Promise<{ success: boolean }> {
  return apiRequest<{ success: boolean }>(`/customers/${id}/contacts/${contactId}`, { method: "DELETE" });
}

export async function createCustomerAddress(id: string, data: Omit<CustomerAddress, "id" | "customer_id" | "created_at" | "updated_at">): Promise<CustomerAddress> {
  return apiRequest<CustomerAddress>(`/customers/${id}/addresses`, { method: "POST", body: JSON.stringify(data) });
}

export async function updateCustomerAddress(id: string, addressId: string, data: Omit<CustomerAddress, "id" | "customer_id" | "created_at" | "updated_at">): Promise<CustomerAddress> {
  return apiRequest<CustomerAddress>(`/customers/${id}/addresses/${addressId}`, { method: "PATCH", body: JSON.stringify(data) });
}

export async function deleteCustomerAddress(id: string, addressId: string): Promise<{ success: boolean }> {
  return apiRequest<{ success: boolean }>(`/customers/${id}/addresses/${addressId}`, { method: "DELETE" });
}
