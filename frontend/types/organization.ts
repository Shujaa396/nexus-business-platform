export type Member = {
  membership_id: string;
  user_id: string;
  email: string;
  full_name: string;
  role_name: "admin" | "manager" | "staff" | string;
  is_active: boolean;
  joined_at: string;
};

export type MemberCreate = {
  email: string;
  full_name: string;
  password: string;
  role_name: string;
};

export type MemberRoleUpdate = {
  role_name: string;
};

export type OrganizationUpdate = {
  name?: string;
  email?: string;
  phone?: string;
  address?: string;
  tax_number?: string;
  currency?: string;
};
