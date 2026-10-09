import { useMemo } from "react";

import { BpmnRevisionViewPage } from "@delpi/bpmn-editor";

import { ModelerDocumentHost } from "../data/ModelerDocumentHost";

type Props = {
  modelId: string;
  revisionNumber: number;
  getAccessToken?: () => string | undefined;
  navigate: (path: string) => void;
};

/** Wrapper Modeler: view de revisão histórica sobre o host do Modeler. */
export function RevisionViewPage({
  modelId,
  revisionNumber,
  getAccessToken,
  navigate,
}: Props) {
  const host = useMemo(
    () => new ModelerDocumentHost(modelId, getAccessToken),
    [modelId, getAccessToken],
  );

  return (
    <BpmnRevisionViewPage
      host={host}
      revisionNumber={revisionNumber}
      backLabel="Voltar ao modelo"
      backPath={`/apps/bpmn-modeler/models/${modelId}`}
      navigate={navigate}
    />
  );
}
