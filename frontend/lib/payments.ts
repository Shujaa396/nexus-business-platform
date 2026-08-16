import { apiRequest } from "./api";
import type { Payment } from "../types/orders";

export async function listPayments(params?: {
  page?: number;
  page_size?: number;
  order_id?: string;
  status?: string;
  payment_method?: string;
}): Promise<Payment[]> {
  const query = new URLSearchParams();
  if (params?.page) query.append("page", params.page.toString());
  if (params?.page_size) query.append("page_size", params.page_size.toString());
  if (params?.order_id) query.append("order_id", params.order_id);
  if (params?.status) query.append("status", params.status);
  if (params?.payment_method)
    query.append("payment_method", params.payment_method);

  const qs = query.toString() ? `?${query.toString()}` : "";
  return apiRequest<Payment[]>(`/payments${qs}`);
}

export async function refundPayment(paymentId: string): Promise<Payment> {
  return apiRequest<Payment>(`/payments/${paymentId}/refund`, {
    method: "POST",
  });
}
