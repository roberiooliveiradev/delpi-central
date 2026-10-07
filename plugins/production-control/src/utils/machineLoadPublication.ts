import { copy } from "../content/copy";
import type { MachineLoadPublicationInfo } from "../types";
import { formatRefreshedAt } from "./formatRefreshedAt";

export type MachineLoadPublicationView = {
  /** Rótulo do estado — texto explícito, nunca só cor/ícone. */
  label: string;
  /** Explicação curta do que o estado significa para o operador. */
  hint: string;
  /** Há algo novo para enviar aos cockpits (draft/unpublished). */
  canPublish: boolean;
};

/**
 * Apresentação do estado semântico derivado pelo backend (E5).
 * A UI nunca compara gerações — só traduz o `state` recebido.
 */
export function describeMachineLoadPublication(
  publication: MachineLoadPublicationInfo | null | undefined,
): MachineLoadPublicationView {
  const state = publication?.state ?? "unpublished";
  const publish = copy.machineLoad.publish;

  if (state === "live") {
    return {
      label: publish.liveLabel,
      hint: publish.liveHint(
        formatRefreshedAt(publication?.published_at),
        publication?.published_by ?? null,
      ),
      canPublish: false,
    };
  }

  if (state === "unpublished") {
    return {
      label: publish.draftLabel,
      hint: publish.unpublishedHint,
      canPublish: true,
    };
  }

  const lastSent = publication?.published_at
    ? publish.draftLastSent(formatRefreshedAt(publication.published_at))
    : null;
  return {
    label: publish.draftLabel,
    hint: lastSent ? `${publish.draftHint} ${lastSent}` : publish.draftHint,
    canPublish: true,
  };
}
