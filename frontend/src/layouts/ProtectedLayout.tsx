import { Link, Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const links = [
  { to: "/", label: "Dashboard", icon: "▦" },
  { to: "/ingredient-detection", label: "Detect", icon: "▣" },
  { to: "/nutrition", label: "Nutrition", icon: "⌁" },
  { to: "/recipes", label: "Recipes", icon: "✣" },
  { to: "/diet-planner", label: "Diet Planner", icon: "⚖" },
  { to: "/shopping-list", label: "Shopping List", icon: "☷" },
  { to: "/history", label: "History", icon: "◷" },
  { to: "/profile", label: "Profile", icon: "♙" },
  { to: "/settings", label: "Settings", icon: "⚙" },
];

export function ProtectedLayout() {
  const { isAuthenticated, user, signOut } = useAuth();
  const location = useLocation();
  const currentPage = links.find((item) => item.to === location.pathname)?.label ?? "Kitchen command center";

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div>
          <p className="eyebrow">SmartChef Web</p>
          <h2>{user?.email ?? "Chef"}</h2>
        </div>
        <nav className="sidebar__nav">
          {links.map((item) => (
            <Link key={item.to} to={item.to} className={location.pathname === item.to ? "active" : ""}>
              <span className="sidebar__icon" aria-hidden="true">{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          ))}
        </nav>
        <button className="button button--ghost" onClick={() => void signOut()}>
          Sign out
        </button>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <p className="eyebrow">SmartChef</p>
            <h1>{currentPage}</h1>
          </div>
          <button className="button button--ghost topbar__signout" onClick={() => void signOut()}>
            Sign out
          </button>
        </header>
        <Outlet />
      </main>
    </div>
  );
}
