export type AnalyticsIntent =
  | "sales_summary"
  | "sales_trend"
  | "top_products"
  | "top_customers"
  | "branch_performance"
  | "inventory_summary"
  | "payment_summary"
  | "invoice_summary"
  | "supplier_summary"
  | "procurement_summary";

export type AnalyticsPeriod = "daily" | "weekly" | "monthly";

export type AnalyticsFilters = {
  date_from?: string;
  date_to?: string;
  branch_id?: string;
  limit?: number;
  period?: AnalyticsPeriod;
};

export type AnalyticsResponse<T> = {
  intent: AnalyticsIntent;
  date_from: string;
  date_to: string;
  data: T;
};

export type SalesSummary = {
  total_sales: string | number;
  order_count: number;
  average_order_value: string | number;
};

export type SalesTrend = {
  breakdown: Array<{
    period: string;
    sales: string | number;
    order_count: number;
  }>;
};

export type TopProducts = {
  products: Array<{
    product_id: string;
    sku: string;
    name: string;
    quantity: string | number;
    revenue: string | number;
  }>;
};

export type TopCustomers = {
  customers: Array<{
    customer_id: string;
    name: string;
    email: string | null;
    order_count: number;
    revenue: string | number;
  }>;
};

export type BranchPerformance = {
  branches: Array<{
    branch_id: string;
    code: string;
    name: string;
    order_count: number;
    sales: string | number;
  }>;
};

export type InventorySummary = {
  low_stock: InventoryRow[];
  out_of_stock: InventoryRow[];
  inventory_value: string | number;
};

export type InventoryRow = {
  product_id: string;
  sku: string;
  name: string;
  branch_id: string;
  branch_name: string;
  quantity: string | number;
  reorder_level: string | number;
};

export type PaymentSummary = {
  total: string | number;
  by_method: Array<{ method: string; total: string | number }>;
  by_status: Array<{ status: string; total: string | number }>;
};

export type InvoiceSummary = {
  total: string | number;
  invoice_count: number;
  status_counts: Record<string, number>;
  overdue_count: number;
};

export type SupplierSummary = {
  suppliers: Array<{
    supplier_id: string;
    supplier_name: string;
    product_count: number;
    inventory_value: string | number;
  }>;
};

export type ProcurementSummary = {
  purchase_order_count: number;
  pending_approvals: number;
  pending_receipts: number;
  purchasing_total: string | number;
  status_counts: Record<string, number>;
  top_suppliers: Array<{ supplier_id: string; supplier_name: string; purchase_order_count: number; purchasing_total: string | number }>;
};

export type AnalyticsDashboardData = {
  summary: AnalyticsResponse<SalesSummary>;
  trend: AnalyticsResponse<SalesTrend>;
  products: AnalyticsResponse<TopProducts>;
  customers: AnalyticsResponse<TopCustomers>;
  branches: AnalyticsResponse<BranchPerformance>;
  inventory: AnalyticsResponse<InventorySummary>;
  payments: AnalyticsResponse<PaymentSummary>;
  invoices: AnalyticsResponse<InvoiceSummary>;
  suppliers: AnalyticsResponse<SupplierSummary>;
  procurement: AnalyticsResponse<ProcurementSummary>;
};

export type NaturalLanguageResponse = {
  supported: boolean;
  message: string;
  intent: AnalyticsIntent | null;
  date_from: string | null;
  date_to: string | null;
  data: Record<string, unknown> | null;
};
