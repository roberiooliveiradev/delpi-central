/** PRC-REF-023-UI-FORM-UNIFICATION-05 — wrapper fino do formulário
 * compartilhado `PrcRequestForm` (@delpi/plugin-ui), o mesmo wizard
 * consumido pelo Portal Engenharia. O MFE só fornece o adapter
 * oficial da Engineering API, o shell e o destino pós-envio.
 *
 * A autoridade de validação, workflow e identificador continua sendo
 * a Engineering API; `source` "my-requests" marca a origem do intake. */

import { useMemo } from "react";

import { PrcRequestForm } from "@delpi/plugin-ui/index";

import { AppShell } from "../../components/AppShell";
import { MR_PORTAL_SCOPE } from "../../ui/mrUi";
import {
  fetchPrcCatalog,
  fetchPrcEditContext,
  fetchPrcReferenceData,
  prcIntakeSubmit,
  searchPrcSuppliers,
  uploadPrcAttachment,
} from "./prcApi";

const PRC_SOURCE = "my-requests";

type Props = {
  onCancel: () => void;
  onDone: (requestId: string) => void;
};

export function PrcRequestPage({ onCancel, onDone }: Props) {
  const dataProvider = useMemo(
    () => ({
      fetchReferenceData: (signal?: AbortSignal) =>
        fetchPrcReferenceData(signal),
      fetchCatalog: (
        kind: string,
        query: string | undefined,
        signal: AbortSignal | undefined,
        limit: number,
      ) =>
        fetchPrcCatalog(kind, query, signal, limit).then((data) => ({
          data,
        })),
      searchSuppliers: searchPrcSuppliers,
      fetchEditContext: fetchPrcEditContext,
      submitIntake: (
        body: Parameters<typeof prcIntakeSubmit>[0],
        idempotencyKey: string,
      ) =>
        prcIntakeSubmit(body, idempotencyKey).then((result) => ({
          requestId: result.requestId,
        })),
      uploadAttachment: (requestId: string, file: File) =>
        uploadPrcAttachment(requestId, file).then(() => undefined),
    }),
    [],
  );

  return (
    <AppShell title="Matéria-prima / produto">
      <PrcRequestForm
        source={PRC_SOURCE}
        dataProvider={dataProvider}
        portalScopeClassName={MR_PORTAL_SCOPE}
        onCancel={onCancel}
        onCompleted={onDone}
      />
    </AppShell>
  );
}
