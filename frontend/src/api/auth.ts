import { apiFetch, clearTokens, setTokens } from "./client";
import { firebasePasswordReset, firebaseSignIn, firebaseSignUp } from "./firebaseAuth";
import type { AuthPayload, Profile } from "../types";

export async function login(email: string, password: string) {
  const firebase = await firebaseSignIn(email, password);
  const data = await apiFetch<AuthPayload>("/auth/firebase/", {
    method: "POST",
    body: JSON.stringify({ id_token: firebase.idToken, platform: "web" }),
  });
  setTokens(data.access, data.refresh);
  return data;
}

export async function signup(payload: {
  email: string;
  password: string;
  display_name: string;
}) {
  const firebase = await firebaseSignUp(payload.email, payload.password);
  const data = await apiFetch<AuthPayload>("/auth/firebase/", {
    method: "POST",
    body: JSON.stringify({ id_token: firebase.idToken, platform: "web", display_name: payload.display_name }),
  });
  setTokens(data.access, data.refresh);
  return data;
}

export async function logout() {
  const refresh = localStorage.getItem("smartchef_refresh") ?? "";
  try {
    await apiFetch("/auth/logout/", {
      method: "POST",
      body: JSON.stringify({ refresh }),
    });
  } finally {
    clearTokens();
  }
}

export async function loadCurrentUser() {
  return apiFetch<{ user: AuthPayload["user"]; profile: Profile }>("/auth/me/", {
    method: "GET",
  });
}

export async function requestPasswordReset(email: string) {
  await firebasePasswordReset(email);
  return { detail: "If an account exists, a password reset email has been sent.", email_exists: true };
}
