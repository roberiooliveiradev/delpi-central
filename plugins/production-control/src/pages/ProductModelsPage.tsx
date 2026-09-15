import { Box, Trash2, Upload } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { deleteProduct3DModel, fetchProduct3DModels, upsertProduct3DModel } from "../api/ppcApi";
import { PpcWorkspaceHeader } from "../components/PpcWorkspaceHeader";
import { usePpcConfirm } from "../components/PpcConfirmDialogProvider";
import { copy } from "../content/copy";
import { helpTooltips } from "../content/helpTooltips";
import type { PpcBranch, Product3DModel } from "../types";

function formatBytes(size: number): string {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

function formatWhen(value: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("pt-BR");
}

type Props = {
  branch: PpcBranch;
};

export function ProductModelsPage({ branch }: Props) {
  const confirm = usePpcConfirm();
  const texts = copy.productModels;
  const [items, setItems] = useState<Product3DModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [productCode, setProductCode] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  const reload = useCallback(() => setReloadToken((value) => value + 1), []);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    fetchProduct3DModels({ signal: controller.signal })
      .then((payload) => {
        setItems(payload.items);
        setError(null);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : texts.loadError);
        setItems([]);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [reloadToken, texts.loadError]);

  const visibleItems = useMemo(() => {
    const wanted = query.trim().toUpperCase();
    if (!wanted) return items;
    return items.filter(
      (item) =>
        item.product_code.toUpperCase().includes(wanted) ||
        item.original_filename.toUpperCase().includes(wanted),
    );
  }, [items, query]);

  const existingCodes = useMemo(
    () => new Set(items.map((item) => item.product_code.toUpperCase())),
    [items],
  );

  const handleAttach = async () => {
    const code = productCode.trim();
    if (!code || !file) {
      setError(texts.missingFields);
      return;
    }
    if (!file.name.toLowerCase().endsWith(".glb")) {
      setError(texts.invalidFile);
      return;
    }
    if (existingCodes.has(code.toUpperCase())) {
      const ok = await confirm({
        title: texts.replaceTitle,
        message: texts.replaceMessage(code),
        confirmLabel: texts.replaceConfirm,
        variant: "danger",
      });
      if (!ok) return;
    }
    setSaving(true);
    setError(null);
    try {
      await upsertProduct3DModel({ productCode: code, file });
      setFile(null);
      setProductCode("");
      reload();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : texts.saveError);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (item: Product3DModel) => {
    const ok = await confirm({
      title: texts.deleteTitle,
      message: texts.deleteMessage(item.product_code),
      confirmLabel: texts.deleteConfirm,
      variant: "danger",
    });
    if (!ok) return;
    setSaving(true);
    setError(null);
    try {
      await deleteProduct3DModel({ productCode: item.product_code });
      reload();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : texts.deleteError);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="ppc-page-stack ppc-page-stack--product-models">
      <PpcWorkspaceHeader
        title={texts.title}
        subtitle={texts.subtitle}
        titleHint={helpTooltips.productModels}
        branch={branch}
        subpluginId="product-models"
        onRefresh={reload}
        refreshBusy={loading || saving}
      />

      <form
        className="ppc-product-models__form"
        onSubmit={(event) => {
          event.preventDefault();
          void handleAttach();
        }}
      >
        <label className="ppc-product-models__field">
          <span>{texts.productCode}</span>
          <input
            value={productCode}
            onChange={(event) => setProductCode(event.target.value)}
            placeholder={texts.productCodePlaceholder}
            autoComplete="off"
            spellCheck={false}
          />
        </label>
        <label className="ppc-product-models__field ppc-product-models__field--file">
          <span>{texts.fileLabel}</span>
          <input
            type="file"
            accept=".glb,model/gltf-binary"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          />
        </label>
        <button type="submit" className="ppc-product-models__submit" disabled={saving}>
          <Upload size={16} strokeWidth={1.75} aria-hidden />
          {saving ? texts.saving : texts.attach}
        </button>
      </form>

      <label className="ppc-product-models__search">
        <span className="ppc-sr-only">{texts.searchLabel}</span>
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder={texts.searchPlaceholder}
        />
      </label>

      {error ? (
        <p className="ppc-state ppc-state--error" role="alert">
          {error}
        </p>
      ) : null}

      {loading && items.length === 0 ? (
        <p className="ppc-state" role="status">
          {texts.loading}
        </p>
      ) : null}

      {!loading && visibleItems.length === 0 ? (
        <p className="ppc-state" role="status">
          {texts.empty}
        </p>
      ) : null}

      {visibleItems.length > 0 ? (
        <div className="ppc-product-models__table-wrap">
          <table className="ppc-product-models__table">
            <thead>
              <tr>
                <th>{texts.columns.product}</th>
                <th>{texts.columns.file}</th>
                <th>{texts.columns.size}</th>
                <th>{texts.columns.when}</th>
                <th>{texts.columns.who}</th>
                <th>
                  <span className="ppc-sr-only">{texts.columns.actions}</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {visibleItems.map((item) => (
                <tr key={item.product_code}>
                  <td>
                    <strong>{item.product_code}</strong>
                  </td>
                  <td>{item.original_filename}</td>
                  <td>{formatBytes(item.byte_size)}</td>
                  <td>{formatWhen(item.uploaded_at)}</td>
                  <td>{item.uploaded_by || "—"}</td>
                  <td>
                    <button
                      type="button"
                      className="ppc-product-models__delete"
                      onClick={() => void handleDelete(item)}
                      disabled={saving}
                      aria-label={texts.deleteAria(item.product_code)}
                    >
                      <Trash2 size={16} strokeWidth={1.75} aria-hidden />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      <p className="ppc-product-models__hint">
        <Box size={14} strokeWidth={1.75} aria-hidden />
        {texts.hint}
      </p>
    </div>
  );
}
