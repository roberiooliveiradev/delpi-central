/** Feature Product Registration — resolve sub-paths de
 * `/apps/engineering/product-registration` e renderiza fila/detalhe. */

import { useMemo } from "react";
import { navigateEngineeringView } from "../../app/engineeringRoutes";
import { PrcQueuePage } from "./pages/PrcQueuePage";
import { PrcDetailPage } from "./pages/PrcDetailPage";

export function resolvePrcPath(relativePath: string): {
  page: "queue" | "detail";
  requestId?: string;
} {
  const parts = relativePath
    .replace(/^product-registration\/?/, "")
    .split("/")
    .filter(Boolean);
  if (parts.length >= 1 && /^[0-9a-fA-F-]{36}$/.test(parts[0])) {
    return { page: "detail", requestId: parts[0] };
  }
  return { page: "queue" };
}

export function ProductRegistrationFeature({
  relativePath,
  basePath,
}: {
  relativePath: string;
  basePath: string;
}) {
  const resolved = useMemo(() => resolvePrcPath(relativePath), [relativePath]);
  if (resolved.page === "detail" && resolved.requestId) {
    return (
      <PrcDetailPage
        requestId={resolved.requestId}
        onBack={() =>
          navigateEngineeringView("product-registration", { basePath })
        }
      />
    );
  }
  return <PrcQueuePage basePath={basePath} />;
}
