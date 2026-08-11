import { useCallback, useEffect, useMemo, useState, type ChangeEvent, type FormEvent } from "react";
import {
  ActionButton,
  ConfirmModalPanel,
  FieldLabel,
  IconButton,
  NativeTextAreaControl,
  NativeTextControl,
  ScreenLoading,
  confirmModalBemClasses,
} from "@delpi/plugin-ui/index";
import { ChevronDown, ChevronUp, Pencil, Plus, QrCode, Trash2 } from "lucide-react";

import {
  createLink,
  deleteHub,
  deleteLink,
  deleteLinkImage,
  fetchHub,
  fetchHubQrPng,
  fetchLinks,
  reorderLinks,
  resolvePublicMenuUrl,
  updateHub,
  updateLink,
  uploadLinkImage,
  type MuralHub,
  type MuralLink,
  type MuralLinkPayload,
} from "../api/muralAcessosApi";
import { HttpRequestError } from "../api/httpClient";
import { LinkIcon } from "../components/LinkIcon";
import { MURAL_HELP } from "../content/helpTooltips";
import {
  MURAL_PREFIX,
  MURAL_ROOT_CLASS,
  MuralDialog,
  MuralEmptyState,
  MuralPageHeader,
} from "../ui/muralUi";
import { muralListPath, navigateMural } from "../utils/route";

const EMPTY_FORM: MuralLinkPayload = {
  title: "",
  url: "https://",
  description: "",
  active: true,
};

type EditorState = {
  mode: "create" | "edit";
  link?: MuralLink;
  form: MuralLinkPayload;
  file: File | null;
};

