import { apiRequest } from "./api";
import type {
  InventoryAdjust,
  InventoryItem,
  InventoryTransaction,
  StockOpRequest,
} from "../types/inventory";

export async function listInventory(params?: {
  branch_id?: string;
  product_id?: string;
  low_stock?: boolean;
  page?: number;
  page_size?: number;
}): Promise<InventoryItem[]> {
  const query = new URLSearchParams();
  if (params?.branch_id) query.append("branch_id", params.branch_id);
  if (params?.product_id) query.append("product_id", params.product_id);
  if (params?.low_stock !== undefined)
    query.append("low_stock", params.low_stock.toString());
  if (params?.page) query.append("page", params.page.toString());
  if (params?.page_size) query.append("page_size", params.page_size.toString());

  const qs = query.toString() ? `?${query.toString()}` : "";
  return apiRequest<InventoryItem[]>(`/inventory${qs}`);
}

export async function getInventoryDetail(id: string): Promise<InventoryItem> {
  return apiRequest<InventoryItem>(`/inventory/${id}`);
}

export async function getInventoryTransactions(
  inventoryId: string,
  params?: {
    transaction_type?: string;
    page?: number;
    page_size?: number;
  },
): Promise<InventoryTransaction[]> {
  const query = new URLSearchParams();
  if (params?.transaction_type)
    query.append("transaction_type", params.transaction_type);
  if (params?.page) query.append("page", params.page.toString());
  if (params?.page_size) query.append("page_size", params.page_size.toString());

  const qs = query.toString() ? `?${query.toString()}` : "";
  return apiRequest<InventoryTransaction[]>(
    `/inventory/${inventoryId}/transactions${qs}`,
  );
}

export async function stockIn(
  data: StockOpRequest,
): Promise<InventoryTransaction> {
  return apiRequest<InventoryTransaction>("/inventory/stock-in", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function stockOut(
  data: StockOpRequest,
): Promise<InventoryTransaction> {
  return apiRequest<InventoryTransaction>("/inventory/stock-out", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function adjustStock(
  data: InventoryAdjust,
): Promise<InventoryTransaction> {
  return apiRequest<InventoryTransaction>("/inventory/adjust", {
    method: "POST",
    body: JSON.stringify(data),
  });
}
