// src/ui/App.tsx
import { useContext } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { AuthContext } from "../state/AuthContext";
import { Sidebar } from "../layout/Sidebar";
import { ProtectedRoute } from "../routes/ProtectedRoute";
import { Unauthorized } from "./Unauthorized";
import { motion } from "framer-motion";
import { Loader } from "./Loader";
import { HomePage } from "./HomePage";
import { AdminPage } from "./admin/AdminPage";
import { AppHost } from "./AppHost";
import { LoginPage } from "./LoginPage";

import { ProductsPage } from "../pages/ProductsPage";
import { DelpiHealthPage } from "../pages/DelpiHealthPage";

import { MyProfile } from "./MyProfile";
import { NotificationsPage } from "./NotificationsPage";



const AnimatedWrapper = ({ children }: { children: React.ReactNode }) => (
  <motion.div
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0 }}
    transition={{ duration: 0.2 }}
  >
    {children}
  </motion.div>
);

function AppShell() {
  const { routes } = useContext(AuthContext);

  return (
    <div className="app-shell">
      <Sidebar />

      <div className="main-area">
        <div className="content">
          <Routes>
            <Route path="/delpi/products" element={<ProductsPage />} />
            <Route path="/delpi/health" element={<DelpiHealthPage />} />
            <Route path="/" element={<HomePage />} />
            <Route path="/profile" element={<MyProfile />} />
            <Route path="/notifications" element={<NotificationsPage />} />
            <Route path="/unauthorized" element={<Unauthorized />} />

            <Route
              path="/admin"
              element={
                <ProtectedRoute permission="rbac.manage">
                  <AdminPage />
                </ProtectedRoute>
              }
            />

            {routes.map((route) => (
              <Route
                key={route.path}
                path={route.path}
                element={
                  <ProtectedRoute permission={route.permission}>
                    <AnimatedWrapper>
                      <AppHost key={route.path} />
                    </AnimatedWrapper>
                  </ProtectedRoute>
                }
              />
            ))}

            {/* fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const { initialized, loading, isAuthenticated } = useContext(AuthContext);

  // 1) Espera init do keycloak (evita flicker)
  if (!initialized || loading) return <Loader />;

  // 2) Público: /login
  if (!isAuthenticated) {
    return (
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  // 3) Autenticado: shell normal
  return <AppShell />;
}