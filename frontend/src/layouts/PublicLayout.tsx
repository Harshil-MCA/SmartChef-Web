import { Outlet } from "react-router-dom";

export function PublicLayout() {
  return (
    <div className="auth-shell">
      <div className="auth-shell__panel">
        <Outlet />
      </div>
    </div>
  );
}
