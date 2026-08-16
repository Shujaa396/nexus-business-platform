import { apiRequest } from "./api";
import type {
  Invoice,
  InvoiceCreate,
  InvoiceIssue,
  InvoicePayment,
  InvoiceVoid,
} from "../types/invoices";
import type { Payment } from "../types/orders";

export async function listInvoices(params?: {
  page?: number;
  page_size?: number;
  status?: string;
  customer_id?: string;
  branch_id?: string;
  invoice_number?: string;
}): Promise<Invoice[]> {
  const query = new URLSearchParams();
  if (params?.page) query.append("page", params.page.toString());
  if (params?.page_size) query.append("page_size", params.page_size.toString());
  if (params?.status) query.append("status", params.status);
  if (params?.customer_id) query.append("customer_id", params.customer_id);
  if (params?.branch_id) query.append("branch_id", params.branch_id);
  if (params?.invoice_number)
    query.append("invoice_number", params.invoice_number);

  const qs = query.toString() ? `?${query.toString()}` : "";
  return apiRequest<Invoice[]>(`/invoices${qs}`);
}

export async function getInvoice(invoiceId: string): Promise<Invoice> {
  return apiRequest<Invoice>(`/invoices/${invoiceId}`);
}

export async function createInvoice(data: InvoiceCreate): Promise<Invoice> {
  return apiRequest<Invoice>("/invoices", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function issueInvoice(
  invoiceId: string,
  data?: InvoiceIssue,
): Promise<Invoice> {
  return apiRequest<Invoice>(`/invoices/${invoiceId}/issue`, {
    method: "POST",
    body: data ? JSON.stringify(data) : undefined,
  });
}

export async function recordInvoicePayment(
  invoiceId: string,
  data: InvoicePayment,
): Promise<Payment> {
  return apiRequest<Payment>(`/invoices/${invoiceId}/payments`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function voidInvoice(
  invoiceId: string,
  data?: InvoiceVoid,
): Promise<Invoice> {
  return apiRequest<Invoice>(`/invoices/${invoiceId}/void`, {
    method: "POST",
    body: data ? JSON.stringify(data) : undefined,
  });
}
