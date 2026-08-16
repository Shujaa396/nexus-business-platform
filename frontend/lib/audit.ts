import { apiRequest } from "./api";
import type { AuditLog } from "../types/audit";

export async function listAuditLogs(params?: {
  page?: number;
  page_size?: number;
  action?: string;
  entity_type?: string;
  user_id?: string;
}): Promise<AuditLog[]> {
  const query = new URLSearchParams();
  if (params?.page) query.append("page", params.page.toString());
  if (params?.page_size) query.append("page_size", params.page_size.toString());
  if (params?.action) query.append("action", params.action);
  if (params?.entity_type) query.append("entity_type", params.entity_type);
  if (params?.user_id) query.append("user_id", params.user_id);

  const qs = query.toString() ? `?${query.toString()}` : "";
  return apiRequest<AuditLog[]>(`/audit-logs${qs}`);
}
