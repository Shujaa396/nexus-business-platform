import { apiRequest } from "./api";
import type {
  Category,
  CategoryCreate,
  CategoryUpdate,
  Product,
  ProductCreate,
  ProductUpdate,
} from "../types/products";

export async function listProducts(params?: {
  page?: number;
  page_size?: number;
  q?: string;
  category_id?: string;
}): Promise<Product[]> {
  const query = new URLSearchParams();
  if (params?.page) query.append("page", params.page.toString());
  if (params?.page_size) query.append("page_size", params.page_size.toString());
  if (params?.q) query.append("q", params.q);
  if (params?.category_id) query.append("category_id", params.category_id);

  const qs = query.toString() ? `?${query.toString()}` : "";
  return apiRequest<Product[]>(`/products${qs}`);
}

export async function getProduct(id: string): Promise<Product> {
  return apiRequest<Product>(`/products/${id}`);
}

export async function createProduct(data: ProductCreate): Promise<Product> {
  return apiRequest<Product>("/products", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateProduct(
  id: string,
  data: ProductUpdate,
): Promise<Product> {
  return apiRequest<Product>(`/products/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deleteProduct(id: string): Promise<{ status: string }> {
  return apiRequest<{ status: string }>(`/products/${id}`, {
    method: "DELETE",
  });
}

// Category services
export async function listCategories(params?: {
  page?: number;
  page_size?: number;
}): Promise<Category[]> {
  const query = new URLSearchParams();
  if (params?.page) query.append("page", params.page.toString());
  if (params?.page_size) query.append("page_size", params.page_size.toString());

  const qs = query.toString() ? `?${query.toString()}` : "";
  return apiRequest<Category[]>(`/categories${qs}`);
}

export async function getCategory(id: string): Promise<Category> {
  return apiRequest<Category>(`/categories/${id}`);
}

export async function createCategory(data: CategoryCreate): Promise<Category> {
  return apiRequest<Category>("/categories", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateCategory(
  id: string,
  data: CategoryUpdate,
): Promise<Category> {
  return apiRequest<Category>(`/categories/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deleteCategory(id: string): Promise<{ status: string }> {
  return apiRequest<{ status: string }>(`/categories/${id}`, {
    method: "DELETE",
  });
}
