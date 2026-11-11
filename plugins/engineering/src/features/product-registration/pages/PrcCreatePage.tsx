/** Nova solicitação PRC — wrapper fino do formulário compartilhado
 * `PrcRequestForm` (@delpi/plugin-ui, PRC-REF-023-UI-FORM-UNIFICATION-05).
 * O MFE só fornece o adapter oficial da Engineering API, o escopo de
 * portal e a navegação; a composição do wizard é única para Portal
 * Engenharia e Minhas Solicitações. */

import { useMemo } from "react";

import { PrcRequestForm } from "@delpi/plugin-ui/index";
import { ENGINEERING_PORTAL_SCOPE } from "../../../ui/engineeringUi";
import {
  EngineeringPageHero,
  EngineeringPagePath,
} from "../../../ui/engineeringUi";
import {
  fetchPrcCatalog,
  fetchPrcEditContext,
  fetchPrcReferenceData,
  prcIntakeSubmit,
  searchPrcSuppliers,
  uploadPrcAttachment,
} from "../api/productRegistrationApi";
import {
  buildPrcQueueUrl,
  EMPTY_PRC_QUEUE_URL,
  navigatePrc,
  navigatePrcHref,
  PRC_PATHS,
} from "../prcNavigate";
import { PRC_COPY } from "../prcCopy";
import { PRC_PORTAL_SOURCE } from "../prcIntakePayload";

export function PrcCreatePage({ basePath }: { basePath: string }) {
  const dataProvider = useMemo(
    () => ({
      fetchReferenceData: (signal?: AbortSignal) =>
        fetchPrcReferenceData(signal).then((env) => env.data),
      fetchCatalog: (
        kind: string,
        query: string | undefined,
        signal: AbortSignal | undefined,
        limit: number,
      ) => fetchPrcCatalog(kind, query, signal, limit),
      searchSuppliers: (query: string, signal?: AbortSignal) =>
        searchPrcSuppliers(query, signal).then(
          (env) => env.data?.items || [],
        ),
      fetchEditContext: (officialCode: string) =>
        fetchPrcEditContext(officialCode).then((env) => env.data),
      submitIntake: (
        body: Parameters<typeof prcIntakeSubmit>[0],
        idempotencyKey: string,
      ) =>
        prcIntakeSubmit(body, idempotencyKey).then((env) => ({
          requestId: env.data.requestId,
        })),
      uploadAttachment: (requestId: string, file: File) =>
        uploadPrcAttachment(requestId, file).then(() => undefined),
    }),
    [],
  );

  const backToQueue = () =>
    navigatePrcHref(buildPrcQueueUrl(basePath, EMPTY_PRC_QUEUE_URL));

  return (
    <main className="engineering-prc">
      <EngineeringPagePath
        back={{
          label: PRC_COPY.detailBreadcrumb,
          href: `${basePath}/${PRC_PATHS.queue}`,
          onNavigate: (event) => {
            event.preventDefault();
            backToQueue();
          },
        }}
        items={[]}
        current={PRC_COPY.newRequest}
      />

      <EngineeringPageHero
        eyebrow={PRC_COPY.breadcrumbRoot}
        title={PRC_COPY.newRequest}
        description={PRC_COPY.intakeNote}
      />

      <PrcRequestForm
        source={PRC_PORTAL_SOURCE}
        dataProvider={dataProvider}
        portalScopeClassName={ENGINEERING_PORTAL_SCOPE}
        onCancel={backToQueue}
        onCompleted={(requestId) =>
          navigatePrc(PRC_PATHS.detail(requestId), basePath)
        }
      />
    </main>
  );
}
