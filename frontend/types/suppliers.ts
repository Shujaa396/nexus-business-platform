export type Supplier = {
  id: string;
  organization_id: string;
  name: string;
  email: string | null;
  phone: string | null;
  address: string | null;
  notes: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type SupplierCreate = {
  name: string;
  email?: string;
  phone?: string;
  address?: string;
  notes?: string;
};

export type SupplierUpdate = {
  name?: string;
  email?: string;
  phone?: string;
  address?: string;
  notes?: string;
  is_active?: boolean;
};
