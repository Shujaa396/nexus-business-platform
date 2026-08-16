export type Branch = {
  id: string;
  code: string;
  name: string;
  address?: string | null;
  phone?: string | null;
  is_active: boolean;
  created_at?: string | null;
  updated_at?: string | null;
};

export type BranchCreate = {
  code: string;
  name: string;
  address?: string;
  phone?: string;
};

export type BranchUpdate = {
  code?: string;
  name?: string;
  address?: string;
  phone?: string;
  is_active?: boolean;
};
