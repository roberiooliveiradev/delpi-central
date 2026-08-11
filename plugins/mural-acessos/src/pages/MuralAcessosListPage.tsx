import { useCallback, useEffect, useState, type FormEvent } from "react";
import {
  ActionButton,
  FieldLabel,
  NativeTextControl,
  ScreenLoading,
} from "@delpi/plugin-ui/index";
import { Plus, QrCode } from "lucide-react";

import {
  createHub,
  fetchHubs,
  suggestPublicToken,
  type MuralHub,
  type MuralHubPayload,
} from "../api/muralAcessosApi";
import { HttpRequestError } from "../api/httpClient";
import { MURAL_HELP } from "../content/helpTooltips";
import { MuralDialog, MuralEmptyState, MuralPageHeader, MURAL_ROOT_CLASS } from "../ui/muralUi";
import { muralDetailPath, navigateMural } from "../utils/route";

const EMPTY_FORM: MuralHubPayload = {
  title: "",
  subtitle: "",
  publicToken: "",
};

export function MuralAcessosListPage() {
  const [hubs, setHubs] = useState<MuralHub[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [canManage, setCanManage] = useState(true);
  const [editor, setEditor] = useState<MuralHubPayload | null>(null);
  const [tokenTouched, setTokenTouched] = useState(false);

  const load = useCallback(async (signal?: AbortSignal) => {
    setLoading(true);
    setError(null);
    try {
      setHubs(await fetchHubs({ signal }));
    } catch (cause) {
      if (cause instanceof HttpRequestError && cause.status === 403) {
        setCanManage(false);
        setError("Você não tem permissão para abrir o Mural de Acessos.");
      } else if ((cause as Error).name !== "AbortError") {
        setError(cause instanceof Error ? cause.message : "Não foi possível carregar os murais.");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal);
    return () => controller.abort();
  }, [load]);

  function openCreate() {
    setTokenTouched(false);
    setEditor({ ...EMPTY_FORM });
  }

  async function handleCreate(event: FormEvent) {
    event.preventDefault();
    if (!editor) return;
    setSaving(true);
    setError(null);
    try {
      const created = await createHub({
        ...editor,
        publicToken: editor.publicToken || suggestPublicToken(editor.title),
      });
      setEditor(null);
      setNotice(MURAL_HELP.createSuccess);
      navigateMural(muralDetailPath(created.id));
    } catch (cause) {
      if (cause instanceof HttpRequestError && cause.status === 403) {
        setCanManage(false);
      }
      setError(cause instanceof Error ? cause.message : "Não foi possível cadastrar o mural.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className={`${MURAL_ROOT_CLASS} dashboard-page`}>
      <div className="ma-page-stack">
        <MuralPageHeader
          title={MURAL_HELP.pageTitle}
          subtitle={MURAL_HELP.pageSubtitle}
          icon={<QrCode size={28} strokeWidth={1.75} aria-hidden="true" />}
          onRefresh={() => void load()}
          refreshing={loading}
          actions={
            canManage ? (
              <ActionButton variant="primary" onClick={openCreate}>
                <Plus size={16} aria-hidden="true" />
                Novo mural
              </ActionButton>
            ) : null
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

        {loading && hubs.length === 0 ? (
          <ScreenLoading label="Carregando murais…" />
        ) : hubs.length === 0 ? (
          <MuralEmptyState title={MURAL_HELP.listEmptyTitle} message={MURAL_HELP.listEmptyMessage} />
        ) : (
          <ul className="ma-hub-grid">
            {hubs.map((hub) => (
              <li key={hub.id}>
                <button
                  type="button"
                  className="ma-hub-card"
                  onClick={() => navigateMural(muralDetailPath(hub.id))}
                >
                  <strong>{hub.title}</strong>
                  {hub.subtitle ? <span>{hub.subtitle}</span> : null}
                  <em>
                    /{hub.publicToken} · {hub.linkCount ?? 0}{" "}
                    {(hub.linkCount ?? 0) === 1 ? "acesso" : "acessos"}
                  </em>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <MuralDialog open={Boolean(editor)} title="Novo mural" onClose={() => setEditor(null)}>
        {editor ? (
          <form className="ma-editor" onSubmit={(event) => void handleCreate(event)}>
            <FieldLabel htmlFor="ma-new-hub-title" label="Título do mural" />
            <NativeTextControl
              id="ma-new-hub-title"
              value={editor.title}
              onChange={(value) =>
                setEditor({
                  ...editor,
                  title: value,
                  publicToken: tokenTouched ? editor.publicToken : suggestPublicToken(value),
                })
              }
              maxLength={80}
              required
            />
            <FieldLabel htmlFor="ma-new-hub-subtitle" label="Subtítulo" />
            <NativeTextControl
              id="ma-new-hub-subtitle"
              value={editor.subtitle}
              onChange={(value) => setEditor({ ...editor, subtitle: value })}
              maxLength={160}
            />
            <FieldLabel htmlFor="ma-new-hub-token" hint={MURAL_HELP.tokenHelp} label="Identificador público" />
            <NativeTextControl
              id="ma-new-hub-token"
              value={editor.publicToken}
              onChange={(value) => {
                setTokenTouched(true);
                setEditor({ ...editor, publicToken: value });
              }}
              maxLength={40}
              required
            />
            <div className="ma-editor__actions">
              <ActionButton type="button" variant="ghost" onClick={() => setEditor(null)}>
                Cancelar
              </ActionButton>
              <ActionButton type="submit" variant="primary" disabled={saving}>
                Criar mural
              </ActionButton>
            </div>
          </form>
        ) : null}
      </MuralDialog>
    </div>
  );
}
