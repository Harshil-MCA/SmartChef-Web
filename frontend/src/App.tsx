import { Navigate, Route, Routes } from "react-router-dom";
import { ProtectedLayout } from "./layouts/ProtectedLayout";
import { PublicLayout } from "./layouts/PublicLayout";
import { useAuth } from "./context/AuthContext";
import { LoginPage } from "./pages/auth/LoginPage";
import { SignupPage } from "./pages/auth/SignupPage";
import { ForgotPasswordPage } from "./pages/auth/ForgotPasswordPage";
import { DashboardPage } from "./pages/main/DashboardPage";
import { IngredientDetectionPage } from "./pages/main/IngredientDetectionPage";
import { NutritionPage } from "./pages/main/NutritionPage";
import { RecipesPage } from "./pages/main/RecipesPage";
import { DietPlannerPage } from "./pages/main/DietPlannerPage";
import { ShoppingListPage } from "./pages/main/ShoppingListPage";
import { HistoryPage } from "./pages/main/HistoryPage";
import { ProfilePage } from "./pages/main/ProfilePage";
import { SettingsPage } from "./pages/main/SettingsPage";

export default function App() {
  const { initialized, isAuthenticated } = useAuth();

  if (!initialized) {
    return (
      <div className="app-shell app-shell--center">
        <div className="hero-card hero-card--compact">
          <p className="eyebrow">SmartChef</p>
          <h1>Loading your kitchen workspace</h1>
          <p className="muted">Preparing your kitchen workspace.</p>
        </div>
      </div>
    );
  }

  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route path="/login" element={isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />} />
        <Route path="/signup" element={isAuthenticated ? <Navigate to="/" replace /> : <SignupPage />} />
        <Route path="/forgot-password" element={isAuthenticated ? <Navigate to="/" replace /> : <ForgotPasswordPage />} />
      </Route>

      <Route element={<ProtectedLayout />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/ingredient-detection" element={<IngredientDetectionPage />} />
        <Route path="/nutrition" element={<NutritionPage />} />
        <Route path="/recipes" element={<RecipesPage />} />
        <Route path="/diet-planner" element={<DietPlannerPage />} />
        <Route path="/shopping-list" element={<ShoppingListPage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>

      <Route
        path="*"
        element={<Navigate to={isAuthenticated ? "/" : "/login"} replace />}
      />
    </Routes>
  );
}
