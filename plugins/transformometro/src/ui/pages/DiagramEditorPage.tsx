import { useMemo, useState } from "react";

import { EditorChromeNotice } from "@delpi/plugin-ui/index";

import type { AppProps } from "../../App";
import { TransformometroShell } from "../../components/TransformometroShell";
import { ProcessoDiagramSection } from "../../components/diagram/sections/ProcessoDiagramSection";
import { InstanciaDiagramEscopoSection } from "../../components/diagram/sections/InstanciaDiagramEscopoSection";
import { RevisaoDiagramSection } from "../../components/diagram/sections/RevisaoDiagramSection";
import { StatusAlerts } from "../../components/StatusAlerts";
import {
  buildInstanciaSectionHref,
  buildProcessoSecondaryHref,
  buildRevisaoSectionHref,
} from "../processes/processWorkspaceNav";

export type DiagramEditorKind = "processo" | "instancia" | "revisao";

type Props = Pick<AppProps, "getAccessToken"> & {
  kind: DiagramEditorKind;
  processoId: string;
  instanciaId?: string;
  revisaoId?: string;
  onNavigate: (path: string) => void;
};

const KIND_CONFIG: Record<DiagramEditorKind, { title: string }> = {
  processo: { title: "Diagrama macro legado" },
  instancia: { title: "Escopo de diagrama legado" },
  revisao: { title: "Diagrama de revisão legado" },
};

function backHref(input: {
  kind: DiagramEditorKind;
  processoId: string;
  instanciaId?: string;
  revisaoId?: string;
}): string {
  if (input.kind === "revisao" && input.instanciaId && input.revisaoId) {
    return buildRevisaoSectionHref(
      input.processoId,
      input.instanciaId,
      input.revisaoId,
      "diagrama",
    );
  }
  if (input.kind === "instancia" && input.instanciaId) {
    return buildInstanciaSectionHref(input.processoId, input.instanciaId, "diagrama");
  }
  return buildProcessoSecondaryHref(input.processoId, "fluxo");
}

/**
 * Deep-link legado (`/diagram/edit`) — agora viewer somente leitura.
 * flowchart_v1/scope/overlay não aceitam mais writes (LEGACY_DIAGRAM_READ_ONLY);
 * novos diagramas são BPMN nativos criados no detalhe do processo.
 */
export function DiagramEditorPage({
  getAccessToken,
  kind,
  processoId,
  instanciaId,
  revisaoId,
  onNavigate,
}: Props) {
  const config = KIND_CONFIG[kind];
  const detailHref = useMemo(
    () =>
      backHref({
        kind,
        processoId,
        instanciaId,
        revisaoId,
      }),
    [kind, processoId, instanciaId, revisaoId],
  );

  const [error, setError] = useState<string | null>(null);

  const chromeLeading = {
    onBack: () => onNavigate(detailHref),
    backLabel: "Voltar",
    title: config.title,
  };

  const chromeNotices = (
    <EditorChromeNotice tone="info">
      Mapeamento legado — somente leitura. Novos diagramas são BPMN nativos:
      crie ou importe pelo card «Modelo BPMN» no detalhe do processo.
    </EditorChromeNotice>
  );

  const missingIds =
    (kind === "instancia" && !instanciaId) || (kind === "revisao" && !revisaoId);

  return (
    <TransformometroShell>
      <div className="tm-diagram-editor-page">
        <StatusAlerts
          error={error}
          loading={false}
          hasData
          onRetry={() => setError(null)}
          onDismissError={() => setError(null)}
        />

        {missingIds ? (
          <p className="ds-hint">Identificadores incompletos para abrir o diagrama.</p>
        ) : (
          <div className="tm-diagram-editor-page__canvas">
            {kind === "processo" ? (
              <ProcessoDiagramSection
                variant="page"
                chromeLeading={chromeLeading}
                chromeNotices={chromeNotices}
                processoId={processoId}
                getAccessToken={getAccessToken}
                onError={setError}
              />
            ) : null}
            {kind === "instancia" && instanciaId ? (
              <InstanciaDiagramEscopoSection
                variant="page"
                chromeLeading={chromeLeading}
                chromeNotices={chromeNotices}
                processoId={processoId}
                instanciaId={instanciaId}
                getAccessToken={getAccessToken}
                onError={setError}
              />
            ) : null}
            {kind === "revisao" && revisaoId ? (
              <RevisaoDiagramSection
                variant="page"
                chromeLeading={chromeLeading}
                chromeNotices={chromeNotices}
                revisaoId={revisaoId}
                getAccessToken={getAccessToken}
                onError={setError}
              />
            ) : null}
          </div>
        )}
      </div>
    </TransformometroShell>
  );
}
