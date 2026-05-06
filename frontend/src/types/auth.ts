// types/auth.ts
export interface User {
  id?: number;
  username: string;
  email?: string;
  created_at?: string;
  is_active?: boolean;
  minio_bucket?: string;
  minio_folder?: string;
  is_admin?: boolean;
  roles?: string[];
}

export interface LoginData {
  username: string;
  password: string;
}

export interface RegisterData {
  username: string;
  email?: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  refresh_token: string;
  user?: User;
}

export interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (username: string, password: string) => Promise<User>;
  logout: () => void;
  isLoading: boolean;
  register: (data: RegisterData) => Promise<User>;
  updateUser: (user: Partial<User>) => Promise<void>;
}