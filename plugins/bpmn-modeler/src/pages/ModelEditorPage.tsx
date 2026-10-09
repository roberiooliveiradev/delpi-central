import { useMemo } from "react";

import { BpmnDocumentEditorPage } from "@delpi/bpmn-editor";

import { ModelerDocumentHost } from "../data/ModelerDocumentHost";
import { capabilitiesFromPermissions } from "../state/modelerCapabilities";

type Props = {
  modelId: string;
  getAccessToken?: () => string | undefined;
  permissions?: string[];
  navigate: (path: string) => void;
};

/** Wrapper Modeler: injeta o host do próprio bounded context na superfície
 *  de edição compartilhada (G7 / ADR-006). */
export function ModelEditorPage({
  modelId,
  getAccessToken,
  permissions,
  navigate,
}: Props) {
  const host = useMemo(
    () => new ModelerDocumentHost(modelId, getAccessToken),
    [modelId, getAccessToken],
  );
  const capabilities = useMemo(
    () => capabilitiesFromPermissions(permissions),
    [permissions],
  );

  return (
    <BpmnDocumentEditorPage
      host={host}
      capabilities={capabilities}
      backLabel="Biblioteca"
      backPath="/apps/bpmn-modeler"
      revisionPathFor={(n) =>
        `/apps/bpmn-modeler/models/${modelId}/revisions/${n}`
      }
      lifecycle={{
        canManage: capabilities.manage,
        labelFor: (archived) => (archived ? "Desarquivar" : "Arquivar"),
        onToggle: (archived, v) => host.toggleArchive(archived, v),
      }}
      navigate={navigate}
    />
  );
}