export function MuralAcessosPage({ hubId }: { hubId: string }) {
  const [hub, setHub] = useState<MuralHub | null>(null);
  const [links, setLinks] = useState<MuralLink[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [canManage, setCanManage] = useState(true);
  const [editor, setEditor] = useState<EditorState | null>(null);
  const [pendingDelete, setPendingDelete] = useState<MuralLink | null>(null);
  const [pendingDeleteHub, setPendingDeleteHub] = useState(false);
  const [hubDraft, setHubDraft] = useState({ title: "", subtitle: "", publicToken: "" });
  const [qrObjectUrl, setQrObjectUrl] = useState<string | null>(null);

  const load = useCallback(async (signal?: AbortSignal) => {
    setLoading(true);
    setError(null);
    try {
      const [hubData, linkData] = await Promise.all([
        fetchHub(hubId, { signal }),
        fetchLinks(hubId, { signal }),
      ]);
      setHub(hubData);
      setHubDraft({
        title: hubData.title,
        subtitle: hubData.subtitle,
        publicToken: hubData.publicToken,
      });
      setLinks(linkData);
      try {
        const qrUrl = await fetchHubQrPng(hubId, { signal });
        setQrObjectUrl(qrUrl);
      } catch {
        setQrObjectUrl(null);
      }
    } catch (cause) {
      if (cause instanceof HttpRequestError && cause.status === 403) {
        setCanManage(false);
        setError("Você não tem permissão para abrir o Mural de Acessos.");
      } else if ((cause as Error).name !== "AbortError") {
        setError(cause instanceof Error ? cause.message : "Não foi possível carregar o mural.");
      }
    } finally {
      setLoading(false);
    }
  }, [hubId]);

  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal);
    return () => controller.abort();
  }, [load]);

  const publicUrl = useMemo(() => (hub ? resolvePublicMenuUrl(hub) : ""), [hub]);

  useEffect(() => {
    return () => {
      if (qrObjectUrl) URL.revokeObjectURL(qrObjectUrl);
    };
  }, [qrObjectUrl]);

  async function handleSaveHub(event: FormEvent) {
    event.preventDefault();
    if (!canManage) return;
    setSaving(true);
    setError(null);
    try {
      const updated = await updateHub(hubId, hubDraft);
      setHub(updated);
      setHubDraft({
        title: updated.title,
        subtitle: updated.subtitle,
        publicToken: updated.publicToken,
      });
      if (qrObjectUrl) URL.revokeObjectURL(qrObjectUrl);
      try {
        setQrObjectUrl(await fetchHubQrPng(hubId));
      } catch {
        setQrObjectUrl(null);
      }
      setNotice(MURAL_HELP.saveSuccess);
    } catch (cause) {
      if (cause instanceof HttpRequestError && cause.status === 403) {
        setCanManage(false);
      }
      setError(cause instanceof Error ? cause.message : "Não foi possível salvar o mural.");
    } finally {
      setSaving(false);
    }
  }

  async function handleCopyUrl() {
    if (!publicUrl) return;
    try {
      await navigator.clipboard.writeText(publicUrl);
      setNotice(MURAL_HELP.copySuccess);
    } catch {
      setError("Não foi possível copiar o link.");
    }
  }

  function openCreate() {
    setEditor({ mode: "create", form: { ...EMPTY_FORM }, file: null });
  }

  function openEdit(link: MuralLink) {
    setEditor({
      mode: "edit",
      link,
      form: {
        title: link.title,
        url: link.url,
        description: link.description,
        active: link.active,
      },
      file: null,
    });
  }

  async function handleSaveEditor(event: FormEvent) {
    event.preventDefault();
    if (!editor) return;
    setSaving(true);
    setError(null);
    try {
      const saved =
        editor.mode === "create"
          ? await createLink(hubId, editor.form)
          : await updateLink(editor.link!.id, editor.form);
      if (editor.file) {
        await uploadLinkImage(saved.id, editor.file);
      }
      setEditor(null);
      setNotice(MURAL_HELP.saveSuccess);
      await load();
    } catch (cause) {
      if (cause instanceof HttpRequestError && cause.status === 403) {
        setCanManage(false);
      }
      setError(cause instanceof Error ? cause.message : "Não foi possível salvar o acesso.");
    } finally {
      setSaving(false);
    }
  }

  async function handleConfirmDelete() {
    if (!pendingDelete) return;
    setSaving(true);
    setError(null);
    try {
      await deleteLink(pendingDelete.id);
      setPendingDelete(null);
      await load();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Não foi possível remover o acesso.");
    } finally {
      setSaving(false);
    }
  }

  async function moveLink(index: number, direction: -1 | 1) {
    const target = index + direction;
    if (target < 0 || target >= links.length) return;
    const next = [...links];
    const [item] = next.splice(index, 1);
    next.splice(target, 0, item);
    setLinks(next);
    try {
      setLinks(await reorderLinks(hubId, next.map((link) => link.id)));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Não foi possível reordenar.");
      await load();
    }
  }

  async function handleRemoveImage() {
    if (!editor?.link?.hasImage) return;
    setSaving(true);
    try {
      const updated = await deleteLinkImage(editor.link.id);
      setEditor({
        ...editor,
        link: updated,
        file: null,
      });
      await load();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Não foi possível remover a imagem.");
    } finally {
      setSaving(false);
    }
  }

  async function handleConfirmDeleteHub() {
    setSaving(true);
    setError(null);
    try {
      await deleteHub(hubId);
      setPendingDeleteHub(false);
      navigateMural(muralListPath());
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Não foi possível remover o mural.");
    } finally {
      setSaving(false);
    }
  }

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] ?? null;
    if (!editor) return;
    setEditor({ ...editor, file });
  }

  return (
    <div className={`${MURAL_ROOT_CLASS} dashboard-page`}>
      <div className="ma-page-stack">
        <MuralPageHeader
          title={hub?.title ?? MURAL_HELP.pageTitle}
          subtitle={MURAL_HELP.qrHelp}
          icon={<QrCode size={28} strokeWidth={1.75} aria-hidden="true" />}
          onRefresh={() => void load()}
          refreshing={loading}
          actions={
            <>
              <ActionButton variant="ghost" onClick={() => navigateMural(muralListPath())}>
                Voltar aos murais
              </ActionButton>
              {canManage ? (
                <ActionButton variant="primary" onClick={openCreate}>
                  <Plus size={16} aria-hidden="true" />
                  Novo acesso
                </ActionButton>
              ) : null}
            </>
          }
        />

        {error ? (
          <p className="ma-banner ma-banner--error" role="alert">
            {error}
          </p>
        ) : null}
        {notice ? (
          <p className="ma-banner ma-banner--success" role="status">
            {notice}
          </p>
        ) : null}

        {loading && !hub ? (
          <ScreenLoading label="Carregando mural…" />
        ) : (
          <>
            <section className="ma-qr-panel" aria-labelledby="ma-qr-title">
              <div className="ma-qr-panel__preview">
                {qrObjectUrl ? (
                  <img className="ma-qr-panel__image" src={qrObjectUrl} alt="QR Code do mural" />
                ) : (
                  <div className="ma-qr-panel__placeholder" aria-hidden="true" />
                )}
              </div>
              <div className="ma-qr-panel__body">
                <h2 id="ma-qr-title">{MURAL_HELP.qrTitle}</h2>
                <p>{MURAL_HELP.qrHelp}</p>
                <p className="ma-qr-panel__url">{publicUrl}</p>
                <div className="ma-qr-panel__actions">
                  <ActionButton variant="ghost" onClick={() => void handleCopyUrl()}>
                    Copiar link
                  </ActionButton>
                  {publicUrl ? (
                    <a className="ma-qr-panel__open" href={publicUrl} target="_blank" rel="noreferrer">
                      Abrir menu
                    </a>
                  ) : null}
                  {qrObjectUrl ? (
                    <a
                      className="ma-qr-panel__open"
                      href={qrObjectUrl}
                      download={`mural-${hub?.publicToken ?? "acessos"}-qr.png`}
                    >
                      Baixar QR
                    </a>
                  ) : null}
                </div>
                {canManage ? (
                  <form className="ma-hub-form" onSubmit={(event) => void handleSaveHub(event)}>
                    <FieldLabel htmlFor="ma-hub-title" hint={MURAL_HELP.qrHelp} label="Título do menu" />
                    <NativeTextControl
                      id="ma-hub-title"
                      value={hubDraft.title}
                      onChange={(value) => setHubDraft((current) => ({ ...current, title: value }))}
                      maxLength={80}
                      required
                    />
                    <FieldLabel htmlFor="ma-hub-subtitle" label="Subtítulo" />
                    <NativeTextControl
                      id="ma-hub-subtitle"
                      value={hubDraft.subtitle}
                      onChange={(value) =>
                        setHubDraft((current) => ({ ...current, subtitle: value }))
                      }
                      maxLength={160}
                    />
                    <FieldLabel
                      htmlFor="ma-hub-token"
                      hint={MURAL_HELP.tokenHelp}
                      label="Identificador público"
                    />
                    <NativeTextControl
                      id="ma-hub-token"
                      value={hubDraft.publicToken}
                      onChange={(value) =>
                        setHubDraft((current) => ({ ...current, publicToken: value }))
                      }
                      maxLength={40}
                      required
                    />
                    <div className="ma-hub-form__actions">
                      <ActionButton type="submit" variant="ghost" disabled={saving}>
                        Salvar mural
                      </ActionButton>
                      <ActionButton
                        type="button"
                        variant="ghost"
                        disabled={saving}
                        onClick={() => setPendingDeleteHub(true)}
                      >
                        Excluir mural
                      </ActionButton>
                    </div>
                  </form>
                ) : null}
              </div>
            </section>

            {links.length === 0 ? (
              <MuralEmptyState
                title={MURAL_HELP.emptyTitle}
                message={MURAL_HELP.emptyMessage}
              />
            ) : (
              <ul className="ma-link-list">
                {links.map((link, index) => (
                  <li key={link.id} className={link.active ? "ma-link-row" : "ma-link-row ma-link-row--inactive"}>
                    <div className="ma-icon" aria-hidden="true">
                      <LinkIcon title={link.title} imageUrl={link.imageUrl} />
                    </div>
                    <div className="ma-link-row__body">
                      <strong>{link.title}</strong>
                      <span>{link.url}</span>
                      {!link.active ? <em>Oculto no mural</em> : null}
                    </div>
                    {canManage ? (
                      <div className="ma-link-row__actions">
                        <IconButton
                          aria-label={`Subir ${link.title}`}
                          disabled={index === 0}
                          onClick={() => void moveLink(index, -1)}
                        >
                          <ChevronUp size={16} />
                        </IconButton>
                        <IconButton
                          aria-label={`Descer ${link.title}`}
                          disabled={index === links.length - 1}
                          onClick={() => void moveLink(index, 1)}
                        >
                          <ChevronDown size={16} />
                        </IconButton>
                        <IconButton aria-label={`Editar ${link.title}`} onClick={() => openEdit(link)}>
                          <Pencil size={16} />
                        </IconButton>
                        <IconButton
                          aria-label={`Remover ${link.title}`}
                          tone="danger"
                          onClick={() => setPendingDelete(link)}
                        >
                          <Trash2 size={16} />
                        </IconButton>
                      </div>
                    ) : null}
                  </li>
                ))}
              </ul>
            )}
          </>
        )}
      </div>

      <MuralDialog
        open={Boolean(editor)}
        title={editor?.mode === "edit" ? "Editar acesso" : "Novo acesso"}
        onClose={() => setEditor(null)}
      >
        {editor ? (
          <form className="ma-editor" onSubmit={(event) => void handleSaveEditor(event)}>
            <FieldLabel htmlFor="ma-link-title" hint={MURAL_HELP.titleHelp} label="Título" />
            <NativeTextControl
              id="ma-link-title"
              value={editor.form.title}
              onChange={(value) =>
                setEditor({ ...editor, form: { ...editor.form, title: value } })
              }
              maxLength={80}
              required
            />
            <FieldLabel htmlFor="ma-link-url" hint={MURAL_HELP.urlHelp} label="Link" />
            <NativeTextControl
              id="ma-link-url"
              type="url"
              value={editor.form.url}
              onChange={(value) => setEditor({ ...editor, form: { ...editor.form, url: value } })}
              required
            />
            <FieldLabel htmlFor="ma-link-description" label="Descrição" />
            <NativeTextAreaControl
              id="ma-link-description"
              value={editor.form.description}
              onChange={(value) =>
                setEditor({ ...editor, form: { ...editor.form, description: value } })
              }
              maxLength={240}
            />
            <label className="ma-editor__check">
              <input
                type="checkbox"
                checked={editor.form.active}
                onChange={(event) =>
                  setEditor({
                    ...editor,
                    form: { ...editor.form, active: event.target.checked },
                  })
                }
              />
              Visível no mural
            </label>
            <FieldLabel htmlFor="ma-link-image" hint={MURAL_HELP.imageHelp} label="Imagem do ícone" />
            <input
              id="ma-link-image"
              type="file"
              accept="image/jpeg,image/png,image/webp,image/gif"
              onChange={handleFileChange}
            />
            {editor.link?.hasImage ? (
              <ActionButton type="button" variant="ghost" onClick={() => void handleRemoveImage()}>
                Remover imagem atual
              </ActionButton>
            ) : null}
            <div className="ma-editor__actions">
              <ActionButton type="button" variant="ghost" onClick={() => setEditor(null)}>
                Cancelar
              </ActionButton>
              <ActionButton type="submit" variant="primary" disabled={saving}>
                Salvar
              </ActionButton>
            </div>
          </form>
        ) : null}
      </MuralDialog>

      <MuralDialog
        open={pendingDeleteHub}
        title="Excluir mural"
        onClose={() => setPendingDeleteHub(false)}
      >
        <ConfirmModalPanel
          message={`Excluir “${hub?.title ?? ""}” e todos os acessos deste mural? O QR deste mural deixa de funcionar.`}
          confirmLabel="Excluir mural"
          cancelLabel="Cancelar"
          confirmBusy={saving}
          variant="danger"
          onConfirm={() => void handleConfirmDeleteHub()}
          onCancel={() => setPendingDeleteHub(false)}
          classNames={confirmModalBemClasses(MURAL_PREFIX)}
        />
      </MuralDialog>

      <MuralDialog
        open={Boolean(pendingDelete)}
        title="Remover acesso"
        onClose={() => setPendingDelete(null)}
      >
        <ConfirmModalPanel
          message={`Remover “${pendingDelete?.title ?? ""}” do mural?`}
          confirmLabel="Remover"
          cancelLabel="Cancelar"
          confirmBusy={saving}
          variant="danger"
          onConfirm={() => void handleConfirmDelete()}
          onCancel={() => setPendingDelete(null)}
          classNames={confirmModalBemClasses(MURAL_PREFIX)}
        />
      </MuralDialog>
    </div>
  );
}
