/** U2 — detalhe do produto acompanhado: hero compacto (código,
 * descrição, versão acompanhada, origem, bandeiras) + duas abas
 * «Ficha técnica | Versões». A ficha consolida o snapshot da revisão
 * selecionada (`?rev=N`) — sempre somente leitura, sem confundir
 * versão do produto com `caseVersion` de solicitação. */

import { useCallback, useEffect, useMemo, useState } from "react";
import { ExternalLink, Flag, RefreshCw } from "lucide-react";

import { HomeApiError } from "../../../api/httpClient";
import { navigateEngineeringView } from "../../../app/engineeringRoutes";
import {
  PrcTechnicalSheetView,
  type SupplierRow,
} from "@delpi/plugin-ui/index";
import {
  EngineeringActionButton,
  EngineeringEmptyState,
  EngineeringLoadingActivityCard,
  EngineeringPageHero,
  EngineeringPagePath,
  EngineeringScopeChipBar,
  EngineeringStateBanner,
  EngineeringTabs,
} from "../../../ui/engineeringUi";
import {
  fetchPrcRecord,
  fetchPrcReferenceData,
  fetchPrcRevision,
  type PrcFieldSpec,
  type PrcProductDetail,
  type PrcRevisionDetail,
} from "../api/productRegistrationApi";
import {
  navigatePrc,
  navigatePrcHref,
  parsePrcProductRevision,
  parsePrcProductTab,
  prcProductHref,
  PRC_PATHS,
  useLocationSearch,
  type PrcProductTabKey,
} from "../prcNavigate";
import {
  PRC_COPY,
  PRC_FIELD_LABELS,
  PRC_PRODUCTS_COPY,
  PRC_SUPPLIER_LABELS,
  prcShortId,
} from "../prcCopy";
import {
  openRecordFlagForField,
  openRecordFlagForSupplier,
  resolvedRecordFlagsForField,
  resolvedRecordFlagsForSupplier,
  snapshotFieldsToSheetData,
  snapshotSupplierRows,
} from "../prcSnapshot";
import {
  PrcProductFlagsProvider,
  PrcRecordFlagTrigger,
} from "../components/PrcProductFlags";
import { usePrcProductFlags } from "../components/prcProductFlagsContext";
import { PrcProductVersionsTab } from "../components/PrcProductVersionsTab";

const PRODUCT_TABS: { key: PrcProductTabKey; label: string }[] = [
  { key: "sheet", label: PRC_PRODUCTS_COPY.tabSheet },
  { key: "versions", label: PRC_PRODUCTS_COPY.tabVersions },
];

function formatWhen(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString("pt-BR");
  } catch {
    return iso;
  }
}

