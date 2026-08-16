import { apiRequest } from "./api";
import type {
  Order,
  OrderCreate,
  OrderUpdate,
  Payment,
  PaymentCreate,
} from "../types/orders";

export async function listOrders(params?: {
  page?: number;
  page_size?: number;
  status?: string;
  payment_status?: string;
  customer_id?: string;
  branch_id?: string;
  order_number?: string;
}): Promise<Order[]> {
  const query = new URLSearchParams();
  if (params?.page) query.append("page", params.page.toString());
  if (params?.page_size) query.append("page_size", params.page_size.toString());
  if (params?.status) query.append("status", params.status);
  if (params?.payment_status)
    query.append("payment_status", params.payment_status);
  if (params?.customer_id) query.append("customer_id", params.customer_id);
  if (params?.branch_id) query.append("branch_id", params.branch_id);
  if (params?.order_number) query.append("order_number", params.order_number);

  const qs = query.toString() ? `?${query.toString()}` : "";
  return apiRequest<Order[]>(`/orders${qs}`);
}

export async function getOrderDetail(orderId: string): Promise<Order> {
  return apiRequest<Order>(`/orders/${orderId}`);
}

export async function createOrder(data: OrderCreate): Promise<Order> {
  return apiRequest<Order>("/orders", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateOrder(
  orderId: string,
  data: OrderUpdate,
): Promise<Order> {
  return apiRequest<Order>(`/orders/${orderId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function confirmOrder(orderId: string): Promise<Order> {
  return apiRequest<Order>(`/orders/${orderId}/confirm`, {
    method: "POST",
  });
}

export async function cancelOrder(orderId: string): Promise<Order> {
  return apiRequest<Order>(`/orders/${orderId}/cancel`, {
    method: "POST",
  });
}

export async function completeOrder(orderId: string): Promise<Order> {
  return apiRequest<Order>(`/orders/${orderId}/complete`, {
    method: "POST",
  });
}

export async function addOrderPayment(
  orderId: string,
  data: PaymentCreate,
): Promise<Payment> {
  return apiRequest<Payment>(`/orders/${orderId}/payments`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getOrderPayments(orderId: string): Promise<Payment[]> {
  return apiRequest<Payment[]>(`/orders/${orderId}/payments`);
}
