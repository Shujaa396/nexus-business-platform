import { apiRequest } from "./api";
import type {
  AnalyticsDashboardData,
  AnalyticsFilters,
  AnalyticsIntent,
  AnalyticsResponse,
  BranchPerformance,
  InventorySummary,
  InvoiceSummary,
  NaturalLanguageResponse,
  PaymentSummary,
  ProcurementSummary,
  SalesSummary,
  SalesTrend,
  SupplierSummary,
  TopCustomers,
  TopProducts,
  WarehouseSummary,
} from "../types/analytics";

const endpoints: Record<AnalyticsIntent, string> = {
  sales_summary: "/analytics/sales-summary",
  sales_trend: "/analytics/sales-trend",
  top_products: "/analytics/top-products",
  top_customers: "/analytics/top-customers",
  branch_performance: "/analytics/branches",
  inventory_summary: "/analytics/inventory",
  payment_summary: "/analytics/payments",
  invoice_summary: "/analytics/invoices",
  supplier_summary: "/analytics/suppliers",
  procurement_summary: "/analytics/procurement",
  warehouse_summary: "/analytics/warehouses",
  sales_order_summary: "/analytics/sales-orders",
  fulfillment_summary: "/analytics/fulfillment",
  customer_sales: "/analytics/top-customers",
  outstanding_customer_balance: "/analytics/outstanding-customer-balance",
};

function queryString(filters: AnalyticsFilters = {}): string {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== "") params.set(key, String(value));
  });
  const query = params.toString();
  return query ? `?${query}` : "";
}

export async function getAnalytics<T>(
  intent: AnalyticsIntent,
  filters?: AnalyticsFilters,
): Promise<AnalyticsResponse<T>> {
  return apiRequest<AnalyticsResponse<T>>(`${endpoints[intent]}${queryString(filters)}`);
}

export async function getAnalyticsDashboard(
  filters: AnalyticsFilters,
): Promise<AnalyticsDashboardData> {
  const [summary, trend, products, customers, branches, inventory, payments, invoices, suppliers, procurement, warehouses] = await Promise.all([
    getAnalytics<SalesSummary>("sales_summary", filters),
    getAnalytics<SalesTrend>("sales_trend", filters),
    getAnalytics<TopProducts>("top_products", filters),
    getAnalytics<TopCustomers>("top_customers", filters),
    getAnalytics<BranchPerformance>("branch_performance", filters),
    getAnalytics<InventorySummary>("inventory_summary", filters),
    getAnalytics<PaymentSummary>("payment_summary", filters),
    getAnalytics<InvoiceSummary>("invoice_summary", filters),
    getAnalytics<SupplierSummary>("supplier_summary", filters),
    getAnalytics<ProcurementSummary>("procurement_summary", filters),
    getAnalytics<WarehouseSummary>("warehouse_summary", filters),
  ]);
  return { summary, trend, products, customers, branches, inventory, payments, invoices, suppliers, procurement, warehouses };
}

export async function askAnalytics(question: string): Promise<NaturalLanguageResponse> {
  return apiRequest<NaturalLanguageResponse>("/analytics/query", {
    method: "POST",
    body: JSON.stringify({ question }),
  });
}
