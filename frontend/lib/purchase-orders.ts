import { apiRequest } from "./api";
import type {
  PurchaseOrder,
  PurchaseOrderCreate,
  PurchaseOrderUpdate,
  ReceivePurchaseOrder,
  StatusTransitionResponse,
} from "../types/purchase-orders";

export async function listPurchaseOrders(params?: {
  page?: number;
  page_size?: number;
  supplier_id?: string;
  branch_id?: string;
  status?: string;
  date_from?: string;
  date_to?: string;
  purchase_order_number?: string;
}): Promise<PurchaseOrder[]> {
  const query = new URLSearchParams();
  Object.entries(params ?? {}).forEach(([key, value]) => {
    if (value !== undefined && value !== "") query.set(key, String(value));
  });
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return apiRequest<PurchaseOrder[]>(`/purchase-orders${suffix}`);
}

export async function getPurchaseOrder(id: string): Promise<PurchaseOrder> {
  return apiRequest<PurchaseOrder>(`/purchase-orders/${id}`);
}

export async function createPurchaseOrder(data: PurchaseOrderCreate): Promise<PurchaseOrder> {
  return apiRequest<PurchaseOrder>("/purchase-orders", { method: "POST", body: JSON.stringify(data) });
}

export async function updatePurchaseOrder(id: string, data: PurchaseOrderUpdate): Promise<PurchaseOrder> {
  return apiRequest<PurchaseOrder>(`/purchase-orders/${id}`, { method: "PATCH", body: JSON.stringify(data) });
}

export async function submitPurchaseOrder(id: string): Promise<StatusTransitionResponse> {
  return apiRequest<StatusTransitionResponse>(`/purchase-orders/${id}/submit`, { method: "POST" });
}

export async function approvePurchaseOrder(id: string): Promise<StatusTransitionResponse> {
  return apiRequest<StatusTransitionResponse>(`/purchase-orders/${id}/approve`, { method: "POST" });
}

export async function cancelPurchaseOrder(id: string): Promise<StatusTransitionResponse> {
  return apiRequest<StatusTransitionResponse>(`/purchase-orders/${id}/cancel`, { method: "POST" });
}

export async function receivePurchaseOrder(id: string, data: ReceivePurchaseOrder): Promise<PurchaseOrder> {
  return apiRequest<PurchaseOrder>(`/purchase-orders/${id}/receive`, { method: "POST", body: JSON.stringify(data) });
}
