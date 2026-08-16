export type InvoiceLineItem = {
  id: string;
  invoice_id: string;
  product_id: string;
  description: string;
  quantity: string | number;
  unit_price: string | number;
  discount: string | number;
  tax: string | number;
  line_total: string | number;
};

export type Invoice = {
  id: string;
  organization_id: string;
  branch_id: string;
  customer_id: string | null;
  order_id: string;
  invoice_number: string;
  status: "DRAFT" | "ISSUED" | "PAID" | "PARTIAL" | "VOID";
  subtotal: string | number;
  discount_total: string | number;
  tax_total: string | number;
  total: string | number;
  amount_paid: string | number;
  issue_date: string | null;
  due_date: string | null;
  notes: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
  line_items?: InvoiceLineItem[];
};

export type InvoiceCreate = {
  order_id: string;
  due_date?: string;
  notes?: string;
};

export type InvoiceIssue = {
  due_date?: string;
  notes?: string;
};

export type InvoicePayment = {
  amount: number;
  payment_method: string;
  reference?: string;
};

export type InvoiceVoid = {
  notes?: string;
};
