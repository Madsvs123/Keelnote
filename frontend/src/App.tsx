import { useEffect, useState, type ReactNode } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { Shell } from "./components/Shell";
import { LoginPage } from "./pages/LoginPage";
import { ProductPage } from "./pages/ProductPage";
import { ProductsPage } from "./pages/ProductsPage";
import { RegisterPage } from "./pages/RegisterPage";
import { VersionPage } from "./pages/VersionPage";
import { useAuthStore } from "./store/auth";

function BootGate({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(useAuthStore.persist.hasHydrated());

  useEffect(() => {
    const unsubscribe = useAuthStore.persist.onFinishHydration(() => setReady(true));
    if (useAuthStore.persist.hasHydrated()) setReady(true);
    return unsubscribe;
  }, []);

  if (!ready) return <div className="boot">Opening the log…</div>;
  return children;
}

function RequireAuth() {
  const access = useAuthStore((state) => state.access);
  if (!access) return <Navigate to="/login" replace />;
  return <Shell />;
}

export default function App() {
  return (
    <BootGate>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route element={<RequireAuth />}>
          <Route path="/" element={<ProductsPage />} />
          <Route path="/products/:productId" element={<ProductPage />} />
          <Route path="/products/:productId/versions/:versionId" element={<VersionPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BootGate>
  );
}
