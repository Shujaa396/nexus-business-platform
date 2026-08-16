export type OrderItem = {
  id: string;
  order_id: string;
  product_id: string;
  quantity: string | number;
  unit_price: string | number;
  discount: string | number;
  tax: string | number;
  line_total: string | number;
};

export type Order = {
  id: string;
  organization_id: string;
  branch_id: string;
  customer_id: string | null;
  order_number: string;
  status: "DRAFT" | "CONFIRMED" | "COMPLETED" | "CANCELLED";
  subtotal: string | number;
  discount_total: string | number;
  tax_total: string | number;
  total: string | number;
  payment_status: "UNPAID" | "PARTIAL" | "PAID";
  notes: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
  items?: OrderItem[];
};

export type OrderItemCreate = {
  product_id: string;
  quantity: number;
  unit_price: number;
  discount?: number;
  tax?: number;
};

export type OrderCreate = {
  branch_id: string;
  customer_id?: string;
  items: OrderItemCreate[];
  notes?: string;
};

export type OrderUpdate = {
  customer_id?: string;
  items?: OrderItemCreate[];
  notes?: string;
};

export type Payment = {
  id: string;
  order_id: string;
  amount: string | number;
  payment_method: string;
  reference: string | null;
  status: "COMPLETED" | "REFUNDED";
  created_at: string;
};

export type PaymentCreate = {
  amount: number;
  payment_method: string;
  reference?: string;
};
