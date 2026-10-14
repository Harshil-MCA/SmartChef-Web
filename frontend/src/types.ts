export type User = {
  id: number;
  email: string;
  display_name?: string;
  photo_url?: string;
  date_joined?: string;
};

export type Profile = {
  id: number;
  email: string;
  display_name: string;
  photo_url: string;
  phone_number: string;
  theme_preference: "system" | "light" | "dark";
  unit_preference: "metric" | "imperial";
  language: string;
  notifications_enabled: boolean;
  dietary_preference: string;
  medical_restrictions: string;
  age: number | null;
  weight_kg: string | number | null;
  height_cm: string | number | null;
  gender: string;
  activity_level: string;
  created_at: string;
  updated_at: string;
};

export type AuthPayload = {
  access: string;
  refresh: string;
  user: User;
  profile?: Profile;
};

export type HistoryEntry = {
  id: number;
  entry_type: string;
  title: string;
  summary: string;
  payload: Record<string, unknown>;
  source_app: string;
  created_at: string;
};

export type ShoppingItem = {
  id: number;
  name: string;
  quantity: string;
  category: string;
  is_purchased: boolean;
  is_favorite: boolean;
  notes: string;
};

export type RecipeRecord = {
  id: number;
  recipe_name: string;
  description: string;
  ingredients: Array<{ name: string; quantity: string; unit: string }>;
  steps: string[];
  nutrition: Record<string, number | null>;
  estimated_cost: string;
  cook_time: string;
  difficulty: string;
  servings: string;
};

export type DietPlanRecord = {
  id: number;
  input_payload: Record<string, unknown>;
  result_payload: Record<string, any>;
  goal: string;
  daily_budget: number | string | null;
};
