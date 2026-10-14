const FIREBASE_API_KEY = import.meta.env.VITE_FIREBASE_WEB_API_KEY ?? "";
const FIREBASE_AUTH_URL = "https://identitytoolkit.googleapis.com/v1";

type FirebaseAuthResponse = {
  idToken: string;
  localId: string;
  email: string;
  refreshToken?: string;
};

async function firebaseRequest<T>(endpoint: string, body: Record<string, unknown>): Promise<T> {
  if (!FIREBASE_API_KEY) {
    throw new Error("Firebase Web Authentication is not configured.");
  }
  const response = await fetch(`${FIREBASE_AUTH_URL}/${endpoint}?key=${FIREBASE_API_KEY}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const code = payload?.error?.message ?? "FIREBASE_AUTH_FAILED";
    const messages: Record<string, string> = {
      INVALID_LOGIN_CREDENTIALS: "The email or password is incorrect.",
      EMAIL_EXISTS: "An account already exists for that email.",
      INVALID_PASSWORD: "The email or password is incorrect.",
      USER_DISABLED: "This account has been disabled.",
      TOO_MANY_ATTEMPTS_TRY_LATER: "Too many attempts. Please try again later.",
    };
    throw new Error(messages[code] ?? code.replaceAll("_", " "));
  }
  return payload as T;
}

export function firebaseSignIn(email: string, password: string) {
  return firebaseRequest<FirebaseAuthResponse>("accounts:signInWithPassword", {
    email,
    password,
    returnSecureToken: true,
  });
}

export function firebaseSignUp(email: string, password: string) {
  return firebaseRequest<FirebaseAuthResponse>("accounts:signUp", {
    email,
    password,
    returnSecureToken: true,
  });
}

export function firebasePasswordReset(email: string) {
  return firebaseRequest("accounts:sendOobCode", {
    requestType: "PASSWORD_RESET",
    email,
  });
}
