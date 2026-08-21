export type Product = {
  id: string;
  sku: string;
  name: string;
  description: string | null;
  unit: string;
  cost_price: string | number;
  selling_price: string | number;
  tax_rate: string | number;
  category_id: string | null;
  supplier_id: string | null;
  is_active: boolean;
};

export type ProductCreate = {
  sku: string;
  name: string;
  description?: string;
  unit: string;
  cost_price: number;
  selling_price: number;
  tax_rate?: number;
  category_id?: string;
  supplier_id?: string;
};

export type ProductUpdate = {
  name?: string;
  description?: string;
  unit?: string;
  cost_price?: number;
  selling_price?: number;
  tax_rate?: number;
  is_active?: boolean;
  category_id?: string;
  supplier_id?: string;
};

export type Category = {
  id: string;
  name: string;
  description?: string | null;
  parent_id?: string | null;
  is_active: boolean;
  created_at?: string | null;
  updated_at?: string | null;
};

export type CategoryCreate = {
  name: string;
  description?: string;
  parent_id?: string;
};

export type CategoryUpdate = {
  name?: string;
  description?: string;
  parent_id?: string;
  is_active?: boolean;
};
