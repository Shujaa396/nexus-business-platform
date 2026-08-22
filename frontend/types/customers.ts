export type Customer = {
  id: string;
  organization_id: string;
  customer_code: string | null;
  name: string;
  company_name: string | null;
  email: string | null;
  phone: string | null;
  address: string | null;
  billing_address: string | null;
  shipping_address: string | null;
  status: string;
  notes: string | null;
  credit_limit: string;
  discount_percent: string;
  user_id: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type CustomerCreate = {
  name: string;
  customer_code?: string;
  company_name?: string;
  email?: string;
  phone?: string;
  address?: string;
  billing_address?: string;
  shipping_address?: string;
  status?: string;
  notes?: string;
  credit_limit?: string;
  discount_percent?: string;
};

export type CustomerUpdate = {
  name?: string;
  customer_code?: string;
  company_name?: string;
  email?: string;
  phone?: string;
  address?: string;
  billing_address?: string;
  shipping_address?: string;
  status?: string;
  notes?: string;
  credit_limit?: string;
  discount_percent?: string;
  is_active?: boolean;
};

export type CustomerSummary = {
  customer_id: string;
  order_count: number;
  invoice_count: number;
  payment_count: number;
  sales_total: string;
  invoiced_total: string;
  paid_total: string;
  outstanding_balance: string;
  overdue_amount: string;
};

export type CustomerPage = {
  items: Customer[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
};

export type CustomerPortalData = {
  customer: Customer;
  summary: CustomerSummary;
  contacts: CustomerContact[];
  addresses: CustomerAddress[];
  orders: Array<{ id: string; order_number: string; status: string; payment_status: string; total: string; created_at: string }>;
  invoices: Array<{ id: string; invoice_number: string; status: string; total: string; amount_paid: string; due_date: string | null; created_at: string }>;
  payments: CustomerPayment[];
};

export type CustomerContact = { id: string; customer_id: string; name: string; email: string | null; phone: string | null; job_title: string | null; is_primary: boolean; is_active: boolean; created_at: string; updated_at: string };
export type CustomerAddress = { id: string; customer_id: string; address_type: string; label: string | null; line1: string; line2: string | null; city: string | null; state: string | null; postal_code: string | null; country: string | null; is_primary: boolean; is_active: boolean; created_at: string; updated_at: string };
export type CustomerPayment = { id: string; order_id: string; order_number: string; invoice_number: string | null; amount: string; payment_method: string; reference: string | null; status: string; created_at: string; updated_at: string };
export type CustomerOrderDetail = CustomerPortalData["orders"][number] & { branch_id: string; customer_id: string | null; subtotal: string; discount: string; tax: string; notes: string | null; items: Array<{ id: string; product_id: string; product_name?: string | null; product_sku?: string | null; quantity: string; fulfilled_quantity?: string; unit_price: string; discount: string; tax: string; line_total: string }> };
export type CustomerInvoiceDetail = CustomerPortalData["invoices"][number] & { order_id: string; customer_id: string | null; issued_date: string | null; subtotal: string; discount: string; tax: string; line_items: Array<{ id: string; product_name: string; quantity: string; line_total: string }> };
export type CustomerInvoicePortalDetail = { invoice: CustomerInvoiceDetail; payments: CustomerPayment[] };
