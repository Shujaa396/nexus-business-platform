export type Warehouse = {
  id: string;
  organization_id: string;
  branch_id: string;
  name: string;
  code: string;
  address: string | null;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type WarehouseInventory = {
  id: string;
  organization_id: string;
  warehouse_id: string;
  product_id: string;
  quantity: string | number;
  reserved_quantity: string | number;
  available_quantity: string | number;
  reorder_level: string | number;
  reorder_quantity: string | number;
  inventory_value: string | number;
};

export type WarehouseCreate = { name: string; code: string; branch_id: string; address?: string; description?: string };
export type WarehouseUpdate = Partial<WarehouseCreate> & { is_active?: boolean };
