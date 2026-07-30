import { useEffect, useMemo, useState } from "react";

import type { AppProps } from "../../App";
import { CollaborativePresenceBanner } from "../../components/collaboration/CollaborativePresenceBanner";
import { TransformometroShell } from "../../components/TransformometroShell";
import { ProcessoDiagramSection } from "../../components/diagram/sections/ProcessoDiagramSection";
import { InstanciaDiagramEscopoSection } from "../../components/diagram/sections/InstanciaDiagramEscopoSection";
import { RevisaoDiagramSection } from "../../components/diagram/sections/RevisaoDiagramSection";
import { StatusAlerts } from "../../components/StatusAlerts";
import type { CollaborationEntityType } from "../../data/api/transformometroCollaborationApi";
import { useCollaborativeSectionEdit } from "../../hooks/useCollaborativeSectionEdit";
import {
  buildInstanciaSectionHref,
  buildProcessoSectionHref,
  buildRevisaoSectionHref,
} from "../processos/processoWorkspaceNav";

export type DiagramEditorKind = "processo" | "instancia" | "revisao";

type Props = Pick<AppProps, "getAccessToken"> & {
  kind: DiagramEditorKind;
  processoId: string;
  instanciaId?: string;
  revisaoId?: string;
  onNavigate: (path: string) => void;
};

const KIND_CONFIG: Record<
  DiagramEditorKind,
  {
    title: string;
    sectionKey: string;
    entityType: CollaborationEntityType;
  }
> = {
  processo: {
    title: "Editar diagrama macro",
    sectionKey: "diagrama_macro",
    entityType: "processo",
  },
  instancia: {
    title: "Editar escopo no diagrama",
    sectionKey: "diagrama_escopo",
    entityType: "processo_instancia",
  },
  revisao: {
    title: "Editar diagrama da revisão",
    sectionKey: "diagrama_revisao",
    entityType: "revisao",
  },
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
  return buildProcessoSectionHref(input.processoId, "diagrama");
}

export function DiagramEditorPage({
  getAccessToken,
  kind,
  processoId,
  instanciaId,
  revisaoId,
  onNavigate,
}: Props) {
  const config = KIND_CONFIG[kind];
  const entityId =
    kind === "processo" ? processoId : kind === "instancia" ? instanciaId ?? "" : revisaoId ?? "";
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
  const [lockReady, setLockReady] = useState(false);
  const [lockFailed, setLockFailed] = useState(false);

  const sectionEdit = useCollaborativeSectionEdit({
    entityType: config.entityType,
    entityId,
    getAccessToken,
    enabled: Boolean(entityId),
  });

  useEffect(() => {
    let cancelled = false;
    setLockReady(false);
    setLockFailed(false);
    void (async () => {
      const acquired = await sectionEdit.startEdit(config.sectionKey);
      if (cancelled) return;
      if (acquired === false) {
        setLockFailed(true);
        setLockReady(true);
        return;
      }
      setLockReady(true);
    })();
    return () => {
      cancelled = true;
      sectionEdit.cancelEdit(config.sectionKey);
    };
    // Intencional: adquirir lock uma vez ao montar / trocar entidade.
    // eslint-disable-next-line react-hooks/exhaustive-deps -- sectionEdit.startEdit/cancelEdit estáveis via hook
  }, [config.sectionKey, entityId]);

  function goBack() {
    sectionEdit.cancelEdit(config.sectionKey);
    onNavigate(detailHref);
  }

  const chromeLeading = {
    onBack: goBack,
    backLabel: "Voltar",
    title: config.title,
  };

  const readOnly = lockFailed || !lockReady;
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

        <CollaborativePresenceBanner
          presence={sectionEdit.presence}
          lockError={sectionEdit.lockError}
          realtimeNotice={sectionEdit.realtimeNotice}
          onDismissRealtimeNotice={sectionEdit.clearRealtimeNotice}
          showViewers={false}
        />

        {lockFailed ? (
          <p className="ds-hint tm-diagram-editor-page__lock-hint" role="status">
            Outro usuário está editando este diagrama. Você pode visualizar em somente leitura ou
            voltar ao detalhe.
          </p>
        ) : null}

        {missingIds ? (
          <p className="ds-hint">Identificadores incompletos para abrir o editor.</p>
        ) : (
          <div className="tm-diagram-editor-page__canvas" aria-busy={!lockReady}>
            {kind === "processo" ? (
              <ProcessoDiagramSection
                variant="page"
                chromeLeading={chromeLeading}
                readOnly={readOnly}
                processoId={processoId}
                getAccessToken={getAccessToken}
                onError={setError}
                resyncVersion={sectionEdit.resyncVersion}
              />
            ) : null}
            {kind === "instancia" && instanciaId ? (
              <InstanciaDiagramEscopoSection
                variant="page"
                chromeLeading={chromeLeading}
                readOnly={readOnly}
                processoId={processoId}
                instanciaId={instanciaId}
                getAccessToken={getAccessToken}
                onError={setError}
                resyncVersion={sectionEdit.resyncVersion}
              />
            ) : null}
            {kind === "revisao" && revisaoId ? (
              <RevisaoDiagramSection
                variant="page"
                chromeLeading={chromeLeading}
                readOnly={readOnly}
                revisaoId={revisaoId}
                getAccessToken={getAccessToken}
                onError={setError}
                resyncVersion={sectionEdit.resyncVersion}
              />
            ) : null}
          </div>
        )}
      </div>
    </TransformometroShell>
  );
}
