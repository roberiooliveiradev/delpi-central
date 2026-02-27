// src/ui/App.tsx

import { useContext } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthContext } from "../state/AuthContext";
import { Sidebar } from "../layout/Sidebar";
import { ProtectedRoute } from "../routes/ProtectedRoute";
import { Unauthorized } from "./Unauthorized";
import { motion } from "framer-motion";
import { Loader } from "./Loader";
import { HomePage } from "./HomePage";
import { AdminPage } from "./admin/AdminPage";
import { AppHost } from "./AppHost";

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


const DummyPage = ({ title }: { title: string }) => (
  <div>
    <h2>{title}</h2>
    <p>Conteúdo do módulo.</p>
  </div>
);

const App = () => {
  const { isAuthenticated, routes } = useContext(AuthContext);

  if (!isAuthenticated) {
    return <Loader />;
  }


  return (
    <BrowserRouter>
      <div className="app-shell">
        <Sidebar />

        <div className="main-area">

          <div className="content">
            <Routes>
              <Route path="/" element={<HomePage />} />
              
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
                        <AppHost />
                    </AnimatedWrapper>
                  </ProtectedRoute>

                  }
                />
              ))}
            </Routes>
          </div>
        </div>
      </div>
    </BrowserRouter>
  );
};

export default App;