export function PrcProductDetailPage({
  recordId,
  basePath,
}: {
  recordId: string;
  basePath: string;
}) {
  const search = useLocationSearch();
  const tab = parsePrcProductTab(search);
  const revParam = parsePrcProductRevision(search);

  const [detail, setDetail] = useState<PrcProductDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<{
    status: number | null;
    message: string;
  } | null>(null);
  const [specs, setSpecs] = useState<PrcFieldSpec[]>([]);

  const load = useCallback(
    async (signal?: AbortSignal) => {
      setLoading(true);
      setError(null);
      try {
        const env = await fetchPrcRecord(recordId, signal);
        setDetail(env.data);
      } catch (e) {
        const err = e as HomeApiError;
        setError({
          status: err.status ?? null,
          message: err.message || "Falha ao carregar o produto.",
        });
        setDetail(null);
      } finally {
        setLoading(false);
      }
    },
    [recordId],
  );

  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal);
    return () => controller.abort();
  }, [load]);

  useEffect(() => {
    const controller = new AbortController();
    fetchPrcReferenceData(controller.signal)
      .then((env) => setSpecs(env.data.fields || []))
      .catch(() => setSpecs([]));
    return () => controller.abort();
  }, []);

  const specNotes = useMemo(
    () =>
      Object.fromEntries(
        specs.map((s) => [s.path, s.note] as const),
      ),
    [specs],
  );

  const selectTab = useCallback(
    (key: PrcProductTabKey) => {
      navigatePrcHref(
        prcProductHref(basePath, recordId, {
          tab: key,
          rev: key === "versions" ? null : revParam,
        }),
        { replace: false },
      );
    },
    [basePath, recordId, revParam],
  );

  const forbidden = error?.status === 403;
  const notFound = error?.status === 404;

  const selectedRev =
    revParam && detail && revParam <= detail.currentRevisionNumber
      ? revParam
      : detail?.currentRevisionNumber ?? null;

  const refresh = useCallback(() => {
    const controller = new AbortController();
    void load(controller.signal);
  }, [load]);

  return (
    <main className="engineering-prc">
      <EngineeringPagePath
        back={{
          label: PRC_COPY.breadcrumbHome,
          href: basePath,
          onNavigate: (event) => {
            event.preventDefault();
            navigateEngineeringView("home", { basePath });
          },
        }}
        items={[
          {
            label: PRC_PRODUCTS_COPY.detailBreadcrumb,
            href: `${basePath}/${PRC_PATHS.queue}?area=products`,
            onNavigate: (event) => {
              event.preventDefault();
              navigatePrcHref(
                `${basePath}/${PRC_PATHS.queue}?area=products`,
                { replace: false },
              );
            },
          },
        ]}
        current={detail?.officialCode || "Produto"}
      />

      {forbidden ? (
        <>
          <EngineeringStateBanner variant="error">
            {PRC_COPY.forbidden}
          </EngineeringStateBanner>
          <EngineeringActionButton
            variant="primary"
            onClick={() => navigateEngineeringView("home", { basePath })}
          >
            Voltar ao início
          </EngineeringActionButton>
        </>
      ) : null}

      {!forbidden && notFound ? (
        <EngineeringEmptyState message="Produto acompanhado não encontrado." />
      ) : null}

      {!forbidden && !notFound && error ? (
        <>
          <EngineeringStateBanner variant="error">
            {`Produto acompanhado indisponível — ${error.message}`}
          </EngineeringStateBanner>
          <EngineeringActionButton variant="primary" onClick={refresh}>
            Tentar novamente
          </EngineeringActionButton>
        </>
      ) : null}

      {!forbidden && !notFound && !error && loading && !detail ? (
        <EngineeringLoadingActivityCard
          title="Carregando produto acompanhado"
          description="Consultando a ficha técnica consolidada."
        />
      ) : null}

      {!forbidden && !notFound && !error && detail ? (
        <>
          <EngineeringPageHero
            eyebrow="Produto acompanhado"
            title={detail.description || detail.officialCode}
            description={`Código oficial ${detail.officialCode} — ficha consolidada das versões confirmadas.`}
            actions={
              <>
                <span
                  className="engineering-prc__count-pill"
                  aria-label={`${PRC_PRODUCTS_COPY.heroVersion} V${detail.currentRevisionNumber}`}
                >
                  V<strong className="engineering-prc__count-pill-value">
                    {detail.currentRevisionNumber}
                  </strong>
                </span>
                {detail.openFlagCount > 0 ? (
                  <span
                    className="engineering-prc__count-pill"
                    aria-label={`${detail.openFlagCount} bandeira(s) aberta(s)`}
                  >
                    <Flag size={13} aria-hidden />{" "}
                    <strong className="engineering-prc__count-pill-value">
                      {detail.openFlagCount}
                    </strong>
                  </span>
                ) : null}
                <EngineeringActionButton
                  variant="ghost"
                  softDisabled={loading}
                  onClick={refresh}
                >
                  <RefreshCw size={16} aria-hidden /> {PRC_COPY.refresh}
                </EngineeringActionButton>
              </>
            }
          >
            <dl className="engineering-prc__product-meta">
              <div>
                <dt>{PRC_PRODUCTS_COPY.heroLastEvolution}</dt>
                <dd>{formatWhen(detail.lastEvolutionAt)}</dd>
              </div>
              <div>
                <dt>{PRC_PRODUCTS_COPY.heroOrigin}</dt>
                <dd>
                  {detail.originRequestId ? (
                    <EngineeringActionButton
                      variant="ghost"
                      title={PRC_PRODUCTS_COPY.openOriginRequest}
                      onClick={() =>
                        navigatePrc(
                          PRC_PATHS.detail(
                            detail.originRequestId as string,
                          ),
                          basePath,
                        )
                      }
                    >
                      <ExternalLink size={13} aria-hidden />{" "}
                      {prcShortId(detail.originRequestId)}
                    </EngineeringActionButton>
                  ) : (
                    PRC_PRODUCTS_COPY.heroOriginNone
                  )}
                </dd>
              </div>
            </dl>
          </EngineeringPageHero>

          <EngineeringTabs
            mode="tabs"
            aria-label="Seções do produto acompanhado"
            activeId={tab}
            items={PRODUCT_TABS.map((t) => ({
              id: t.key,
              label: t.label,
              controlId: `prc-product-panel-${t.key}`,
              tabId: `prc-product-tab-${t.key}`,
              onSelect: () => selectTab(t.key),
            }))}
          />

          <div
            role="tabpanel"
            id={`prc-product-panel-${tab}`}
            aria-labelledby={`prc-product-tab-${tab}`}
            className="engineering-prc__tabpanel"
          >
            {tab === "sheet" && selectedRev ? (
              <ProductSheetTab
                recordId={recordId}
                basePath={basePath}
                detail={detail}
                selectedRev={selectedRev}
                specNotes={specNotes}
                onReload={refresh}
              />
            ) : null}
            {tab === "versions" ? (
              <PrcProductVersionsTab
                recordId={recordId}
                basePath={basePath}
                currentRevisionNumber={detail.currentRevisionNumber}
              />
            ) : null}
          </div>
        </>
      ) : null}
    </main>
  );
}

