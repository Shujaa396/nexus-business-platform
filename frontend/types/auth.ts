export type User = {
    id: string;
    email: string;
    full_name: string;
    is_active: boolean;
    is_superadmin: boolean;
};

export type Organization = {
    id: string;
    name: string;
    slug: string;
    is_active: boolean;
};

export type AuthResponse = {
    access_token: string;
    refresh_token: string;
    token_type: string;
    user: User;
    organization: Organization;
};

export type MeResponse = User & {
    organization_id: string | null;
    organization_name: string | null;
};

export type LoginRequest = {
    email: string;
    password: string;
};

export type RegisterRequest = {
    email: string;
    password: string;
    full_name: string;
    organization_name: string;
    organization_slug: string;
};

export type TokenPairResponse = {
    access_token: string;
    refresh_token: string;
    token_type: string;
};