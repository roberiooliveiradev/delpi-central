import type { ReadOnlyReason } from "../state/capabilities";
import { BpmnmStateBanner } from "../ui/kit";

const MESSAGES: Record<Exclude<ReadOnlyReason, null>, string> = {
  ARCHIVED: "Este modelo está arquivado. Desarquive para editar.",
  NO_EDIT_PERMISSION: "Você tem permissão apenas de visualização.",
  UNSUPPORTED_MUST_UNDERSTAND:
    "Este modelo usa uma extensão obrigatória não suportada. Aberto em modo somente leitura para preservar o conteúdo.",
  EDITOR_CAPABILITY_FAILURE:
    "O editor não conseguiu carregar o diagrama com segurança. Modo somente leitura; o arquivo original permanece preservado.",
  REVISION_VIEW: "Esta é uma revisão histórica. Somente leitura.",
};

export function ReadOnlyBanner({ reason }: { reason: ReadOnlyReason }) {
  if (!reason) return null;
  return (
    <BpmnmStateBanner className="bpmnm-banner bpmnm-banner--readonly">
      {MESSAGES[reason]}
    </BpmnmStateBanner>
  );
}
