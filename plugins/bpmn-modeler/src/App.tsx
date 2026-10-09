import { useCallback } from "react";

import { ModelLibraryPage } from "./pages/ModelLibraryPage";
import { ModelEditorPage } from "./pages/ModelEditorPage";
import { RevisionViewPage } from "./pages/RevisionViewPage";
import { capabilitiesFromPermissions } from "./state/modelerCapabilities";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  permissions?: string[];
  pathname?: string;
};

const MODEL_RE = /^\/apps\/bpmn-modeler\/models\/([^/]+)$/;
const REVISION_RE = /^\/apps\/bpmn-modeler\/models\/([^/]+)\/revisions\/(\d+)$/;

export default function App({ getAccessToken, permissions, pathname }: AppProps) {
  const navigate = useCallback((path: string) => {
    window.history.pushState({}, "", path);
    window.dispatchEvent(new PopStateEvent("popstate"));
  }, []);

  const capabilities = capabilitiesFromPermissions(permissions);
  const base = pathname ?? "/apps/bpmn-modeler";

  const revisionMatch = REVISION_RE.exec(base);
  if (revisionMatch) {
    return (
      <RevisionViewPage
        modelId={revisionMatch[1]}
        revisionNumber={Number(revisionMatch[2])}
        getAccessToken={getAccessToken}
        navigate={navigate}
      />
    );
  }

  const modelMatch = MODEL_RE.exec(base);
  if (modelMatch) {
    return (
      <ModelEditorPage
        modelId={modelMatch[1]}
        getAccessToken={getAccessToken}
        permissions={permissions}
        navigate={navigate}
      />
    );
  }

  return (
    <ModelLibraryPage
      getAccessToken={getAccessToken}
      capabilities={capabilities}
      navigate={navigate}
    />
  );
}
