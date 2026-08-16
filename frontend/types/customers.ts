export type Customer = {
  id: string;
  name: string;
  email: string | null;
  phone: string | null;
  address: string | null;
  notes: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type CustomerCreate = {
  name: string;
  email?: string;
  phone?: string;
  address?: string;
  notes?: string;
};

export type CustomerUpdate = {
  name?: string;
  email?: string;
  phone?: string;
  address?: string;
  notes?: string;
};
