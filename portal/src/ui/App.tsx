// src/ui/App.tsx
import {
  lazy,
  Suspense,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { AuthContext } from "../state/AuthContext";
import { Sidebar } from "../layout/Sidebar";
import { PortalMobileNavBar } from "../layout/PortalMobileNavBar";
import { ProtectedRoute } from "../routes/ProtectedRoute";
import { Unauthorized } from "./Unauthorized";
import { motion } from "framer-motion";
import { Loader } from "./Loader";
import { HomePage } from "./HomePage";
import { AppHost } from "./AppHost";
import { LoginPage } from "./LoginPage";
import { ConsentModal } from "./ConsentModal";
import { PortalTour } from "../tour/PortalTour";

import { ProductsPage } from "../pages/ProductsPage";
import { DelpiHealthPage } from "../pages/DelpiHealthPage";

import { MyProfile } from "./MyProfile";
import { NotificationsPage } from "./NotificationsPage";
import { PrivacyPage } from "./PrivacyPage";
import { PrivacyPolicyPage } from "./PrivacyPolicyPage";

import { ConfirmDialogProvider } from "../components/ConfirmDialogProvider";
import { ApiClient } from "../data/apiClient";
import { CoreApi } from "../data/coreApi";

const AdminPage = lazy(() =>
  import("./admin/AdminPage").then((module) => ({
    default: module.AdminPage,
  })),
);
const ManifestEditorPage = lazy(() =>
  import("./admin/manifest/ManifestEditorPage").then((module) => ({
    default: module.ManifestEditorPage,
  })),
);
const PluginVersionsPage = lazy(() =>
  import("./admin/versions/PluginVersionsPage").then((module) => ({
    default: module.PluginVersionsPage,
  })),
);
const RoleEditPage = lazy(() =>
  import("./admin/rbac/RoleEditPage").then((module) => ({
    default: module.RoleEditPage,
  })),
);
const GroupEditPage = lazy(() =>
  import("./admin/rbac/GroupEditPage").then((module) => ({
    default: module.GroupEditPage,
  })),
);
const UserEditPage = lazy(() =>
  import("./admin/rbac/UserEditPage").then((module) => ({
    default: module.UserEditPage,
  })),
);



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

function normalizeAppBasePath(basePath: string) {
  const normalized = basePath.startsWith("/") ? basePath : `/${basePath}`;
  return normalized.replace(/\/+$/, "") || "/";
}

function AppShell() {
  const { routes, apps } = useContext(AuthContext);

  const federatedAppHosts = useMemo(() => {
    return apps
      .filter((app) => app.renderMode === "federated")
      .map((app) => {
        const basePath = normalizeAppBasePath(app.basePath);
        const mainRoute =
          app.routes?.find((route) => route.showInMenu !== false) ?? app.routes?.[0];

        if (!mainRoute?.permission) {
          return null;
        }

        return {
          appId: app.id,
          basePath,
          path: `${basePath}/*`,
          permission: mainRoute.permission,
        };
      })
      .filter(
        (route): route is { appId: string; basePath: string; path: string; permission: string } =>
          route !== null,
      );
  }, [apps]);

  const embeddedAppHosts = useMemo(() => {
    return apps
      .filter((app) => app.renderMode === "embedded")
      .map((app) => {
        const basePath = normalizeAppBasePath(app.basePath);
        const mainRoute =
          app.routes?.find((route) => route.showInMenu !== false) ?? app.routes?.[0];

        if (!mainRoute?.permission) {
          return null;
        }

        return {
          appId: app.id,
          basePath,
          path: `${basePath}/*`,
          permission: mainRoute.permission,
        };
      })
      .filter(
        (route): route is { appId: string; basePath: string; path: string; permission: string } =>
          route !== null,
      );
  }, [apps]);

  const isFederatedAppRoute = useCallback(
    (path: string) => {
      const normalized = normalizeAppBasePath(path);

      return federatedAppHosts.some(
        (host) =>
          normalized === host.basePath ||
          normalized.startsWith(`${host.basePath}/`),
      );
    },
    [federatedAppHosts],
  );

  const isEmbeddedAppRoute = useCallback(
    (path: string) => {
      const normalized = normalizeAppBasePath(path);

      return embeddedAppHosts.some(
        (host) =>
          normalized === host.basePath ||
          normalized.startsWith(`${host.basePath}/`),
      );
    },
    [embeddedAppHosts],
  );

  const staticPluginRoutes = useMemo(
    () =>
      routes.filter(
        (route) => !isFederatedAppRoute(route.path) && !isEmbeddedAppRoute(route.path),
      ),
    [routes, isFederatedAppRoute, isEmbeddedAppRoute],
  );

  return (
    <div className="app-shell">
      <Sidebar />
      <PortalTour />

      <div className="main-area">
        <div className="content">
          <Suspense fallback={<Loader />}>
            <Routes>
            <Route path="/delpi/products" element={<ProductsPage />} />
            <Route path="/delpi/health" element={<DelpiHealthPage />} />
            <Route path="/" element={<HomePage />} />
            <Route path="/profile" element={<MyProfile />} />
            <Route path="/privacy" element={<PrivacyPage />} />
            <Route path="/privacy-policy" element={<PrivacyPolicyPage />} />
            <Route path="/notifications" element={<NotificationsPage />} />
            <Route
              path="/unauthorized"
              element={
                <AnimatedWrapper>
                  <Unauthorized />
                </AnimatedWrapper>
              }
            />

            <Route
              path="/admin"
              element={
                <ProtectedRoute permission="rbac.manage">
                  <AdminPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="/admin/apps/manifest/new"
              element={
                <ProtectedRoute permission="rbac.manage">
                  <ManifestEditorPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/apps/:appId/manifest"
              element={
                <ProtectedRoute permission="rbac.manage">
                  <ManifestEditorPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="/admin/apps/:appId/versions"
              element={
                <ProtectedRoute permission="rbac.manage">
                  <PluginVersionsPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="/admin/roles/new"
              element={
                <ProtectedRoute permission="rbac.manage">
                  <RoleEditPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/roles/:roleId"
              element={
                <ProtectedRoute permission="rbac.manage">
                  <RoleEditPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="/admin/groups/new"
              element={
                <ProtectedRoute permission="rbac.manage">
                  <GroupEditPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/groups/:groupId"
              element={
                <ProtectedRoute permission="rbac.manage">
                  <GroupEditPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="/admin/users/:userId"
              element={
                <ProtectedRoute permission="rbac.manage">
                  <UserEditPage />
                </ProtectedRoute>
              }
            />

            {staticPluginRoutes.map((route) => (
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

            {federatedAppHosts.map((host) => (
              <Route
                key={host.appId}
                path={host.path}
                element={
                  <ProtectedRoute permission={host.permission}>
                    <AppHost key={host.appId} />
                  </ProtectedRoute>
                }
              />
            ))}

            {embeddedAppHosts.map((host) => (
              <Route
                key={host.appId}
                path={host.path}
                element={
                  <ProtectedRoute permission={host.permission}>
                    <AppHost key={host.appId} />
                  </ProtectedRoute>
                }
              />
            ))}

            {/* fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Suspense>
        </div>
      </div>

      <PortalMobileNavBar />
    </div>
  );
}

function useConsentCheck() {
  const { isAuthenticated, getAccessToken, coreLoaded } = useContext(AuthContext);
  const [status, setStatus] = useState<"loading" | "pending" | "accepted">("loading");
  const checkedRef = useRef(false);

  useEffect(() => {
    if (!isAuthenticated || !coreLoaded) return;
    if (checkedRef.current) return;
    checkedRef.current = true;

    async function check() {
      try {
        const client = new ApiClient("", getAccessToken);
        const api = new CoreApi(client);
        const raw = await api.getConsentsRaw();
        const hasRequired = raw.items.some(
          (c) => c.purpose === "data_processing" && c.granted,
        );
        setStatus(hasRequired ? "accepted" : "pending");
      } catch {
        setStatus("pending");
      }
    }

    void check();
  }, [isAuthenticated, coreLoaded, getAccessToken]);

  const markAccepted = useCallback(() => setStatus("accepted"), []);

  return { status, markAccepted };
}

export default function App() {
  const { initialized, loading, isAuthenticated } = useContext(AuthContext);
  const { status: consentStatus, markAccepted } = useConsentCheck();

  if (!initialized || loading) return <Loader />;

  if (!isAuthenticated) {
    return (
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  if (consentStatus === "loading") return <Loader />;
  if (consentStatus === "pending") return <ConsentModal onAccepted={markAccepted} />;

  return (
    <ConfirmDialogProvider>
      <AppShell />
    </ConfirmDialogProvider>
  );
}