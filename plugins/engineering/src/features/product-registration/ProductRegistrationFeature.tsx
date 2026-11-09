/** Feature Product Registration — resolve sub-paths de
 * `/apps/engineering/product-registration` e renderiza fila/detalhe. */

import { useMemo } from "react";
import { PrcQueuePage } from "./pages/PrcQueuePage";
import { PrcDetailPage } from "./pages/PrcDetailPage";
import { PrcCreatePage } from "./pages/PrcCreatePage";
import { resolvePrcPath } from "./prcNavigate";

export function ProductRegistrationFeature({
  relativePath,
  basePath,
  getAccessToken,
}: {
  relativePath: string;
  basePath: string;
  getAccessToken?: () => string | undefined;
}) {
  const resolved = useMemo(() => resolvePrcPath(relativePath), [relativePath]);
  if (resolved.page === "create") {
    return <PrcCreatePage basePath={basePath} />;
  }
  if (resolved.page === "detail" && resolved.requestId) {
    return <PrcDetailPage
        requestId={resolved.requestId}
        basePath={basePath}
        getAccessToken={getAccessToken}
      />;
  }
  return <PrcQueuePage basePath={basePath} />;
}
