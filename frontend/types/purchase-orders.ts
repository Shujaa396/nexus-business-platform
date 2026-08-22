export type PurchaseOrderStatus =
  | "DRAFT"
  | "SUBMITTED"
  | "APPROVED"
  | "PARTIALLY_RECEIVED"
  | "RECEIVED"
  | "CANCELLED";

export type PurchaseOrderItem = {
  id: string;
  product_id: string;
  quantity: string | number;
  received_quantity: string | number;
  unit_cost: string | number;
  subtotal: string | number;
};

export type PurchaseOrder = {
  id: string;
  organization_id: string;
  supplier_id: string;
  branch_id: string;
  warehouse_id: string | null;
  purchase_order_number: string;
  status: PurchaseOrderStatus;
  order_date: string;
  expected_delivery_date: string | null;
  subtotal: string | number;
  tax: string | number;
  discount: string | number;
  total: string | number;
  notes: string | null;
  created_by: string | null;
  items: PurchaseOrderItem[];
  created_at: string;
  updated_at: string;
};

export type PurchaseOrderItemCreate = {
  product_id: string;
  quantity: number;
  unit_cost: number;
};

export type PurchaseOrderCreate = {
  supplier_id: string;
  branch_id: string;
  warehouse_id?: string;
  order_date?: string;
  expected_delivery_date?: string;
  tax?: number;
  discount?: number;
  notes?: string;
  items: PurchaseOrderItemCreate[];
};

export type PurchaseOrderUpdate = Partial<Omit<PurchaseOrderCreate, "items">> & {
  items?: PurchaseOrderItemCreate[];
};

export type ReceivePurchaseOrder = {
  receipt_reference: string;
  notes?: string;
  items: Array<{ item_id: string; quantity: number }>;
};

export type StatusTransitionResponse = {
  purchase_order: PurchaseOrder;
};
