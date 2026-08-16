export type DashboardSummaryResponse = {
  total_products: number;
  total_customers: number;
  total_orders: number;
  total_invoices: number;
  total_revenue: string | number;
  total_payments: string | number;
  pending_payments: string | number;
  low_stock_product_count: number;
  today_sales: string | number;
  today_orders: number;
  current_month_revenue: string | number;
};

export type SalesAnalyticsItem = {
  period: string;
  order_count: number;
  revenue: string | number;
  payment_total: string | number;
  invoice_total: string | number;
};

export type SalesAnalyticsResponse = {
  preset: string;
  start_date: string | null;
  end_date: string | null;
  total_orders: number;
  total_revenue: string | number;
  total_payments: string | number;
  total_invoices: string | number;
  breakdown: SalesAnalyticsItem[];
};

export type TopProductItem = {
  product_id: string;
  sku: string;
  name: string;
  units_sold: string | number;
  total_revenue: string | number;
};

export type LowStockItem = {
  inventory_item_id: string;
  product_id: string;
  branch_id: string;
  branch_name: string;
  sku: string;
  name: string;
  quantity: string | number;
  reorder_level: string | number;
};

export type ProductAnalyticsResponse = {
  top_selling_products: TopProductItem[];
  highest_revenue_products: TopProductItem[];
  low_stock_products: LowStockItem[];
  total_inventory_value: string | number;
};

export type TopCustomerItem = {
  customer_id: string;
  name: string;
  email: string | null;
  order_count: number;
  total_spent: string | number;
};

export type CustomerAnalyticsResponse = {
  total_customers: number;
  new_customers_in_period: number;
  top_customers: TopCustomerItem[];
};

export type BranchAnalyticsItem = {
  branch_id: string;
  code: string;
  name: string;
  order_count: number;
  revenue: string | number;
  inventory_items_count: number;
  inventory_value: string | number;
};

export type BranchAnalyticsResponse = {
  branches: BranchAnalyticsItem[];
};
