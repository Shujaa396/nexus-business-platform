export type InventoryItem = {
  id: string;
  organization_id: string;
  branch_id: string;
  product_id: string;
  quantity: string | number;
  reorder_level: string | number;
  created_at: string;
  updated_at: string;
};

export type InventoryTransaction = {
  id: string;
  transaction_type: string;
  quantity: string | number;
  reference_type: string | null;
  reference_id: string | null;
  notes: string | null;
  created_by: string | null;
  created_at: string;
};

export type StockOpRequest = {
  branch_id: string;
  product_id: string;
  quantity: number;
  notes?: string;
};

export type InventoryAdjust = {
  branch_id: string;
  product_id: string;
  quantity: number;
  direction: "IN" | "OUT";
  notes?: string;
};
