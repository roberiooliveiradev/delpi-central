import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ClipboardList, Pencil, RefreshCw, Save, Trash2 } from "lucide-react";

import { fetchMeProfile } from "../api/meApi";
import {
  deleteShortageItemNote,
  listShortageItemNotes,
  previewShortage30d,
  upsertShortageItemNote,
} from "../api/reportsApi";
import type { ShortageItemNote } from "../types/reports";
import { formatDateBr, formatDateTimeBr } from "../utils/format";

type PreviewProduct = {
  code: string;
  description: string;
};

type Props = {
  definitionId: string;
  branch: string;
  horizonDays: number;
  disabled?: boolean;
  initialProductCode?: string;
  onStatus?: (message: string) => void;
  onError?: (message: string) => void;
};

export function ShortageItemNotesSection({
  definitionId,
  branch,
  horizonDays,
  disabled = false,
  initialProductCode = "",
  onStatus,
  onError,
}: Props) {
  const onErrorRef = useRef(onError);
  const onStatusRef = useRef(onStatus);
  onErrorRef.current = onError;
  onStatusRef.current = onStatus;

  const [notes, setNotes] = useState<ShortageItemNote[]>([]);
  const [loading, setLoading] = useState(true);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [previewCodes, setPreviewCodes] = useState<PreviewProduct[]>([]);

  const [productCode, setProductCode] = useState(
    () => String(initialProductCode || "").trim(),
  );
  const [noteText, setNoteText] = useState("");
  const [expectedReceiptDate, setExpectedReceiptDate] = useState("");
  const [authorDisplayName, setAuthorDisplayName] = useState("");

  const notesByCode = useMemo(() => {
    const map = new Map<string, ShortageItemNote>();
    for (const note of notes) {
      map.set(note.productCode, note);
    }
    return map;
  }, [notes]);

  const productOptions = useMemo(() => {
    const byCode = new Map<string, PreviewProduct>();
    for (const row of previewCodes) {
      byCode.set(row.code, row);
    }
    for (const note of notes) {
      if (!byCode.has(note.productCode)) {
        byCode.set(note.productCode, {
          code: note.productCode,
          description: "(já com acompanhamento)",
        });
      }
    }
    return Array.from(byCode.values()).sort((a, b) =>
      a.code.localeCompare(b.code, "pt-BR"),
    );
  }, [previewCodes, notes]);

  useEffect(() => {
    const next = String(initialProductCode || "").trim();
    if (next) {
      setProductCode(next);
    }
  }, [initialProductCode]);

  const reloadNotes = useCallback(
    async (signal?: AbortSignal) => {
      setLoading(true);
      try {
        const payload = await listShortageItemNotes(definitionId, signal);
        if (signal?.aborted) return;
        setNotes(payload.items);
      } catch (err) {
        if (signal?.aborted) return;
        onErrorRef.current?.(
          err instanceof Error
            ? err.message
            : "Não foi possível carregar acompanhamentos.",
        );
      } finally {
        if (!signal?.aborted) {
          setLoading(false);
        }
      }
    },
    [definitionId],
  );

  const loadPreviewCodes = useCallback(
    async (
      signal?: AbortSignal,
      options?: { announce?: boolean },
    ) => {
      setPreviewLoading(true);
      try {
        const preview = await previewShortage30d(
          {
            branch,
            horizonDays,
            definitionId,
          },
          signal,
        );
        if (signal?.aborted) return;
        const mapped = preview.items
          .map((row) => ({
            code: String(row.product_code || "").trim(),
            description: String(row.product_description || "").trim(),
          }))
          .filter((row) => row.code);
        setPreviewCodes(mapped);
        if (options?.announce) {
          onStatusRef.current?.(
            mapped.length
              ? `Lista atualizada: ${mapped.length} produto(s) do relatório.`
              : "Preview sem itens de ruptura no horizonte atual.",
          );
        }
      } catch (err) {
        if (signal?.aborted) return;
        onErrorRef.current?.(
          err instanceof Error
            ? err.message
            : "Falha ao carregar produtos do relatório.",
        );
      } finally {
        if (!signal?.aborted) {
          setPreviewLoading(false);
        }
      }
    },
    [branch, definitionId, horizonDays],
  );

  useEffect(() => {
    const controller = new AbortController();
    void reloadNotes(controller.signal);
    return () => controller.abort();
  }, [reloadNotes]);

  useEffect(() => {
    const controller = new AbortController();
    void loadPreviewCodes(controller.signal, { announce: false });
    return () => controller.abort();
  }, [loadPreviewCodes]);

  useEffect(() => {
    const controller = new AbortController();
    void (async () => {
      try {
        const me = await fetchMeProfile(controller.signal);
        if (controller.signal.aborted) return;
        const label = (me.name || me.email || "").trim();
        if (label) {
          setAuthorDisplayName((current) => current || label);
        }
      } catch {
        // nome permanece editável manualmente
      }
    })();
    return () => controller.abort();
  }, []);

  function applyProductSelection(code: string) {
    const next = code.trim();
    setProductCode(next);
    if (!next) {
      setNoteText("");
      setExpectedReceiptDate("");
      return;
    }
    const existing = notesByCode.get(next);
    if (existing) {
      setNoteText(existing.noteText);
      setExpectedReceiptDate(existing.expectedReceiptDate?.slice(0, 10) ?? "");
      setAuthorDisplayName(existing.authorDisplayName || authorDisplayName);
      return;
    }
    setNoteText("");
    setExpectedReceiptDate("");
  }

  function fillForm(note: ShortageItemNote) {
    setProductCode(note.productCode);
    setNoteText(note.noteText);
    setExpectedReceiptDate(note.expectedReceiptDate?.slice(0, 10) ?? "");
    setAuthorDisplayName(note.authorDisplayName || authorDisplayName);
  }

  function clearForm() {
    setProductCode("");
    setNoteText("");
    setExpectedReceiptDate("");
  }

  async function handleSave() {
    const code = productCode.trim();
    const text = noteText.trim();
    const author = authorDisplayName.trim();
    if (!code) {
      onErrorRef.current?.("Selecione um produto na lista.");
      return;
    }
    if (!text) {
      onErrorRef.current?.("Informe o texto do acompanhamento.");
      return;
    }
    if (!author) {
      onErrorRef.current?.("Informe o nome do autor.");
      return;
    }

    setBusy(true);
    try {
      await upsertShortageItemNote(definitionId, code, {
        noteText: text,
        authorDisplayName: author,
        expectedReceiptDate: expectedReceiptDate.trim() || null,
      });
      onStatusRef.current?.(
        "Acompanhamento gravado. Entrará na Observação do próximo e-mail.",
      );
      clearForm();
      await reloadNotes();
    } catch (err) {
      onErrorRef.current?.(
        err instanceof Error ? err.message : "Falha ao gravar acompanhamento.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete(note: ShortageItemNote) {
    const ok = window.confirm(
      `Remover acompanhamento do produto ${note.productCode}?`,
    );
    if (!ok) return;
    setBusy(true);
    try {
      await deleteShortageItemNote(definitionId, note.productCode);
      onStatusRef.current?.("Acompanhamento removido.");
      if (productCode.trim() === note.productCode) {
        clearForm();
      }
      await reloadNotes();
    } catch (err) {
      onErrorRef.current?.(
        err instanceof Error ? err.message : "Falha ao remover acompanhamento.",
      );
    } finally {
      setBusy(false);
    }
  }

  const selectValue = productOptions.some((row) => row.code === productCode)
    ? productCode
    : "";

  return (
    <section className="rp-card">
      <div className="rp-card__header">
        <div>
          <h2 className="rp-card__title">
            <ClipboardList size={18} aria-hidden />
            Acompanhamentos
          </h2>
          <p className="rp-card__hint">
            Os produtos do relatório são carregados automaticamente. Escolha na
            lista, registre o comentário e salve — entra na Observação do e-mail.
          </p>
        </div>
        <button
          type="button"
          className="rp-btn rp-btn--ghost"
          disabled={disabled || busy || previewLoading}
          onClick={() => void loadPreviewCodes(undefined, { announce: true })}
        >
          <RefreshCw
            size={16}
            aria-hidden
            className={previewLoading ? "rp-spin" : undefined}
          />
          Atualizar produtos
        </button>
      </div>

      <div className="rp-form-grid rp-notes-form">
        <label className="rp-field rp-field--full">
          <span>Produto do relatório</span>
          <select
            value={selectValue}
            onChange={(e) => applyProductSelection(e.target.value)}
            disabled={disabled || busy || previewLoading}
          >
            <option value="">
              {previewLoading
                ? "Carregando produtos…"
                : productOptions.length === 0
                  ? "Nenhum produto no preview — atualize a lista"
                  : "Selecione um produto…"}
            </option>
            {productOptions.map((row) => {
              const hasNote = notesByCode.has(row.code);
              const label = row.description
                ? `${row.code} — ${row.description}`
                : row.code;
              return (
                <option key={row.code} value={row.code}>
                  {hasNote ? `${label} · com acompanhamento` : label}
                </option>
              );
            })}
          </select>
          <span className="rp-field__hint">
            {previewLoading
              ? "Buscando rupturas atuais…"
              : `${previewCodes.length} no preview · ${notes.length} com acompanhamento`}
          </span>
        </label>
        <label className="rp-field">
          <span>Previsão de recebimento</span>
          <input
            type="date"
            value={expectedReceiptDate}
            onChange={(e) => setExpectedReceiptDate(e.target.value)}
            disabled={disabled || busy}
          />
        </label>
        <label className="rp-field">
          <span>Autor</span>
          <input
            value={authorDisplayName}
            onChange={(e) => setAuthorDisplayName(e.target.value)}
            maxLength={200}
            disabled={disabled || busy}
          />
        </label>
        <label className="rp-field rp-field--full">
          <span>Texto do acompanhamento</span>
          <textarea
            value={noteText}
            onChange={(e) => setNoteText(e.target.value)}
            rows={3}
            maxLength={2000}
            placeholder="Ex.: Confirmado com o fornecedor — chega na próxima semana."
            disabled={disabled || busy}
          />
        </label>
        <div className="rp-field rp-field--full rp-notes-form__actions">
          <button
            type="button"
            className="rp-btn rp-btn--secondary"
            disabled={disabled || busy}
            onClick={() => void handleSave()}
          >
            <Save size={16} aria-hidden />
            Salvar acompanhamento
          </button>
          {productCode || noteText || expectedReceiptDate ? (
            <button
              type="button"
              className="rp-btn rp-btn--ghost"
              disabled={disabled || busy}
              onClick={clearForm}
            >
              Limpar formulário
            </button>
          ) : null}
        </div>
      </div>

      {loading ? (
        <p className="rp-inline-note">Carregando acompanhamentos…</p>
      ) : notes.length === 0 ? (
        <p className="rp-empty">
          Nenhum acompanhamento registrado nesta definição.
        </p>
      ) : (
        <div className="rp-table-wrap">
          <table className="rp-table">
            <thead>
              <tr>
                <th>Código</th>
                <th>Texto</th>
                <th>Previsão</th>
                <th>Autor</th>
                <th>Atualizado</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {notes.map((note) => (
                <tr key={note.id}>
                  <td>
                    <code className="rp-code">{note.productCode}</code>
                  </td>
                  <td className="rp-notes-table__text">{note.noteText}</td>
                  <td>{formatDateBr(note.expectedReceiptDate)}</td>
                  <td>{note.authorDisplayName || "—"}</td>
                  <td>{formatDateTimeBr(note.updatedAt)}</td>
                  <td>
                    <div className="rp-notes-table__actions">
                      <button
                        type="button"
                        className="rp-btn rp-btn--ghost rp-btn--compact"
                        disabled={disabled || busy}
                        title="Editar"
                        onClick={() => fillForm(note)}
                      >
                        <Pencil size={14} aria-hidden />
                        Editar
                      </button>
                      <button
                        type="button"
                        className="rp-btn rp-btn--ghost rp-btn--compact"
                        disabled={disabled || busy}
                        title="Remover"
                        onClick={() => void handleDelete(note)}
                      >
                        <Trash2 size={14} aria-hidden />
                        Remover
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
