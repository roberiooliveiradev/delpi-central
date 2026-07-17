import type {
  PlaylistHistoryEntry,
  PlaylistHistorySlideChange,
} from "../api/tvDashboardApi";

const PLAYLIST_FIELD_LABELS: Record<string, string> = {
  name: "nome",
  description: "descrição",
  viewportProfile: "formato da tela",
  transitionStyle: "transição",
  defaultDurationSec: "duração padrão",
  globalRefreshSec: "atualização",
  isActive: "status",
  dataDefaults: "dados padrão",
  masterConfig: "aparência",
};

const SLIDE_FIELD_LABELS: Record<string, string> = {
  title: "título",
  durationSec: "duração",
  slideType: "tipo",
  nativeScreenKey: "modelo",
  nativeConfig: "conteúdo",
  externalUrl: "URL",
  externalSandbox: "permissões do conteúdo externo",
  isActive: "status",
  transitionStyle: "transição",
};

function compact(value?: string | null): string {
  return value?.trim() ?? "";
}

function slideCount(value?: PlaylistHistorySlideChange[] | boolean): number {
  if (Array.isArray(value)) return value.length;
  return value ? 1 : 0;
}

function totalOrFallback(total: number | undefined, fallback: number): number {
  return Number.isFinite(total) ? Math.max(0, total ?? 0) : fallback;
}

function quantityLabel(count: number, singular: string, plural: string): string | null {
  return count > 0 ? `${count} ${count === 1 ? singular : plural}` : null;
}

function slideLabel(change: PlaylistHistorySlideChange): string {
  if (typeof change === "string") return change;
  return compact(change.title) || compact(change.id) || "Tela sem título";
}

function summarizeSlideNames(changes?: PlaylistHistorySlideChange[]): string | null {
  if (!changes?.length) return null;
  const labels = changes.slice(0, 3).map(slideLabel);
  const remaining = changes.length - labels.length;
  return `${labels.join(", ")}${remaining > 0 ? ` e mais ${remaining}` : ""}`;
}

function summarizeUpdatedSlides(changes?: PlaylistHistorySlideChange[]): string | null {
  if (!changes?.length) return null;
  const labels = changes.slice(0, 3).map((change) => {
    if (typeof change === "string") return change;
    const fields = (change.fields ?? []).map((field) => SLIDE_FIELD_LABELS[field] ?? field);
    const suffix = fields.length
      ? ` (${new Intl.ListFormat("pt-BR", { style: "long", type: "conjunction" }).format(fields)})`
      : "";
    return `${slideLabel(change)}${suffix}`;
  });
  const remaining = changes.length - labels.length;
  return `${labels.join(", ")}${remaining > 0 ? ` e mais ${remaining}` : ""}`;
}

export function playlistHistoryAuthor(item: PlaylistHistoryEntry): {
  name: string;
  email: string | null;
} {
  const email = compact(item.authorEmail);
  const name = compact(item.authorName) || compact(item.authorId) || email || "Sistema";
  return {
    name,
    email: email && email.toLocaleLowerCase("pt-BR") !== name.toLocaleLowerCase("pt-BR")
      ? email
      : null,
  };
}

export function playlistHistoryPreview(item: PlaylistHistoryEntry): string {
  const preview = item.preview;
  if (!preview) return "Selecione a revisão para consultar o snapshot.";
  const slides =
    preview.slideTitles?.filter(Boolean).slice(0, 3).join(", ") ||
    `${preview.slideCount ?? 0} tela(s)`;
  return [preview.playlistName, slides].filter(Boolean).join(" · ");
}

export function playlistHistoryFallback(item: PlaylistHistoryEntry): string {
  const reason = compact(item.reason);
  return reason ? reason.replaceAll("_", " ") : "Alteração da programação";
}

export function summarizePlaylistHistoryChange(item: PlaylistHistoryEntry): string {
  const change = item.change;
  if (!change?.available) {
    return `${playlistHistoryFallback(item)} · ${playlistHistoryPreview(item)}`;
  }

  const fields = change.playlistFields ?? [];
  const totals = change.totals ?? {};
  const fieldCount = totalOrFallback(
    totals.playlistFields ?? totals.playlistFieldsChanged,
    fields.length,
  );
  const added = totalOrFallback(
    totals.added ?? totals.slidesAdded,
    slideCount(change.slides?.added),
  );
  const removed = totalOrFallback(
    totals.removed ?? totals.slidesRemoved,
    slideCount(change.slides?.removed),
  );
  const updated = totalOrFallback(
    totals.updated ?? totals.slidesUpdated,
    slideCount(change.slides?.updated),
  );
  const reordered = totalOrFallback(
    totals.reordered ?? totals.slidesReordered,
    slideCount(change.slides?.reordered),
  );

  const fieldNames = fields
    .map((field) => PLAYLIST_FIELD_LABELS[field] ?? field)
    .filter(Boolean);
  const addedNames = summarizeSlideNames(change.slides?.added);
  const removedNames = summarizeSlideNames(change.slides?.removed);
  const updatedSlides = summarizeUpdatedSlides(change.slides?.updated);
  const fieldSummary = quantityLabel(fieldCount, "campo alterado", "campos alterados");
  const addedSummary = quantityLabel(added, "tela adicionada", "telas adicionadas");
  const removedSummary = quantityLabel(removed, "tela removida", "telas removidas");
  const updatedSummary = quantityLabel(updated, "tela editada", "telas editadas");
  const parts = [
    fieldSummary && fieldNames.length
      ? `${fieldSummary}: ${new Intl.ListFormat("pt-BR", {
          style: "long",
          type: "conjunction",
        }).format(fieldNames)}`
      : fieldSummary,
    addedSummary && addedNames ? `${addedSummary}: ${addedNames}` : addedSummary,
    removedSummary && removedNames ? `${removedSummary}: ${removedNames}` : removedSummary,
    updatedSummary && updatedSlides ? `${updatedSummary}: ${updatedSlides}` : updatedSummary,
    reordered > 0 ? "ordem das telas alterada" : null,
  ].filter((part): part is string => Boolean(part));

  const comparison =
    change.comparedToRevision != null
      ? `Alteração resultante na revisão ${change.comparedToRevision}.`
      : null;
  return [parts.join("; ") || "Snapshot registrado sem diferenças de conteúdo.", comparison]
    .filter(Boolean)
    .join(" ");
}
