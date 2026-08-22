import { apiRequest } from "./api";
import type { Warehouse, WarehouseCreate, WarehouseInventory, WarehouseUpdate } from "../types/warehouses";

export async function listWarehouses(params?: { page?: number; page_size?: number; q?: string }): Promise<Warehouse[]> {
  const query = new URLSearchParams();
  Object.entries(params ?? {}).forEach(([key, value]) => { if (value !== undefined && value !== "") query.set(key, String(value)); });
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return apiRequest<Warehouse[]>(`/warehouses${suffix}`);
}
export async function createWarehouse(data: WarehouseCreate): Promise<Warehouse> { return apiRequest<Warehouse>("/warehouses", { method: "POST", body: JSON.stringify(data) }); }
export async function updateWarehouse(id: string, data: WarehouseUpdate): Promise<Warehouse> { return apiRequest<Warehouse>(`/warehouses/${id}`, { method: "PATCH", body: JSON.stringify(data) }); }
export async function deactivateWarehouse(id: string): Promise<{ status: string }> { return apiRequest<{ status: string }>(`/warehouses/${id}`, { method: "DELETE" }); }
export async function listWarehouseInventory(params?: { warehouse_id?: string; low_stock?: boolean }): Promise<WarehouseInventory[]> {
  const query = new URLSearchParams();
  Object.entries(params ?? {}).forEach(([key, value]) => { if (value !== undefined) query.set(key, String(value)); });
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return apiRequest<WarehouseInventory[]>(`/inventory/by-warehouse${suffix}`);
}
