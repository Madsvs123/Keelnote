import { useQuery, useQueryClient } from "@tanstack/react-query";
import clsx from "clsx";
import { LogOut } from "lucide-react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { useAuthStore } from "../store/auth";

export function Shell() {
  const username = useAuthStore((state) => state.username);
  const clear = useAuthStore((state) => state.clear);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const products = useQuery({ queryKey: ["products"], queryFn: api.products.list });

  function logout() {
    clear();
    queryClient.clear();
    navigate("/login");
  }

  return (
    <div className="shell">
      <aside className="sidebar">
        <NavLink to="/" className="brand">
          <span className="mark">K</span>
          <span>
            <strong>Keelnote</strong>
            <small>Release log</small>
          </span>
        </NavLink>
        <nav className="side-scroll">
          <NavLink to="/" end className={({ isActive }) => clsx("side-link", isActive && "is-active")}>
            <span>All products</span>
          </NavLink>
          {products.data?.map((product) => (
            <NavLink
              key={product.id}
              to={`/products/${product.id}`}
              className={({ isActive }) => clsx("side-link", isActive && "is-active")}
            >
              <span>{product.name}</span>
              <small>
                {product.latest ?? "No release"}
                {product.unreleased_count > 0 && <em className="count">{product.unreleased_count}</em>}
              </small>
            </NavLink>
          ))}
          {products.isLoading && <p className="muted">Loading products…</p>}
        </nav>
        <div className="side-foot">
          <span>{username}</span>
          <button type="button" className="text-button" onClick={logout}>
            <LogOut size={14} />
            Sign out
          </button>
        </div>
      </aside>
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}