/* --- Aba Ficha técnica ---------------------------------------------------- */

function ProductSheetTab({
  recordId,
  basePath,
  detail,
  selectedRev,
  specNotes,
  onReload,
}: {
  recordId: string;
  basePath: string;
  detail: PrcProductDetail;
  selectedRev: number;
  specNotes: Record<string, string | null | undefined>;
  onReload: () => void;
}) {
  const isCurrent = selectedRev === detail.currentRevisionNumber;
  const [revision, setRevision] = useState<PrcRevisionDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  /* Revisão corrente já veio no detalhe do registro — só busca extra
   * quando a seleção aponta para versão histórica. */
  useEffect(() => {
    if (isCurrent) {
      setRevision(null);
      return undefined;
    }
    const controller = new AbortController();
    setLoading(true);
    setError("");
    fetchPrcRevision(recordId, selectedRev, controller.signal)
      .then((env) => setRevision(env.data))
      .catch((e) => {
        setRevision(null);
        setError(
          e instanceof HomeApiError
            ? e.message
            : "Não foi possível carregar a versão selecionada.",
        );
      })
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, [recordId, selectedRev, isCurrent]);

  const snapshot = isCurrent
    ? detail.snapshot
    : revision?.snapshot;
  const flags = isCurrent ? detail.flags : revision?.flags || [];
  const allowedActions = isCurrent
    ? detail.allowedFlagActions
    : revision?.allowedFlagActions || [];

  const sheetData = useMemo(
    () => ({
      ...snapshotFieldsToSheetData(snapshot, detail.officialCode),
      suppliers: snapshotSupplierRows(snapshot),
    }),
    [snapshot, detail.officialCode],
  );

  const selectRevision = useCallback(
    (n: number) => {
      navigatePrcHref(
        prcProductHref(basePath, recordId, {
          tab: "sheet",
          rev: n === detail.currentRevisionNumber ? null : n,
        }),
        { replace: false },
      );
    },
    [basePath, recordId, detail.currentRevisionNumber],
  );

  const versionChips = useMemo(
    () =>
      Array.from(
        { length: detail.currentRevisionNumber },
        (_, i) => i + 1,
      ).map((n) => ({
        id: `v${n}`,
        label:
          n === detail.currentRevisionNumber
            ? `V${n} · Atual`
            : `V${n}`,
        active: selectedRev === n,
        onSelect: () => selectRevision(n),
      })),
    [detail.currentRevisionNumber, selectedRev, selectRevision],
  );

  if (!isCurrent && loading) {
    return (
      <EngineeringLoadingActivityCard
        title={`Carregando versão V${selectedRev}`}
        description="Consultando o snapshot consolidado."
      />
    );
  }
  if (!isCurrent && error) {
    return (
      <EngineeringStateBanner variant="error">{error}</EngineeringStateBanner>
    );
  }
  if (!isCurrent && !revision) {
    return (
      <EngineeringEmptyState message="Versão selecionada indisponível." />
    );
  }

  return (
    <PrcProductFlagsProvider
      recordId={recordId}
      flags={flags}
      allowedActions={allowedActions}
      isCurrentRevision={isCurrent}
      onChanged={onReload}
    >
      <div className="engineering-prc__product-sheet-head">
        <EngineeringScopeChipBar
          aria-label={PRC_PRODUCTS_COPY.versionSelectorLabel}
          label={PRC_PRODUCTS_COPY.versionSelectorLabel}
          chips={versionChips}
        />
      </div>
      {!isCurrent ? (
        <EngineeringStateBanner variant="default">
          {PRC_PRODUCTS_COPY.flagHistoryOnly}{" "}
          <EngineeringActionButton
            variant="ghost"
            onClick={() =>
              selectRevision(detail.currentRevisionNumber)
            }
          >
            {PRC_PRODUCTS_COPY.flagGoToCurrent}
          </EngineeringActionButton>
        </EngineeringStateBanner>
      ) : null}
      <ProductSheetContent
        sheetData={sheetData}
        specNotes={specNotes}
      />
    </PrcProductFlagsProvider>
  );
}

/** Ficha consolidada somente leitura + adornos de bandeira nos
 * alvos técnicos (campo e vínculo de fornecedor). */
function ProductSheetContent({
  sheetData,
  specNotes,
}: {
  sheetData: Record<string, unknown>;
  specNotes: Record<string, string | null | undefined>;
}) {
  const { flags, isCurrentRevision, openTarget } = usePrcProductFlags();

  const fieldAdornment = useCallback(
    (path: string, displayValue: string) => {
      const openFlag = openRecordFlagForField(flags, path);
      const resolved = resolvedRecordFlagsForField(flags, path);
      /* Em revisão histórica não se oferece «adicionar» — só se lê o
       * estado projetado no corte. */
      if (!isCurrentRevision && !openFlag && !resolved.length) {
        return null;
      }
      return (
        <PrcRecordFlagTrigger
          openFlag={openFlag}
          resolvedFlags={resolved}
          label={PRC_FIELD_LABELS[path] || path}
          onOpen={(flag) =>
            openTarget(
              {
                subject: "FIELD",
                targetPath: path,
                currentValue: displayValue,
                fieldLabel: PRC_FIELD_LABELS[path] || path,
              },
              flag,
            )
          }
        />
      );
    },
    [flags, isCurrentRevision, openTarget],
  );

  const supplierAdornment = useCallback(
    (
      row: SupplierRow,
      attribute: "partNumber" | "catalogNumber",
    ) => {
      const openFlag = openRecordFlagForSupplier(
        flags,
        row.supplierCode,
        row.store,
        attribute,
      );
      const resolved = resolvedRecordFlagsForSupplier(
        flags,
        row.supplierCode,
        row.store,
        attribute,
      );
      if (!isCurrentRevision && !openFlag && !resolved.length) {
        return null;
      }
      const label = `${PRC_SUPPLIER_LABELS[attribute] || attribute} — ${row.supplierCode}/${row.store}`;
      return (
        <PrcRecordFlagTrigger
          openFlag={openFlag}
          resolvedFlags={resolved}
          label={label}
          onOpen={(flag) =>
            openTarget(
              {
                subject: "SUPPLIER_LINK",
                targetAttribute: attribute,
                supplierKey: {
                  supplierCode: row.supplierCode,
                  store: row.store,
                },
                currentValue:
                  attribute === "partNumber"
                    ? row.partNumber
                    : row.catalogNumber || "",
                fieldLabel: label,
              },
              flag,
            )
          }
        />
      );
    },
    [flags, isCurrentRevision, openTarget],
  );

  return (
    <div className="engineering-prc__product-sheet" data-readonly="true">
      <PrcTechnicalSheetView
        draft={sheetData}
        requestType="create"
        specNotes={specNotes}
        fieldAdornment={fieldAdornment}
        supplierAdornment={supplierAdornment}
      />
    </div>
  );
}
