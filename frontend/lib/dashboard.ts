import { apiRequest } from "./api";
import type {
  BranchAnalyticsResponse,
  CustomerAnalyticsResponse,
  DashboardSummaryResponse,
  ProductAnalyticsResponse,
  SalesAnalyticsResponse,
} from "../types/dashboard";

export async function getDashboardSummary(): Promise<DashboardSummaryResponse> {
  return apiRequest<DashboardSummaryResponse>("/dashboard/summary");
}

export async function getSalesAnalytics(
  periodType: "daily" | "weekly" | "monthly" = "daily",
  preset?: string,
  startDate?: string,
  endDate?: string,
): Promise<SalesAnalyticsResponse> {
  const params = new URLSearchParams();
  if (preset) params.append("preset", preset);
  if (startDate) params.append("start_date", startDate);
  if (endDate) params.append("end_date", endDate);

  const queryString = params.toString() ? `?${params.toString()}` : "";
  return apiRequest<SalesAnalyticsResponse>(
    `/dashboard/sales/${periodType}${queryString}`,
  );
}

export async function getProductAnalytics(
  limit = 10,
): Promise<ProductAnalyticsResponse> {
  return apiRequest<ProductAnalyticsResponse>(
    `/dashboard/products?limit=${limit}`,
  );
}

export async function getCustomerAnalytics(
  preset?: string,
  startDate?: string,
  endDate?: string,
  limit = 10,
): Promise<CustomerAnalyticsResponse> {
  const params = new URLSearchParams();
  if (preset) params.append("preset", preset);
  if (startDate) params.append("start_date", startDate);
  if (endDate) params.append("end_date", endDate);
  params.append("limit", limit.toString());

  return apiRequest<CustomerAnalyticsResponse>(
    `/dashboard/customers?${params.toString()}`,
  );
}

export async function getBranchAnalytics(): Promise<BranchAnalyticsResponse> {
  return apiRequest<BranchAnalyticsResponse>("/dashboard/branches");
}
