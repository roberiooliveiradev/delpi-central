import { useCallback, useEffect, useRef, useState } from "react";
import type { AppProps } from "../../App";
import { EditableSectionCard } from "../../components/ui/EditableSectionCard";
import { LoadingActivityCard } from "../../components/LoadingActivityCard";
import {
  useLoadingProgress,
  useTrackedSingleFetchProgress,
} from "../../hooks/useSimulatedLoadingProgress";
import { useCollaborativeSectionEdit } from "../../hooks/useCollaborativeSectionEdit";
import { CollaborativePresenceBanner } from "../../components/collaboration/CollaborativePresenceBanner";
import {
  activateRevisao,
  deleteRevisao,
  fetchInvestimentos,
  fetchMedicao,
  fetchRecursos,
  fetchVinculos,
  updateRevisao,
  upsertMedicao,
  type Investimento,
  type Medicao,
  type OptionsData,
  type RecursoCompartilhado,
  type Revisao,
  type VinculoRecurso,
} from "../../data/api/transformometroApi";
import { fetchRevisaoEvidencias } from "../../data/api/transformometroEvidenceApi";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { TRANSFORMOMETRO_API_BASE, buildAuthHeaders } from "../../data/api/transformometroApiBase";
import { RevisaoEvidenciasSection } from "../revisao/cadastro/RevisaoEvidenciasSection";
import { RevisaoDiagramSection } from "../../components/diagram/RevisaoDiagramSection";
import { RevisaoInvestimentosSection } from "../revisao/cadastro/RevisaoInvestimentosSection";
import { RevisaoAtivarToolbar } from "../revisao/cadastro/RevisaoAtivarToolbar";
import { RevisaoMedicaoSection } from "../revisao/cadastro/RevisaoMedicaoSection";
import { RevisaoRecursosSection } from "../revisao/cadastro/RevisaoRecursosSection";
import {
  buildRevisaoVigenciaFromRevisao,
  RevisaoVigenciaSection,
  revisaoPayloadFromVigenciaForm,
} from "../revisao/cadastro/RevisaoVigenciaSection";

type RateioDiagnostic = {
  revisao_id: string;
  processo_id: string;
  competencia?: string | null;
  economia_bruta: number;
  custo_recursos_compartilhados_mes: number;
  economia_liquida_mes: number;
  rateio_excede_ganho: boolean;
  message: string;
};

type ApiEnvelope<T> = { success: boolean; message: string; data: T };

async function fetchRevisaoDiagnosticoRateio(
  revisaoId: string,
  getAccessToken?: () => string | undefined
): Promise<RateioDiagnostic> {
  const response = await fetch(
    `${TRANSFORMOMETRO_API_BASE}/revisoes/${revisaoId}/diagnostico-rateio`,
    { headers: buildAuthHeaders(getAccessToken) }
  );
  const payload = (await response.json()) as ApiEnvelope<RateioDiagnostic>;
  if (!response.ok || !payload.success) {
    throw new Error(payload.message || `Erro HTTP ${response.status}`);
  }
  return payload.data;
}

const emptyMedicao = (revisaoId: string): Medicao => ({
  revisao_id: revisaoId,
  volume_mensal: 0,
  tempo_medio_execucao_min: 0,
  tempo_retrabalho_min: 0,
  percentual_retrabalho: 0,
  percentual_erro: 0,
  quantidade_erros_mes: 0,
  custo_hora_mao_obra: 0,
  custo_unitario_erro: 0,
  custo_unitario_retrabalho: 0,
  custo_outros_desperdicios: 0,
});

type Props = Pick<AppProps, "getAccessToken"> & {
  revisao: Revisao;
  options: OptionsData;
  onError: (message: string | null) => void;
  onRevisaoUpdated: () => void;
  onRevisaoDeleted?: () => void;
};

export function RevisaoCadastroPanel({
  revisao,
  options,
  getAccessToken,
  onError,
  onRevisaoUpdated,
  onRevisaoDeleted,
}: Props) {
  const medicaoSnapshot = useRef<Medicao>(emptyMedicao(revisao.revisao_id));
  const [medicao, setMedicao] = useState<Medicao>(() => emptyMedicao(revisao.revisao_id));
  const [investimentos, setInvestimentos] = useState<Investimento[]>([]);
  const [vinculos, setVinculos] = useState<VinculoRecurso[]>([]);
  const [recursos, setRecursos] = useState<RecursoCompartilhado[]>([]);
  const [evidenciasCount, setEvidenciasCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [savingVigencia, setSavingVigencia] = useState(false);
  const [savingMedicao, setSavingMedicao] = useState(false);
  const [rateioDiag, setRateioDiag] = useState<RateioDiagnostic | null>(null);
  const [revisaoVigencia, setRevisaoVigencia] = useState(() => buildRevisaoVigenciaFromRevisao(revisao));

  useEffect(() => {
    setRevisaoVigencia(buildRevisaoVigenciaFromRevisao(revisao));
  }, [
    revisao.revisao_id,
    revisao.versao_revisao,
    revisao.cenario_tipo,
    revisao.data_inicio_vigencia,
    revisao.data_implantacao,
    revisao.data_fim_vigencia,
    revisao.descricao_revisao,
    revisao.motivo_revisao,
    revisao.observacoes,
  ]);

  const load = useCallback(async () => {
    setLoading(true);
    onError(null);
    try {
      const [med, inv, vin, rec, ev, diag] = await Promise.all([
        fetchMedicao(revisao.revisao_id, getAccessToken),
        fetchInvestimentos(revisao.revisao_id, getAccessToken),
        fetchVinculos(revisao.revisao_id, getAccessToken),
        fetchRecursos(getAccessToken),
        fetchRevisaoEvidencias(revisao.revisao_id, getAccessToken).catch(() => []),
        fetchRevisaoDiagnosticoRateio(revisao.revisao_id, getAccessToken).catch(() => null),
      ]);
      const nextMedicao = med
        ? { ...med, revisao_id: revisao.revisao_id }
        : emptyMedicao(revisao.revisao_id);
      setMedicao(nextMedicao);
      medicaoSnapshot.current = nextMedicao;
      setInvestimentos(inv.items);
      setVinculos(vin.items);
      setRecursos(rec.items);
      setEvidenciasCount(ev.length);
      setRateioDiag(diag);
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao carregar cadastro da revisão");
    } finally {
      setLoading(false);
    }
  }, [getAccessToken, onError, revisao.revisao_id]);

  const sectionEdit = useCollaborativeSectionEdit({
    entityType: "revisao",
    entityId: revisao.revisao_id,
    getAccessToken,
    onResync: () => {
      void load();
      onRevisaoUpdated();
    },
  });

  useEffect(() => {
    void load();
  }, [load]);

  async function saveVigencia() {
    setSavingVigencia(true);
    onError(null);
    try {
      await updateRevisao(
        revisao.revisao_id,
        {
          processo_id: revisao.processo_id,
          ...revisaoPayloadFromVigenciaForm(revisaoVigencia),
        },
        getAccessToken
      );
      sectionEdit.stopEdit("vigencia");
      onRevisaoUpdated();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao salvar vigência da revisão");
    } finally {
      setSavingVigencia(false);
    }
  }

  async function saveMedicao() {
    setSavingMedicao(true);
    onError(null);
    try {
      await upsertMedicao(medicao, getAccessToken);
      sectionEdit.stopEdit("medicao");
      await load();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao salvar medição");
    } finally {
      setSavingMedicao(false);
    }
  }

  function cancelVigencia() {
    setRevisaoVigencia(buildRevisaoVigenciaFromRevisao(revisao));
    sectionEdit.cancelEdit("vigencia");
  }

  function cancelMedicao() {
    setMedicao(medicaoSnapshot.current);
    sectionEdit.cancelEdit("medicao");
  }

  async function handleActivate() {
    onError(null);
    try {
      await activateRevisao(revisao.revisao_id, getAccessToken);
      onRevisaoUpdated();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao ativar revisão");
    }
  }

  async function handleDeleteRevisao() {
    const label = `v${revisao.versao_revisao} (${revisao.cenario_tipo})`;
    if (!window.confirm(`Excluir a revisão ${label}?`)) {
      return;
    }
    onError(null);
    try {
      await deleteRevisao(revisao.revisao_id, getAccessToken);
      onRevisaoDeleted?.();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao excluir revisão");
    }
  }

  const cadastroFetchProgress = useTrackedSingleFetchProgress(loading);
  const cadastroLoadingProgress = useLoadingProgress(loading, cadastroFetchProgress);

  if (loading) {
    return (
      <LoadingActivityCard
        title="Carregando cadastro da revisão"
        description="Medição, investimentos e recursos compartilhados."
        variant="compact"
        progressPercent={cadastroLoadingProgress}
      />
    );
  }

  return (
    <div className="ds-cadastro-panel ds-cadastro-panel--cards">
      <RevisaoAtivarToolbar
        revisao={revisao}
        onError={onError}
        onActivate={handleActivate}
        onDelete={handleDeleteRevisao}
      />

      <CollaborativePresenceBanner
        presence={sectionEdit.presence}
        lockError={sectionEdit.lockError}
        realtimeNotice={sectionEdit.realtimeNotice}
        onDismissRealtimeNotice={sectionEdit.clearRealtimeNotice}
      />

      {rateioDiag ? (
        <div
          className={[
            "ds-card",
            "ds-rateio-diag",
            rateioDiag.rateio_excede_ganho ? "ds-rateio-diag--warn" : "",
          ]
            .filter(Boolean)
            .join(" ")}
          role="status"
        >
          <p className="ds-rateio-diag__message">{rateioDiag.message}</p>
          <p className="ds-hint">
            Competência {rateioDiag.competencia ?? "—"} · bruta{" "}
            {rateioDiag.economia_bruta.toLocaleString("pt-BR")} · recursos{" "}
            {rateioDiag.custo_recursos_compartilhados_mes.toLocaleString("pt-BR")} · líquida{" "}
            {rateioDiag.economia_liquida_mes.toLocaleString("pt-BR")}
          </p>
        </div>
      ) : null}

      <EditableSectionCard
        title="Vigência e identificação"
        description="Versão, cenário e período usados no dashboard."
        isEditing={sectionEdit.isEditing("vigencia")}
        onEdit={() => void sectionEdit.startEdit("vigencia")}
        onCancel={cancelVigencia}
        onSave={() => void saveVigencia()}
        saving={savingVigencia}
        readContent={
          <RevisaoVigenciaSection
            embeddedInCard
            readOnly
            revisaoVigencia={revisaoVigencia}
            options={options}
            onChange={setRevisaoVigencia}
            onSubmit={(event) => event.preventDefault()}
          />
        }
        editContent={
          <RevisaoVigenciaSection
            embeddedInCard
            hideSubmit
            revisaoVigencia={revisaoVigencia}
            options={options}
            onChange={setRevisaoVigencia}
            onSubmit={(event) => {
              event.preventDefault();
              void saveVigencia();
            }}
          />
        }
      />

      <EditableSectionCard
        title="Diagrama da revisão"
        description="Estado visual as-is ou to-be sobre o escopo da instância."
        hint={TM_HELP_TOOLTIPS.revisao.diagramaRevisao}
        isEditing={sectionEdit.isEditing("diagrama_revisao")}
        onEdit={() => void sectionEdit.startEdit("diagrama_revisao")}
        onCancel={() => sectionEdit.cancelEdit("diagrama_revisao")}
        readContent={
          <RevisaoDiagramSection
            embeddedInCard
            readOnly
            revisaoId={revisao.revisao_id}
            cenarioTipo={revisao.cenario_tipo}
            getAccessToken={getAccessToken}
            onError={onError}
            onReload={load}
          />
        }
        editContent={
          <RevisaoDiagramSection
            embeddedInCard
            revisaoId={revisao.revisao_id}
            cenarioTipo={revisao.cenario_tipo}
            getAccessToken={getAccessToken}
            onError={onError}
            onReload={load}
          />
        }
      />

      <EditableSectionCard
        title="Medição operacional"
        description="Volume, tempos e custos usados para calcular economia bruta."
        isEditing={sectionEdit.isEditing("medicao")}
        onEdit={() => {
          medicaoSnapshot.current = medicao;
          void sectionEdit.startEdit("medicao");
        }}
        onCancel={cancelMedicao}
        onSave={() => void saveMedicao()}
        saving={savingMedicao}
        readContent={
          <RevisaoMedicaoSection
            embeddedInCard
            readOnly
            medicao={medicao}
            onChange={setMedicao}
            onSubmit={(event) => event.preventDefault()}
          />
        }
        editContent={
          <RevisaoMedicaoSection
            embeddedInCard
            hideSubmit
            medicao={medicao}
            onChange={setMedicao}
            onSubmit={(event) => {
              event.preventDefault();
              void saveMedicao();
            }}
          />
        }
      />

      <EditableSectionCard
        title={`Investimentos (${investimentos.length})`}
        description="Custos únicos ou recorrentes ligados a esta revisão."
        isEditing={sectionEdit.isEditing("investimentos")}
        onEdit={() => void sectionEdit.startEdit("investimentos")}
        onCancel={() => sectionEdit.cancelEdit("investimentos")}
        readContent={
          <RevisaoInvestimentosSection
            embeddedInCard
            readOnly
            revisaoId={revisao.revisao_id}
            options={options}
            investimentos={investimentos}
            getAccessToken={getAccessToken}
            onError={onError}
            onReload={load}
          />
        }
        editContent={
          <RevisaoInvestimentosSection
            embeddedInCard
            revisaoId={revisao.revisao_id}
            options={options}
            investimentos={investimentos}
            getAccessToken={getAccessToken}
            onError={onError}
            onReload={load}
          />
        }
      />

      <EditableSectionCard
        title={`Recursos compartilhados (${vinculos.length})`}
        description="Ferramentas do catálogo vinculadas ao rateio desta revisão."
        isEditing={sectionEdit.isEditing("recursos")}
        onEdit={() => void sectionEdit.startEdit("recursos")}
        onCancel={() => sectionEdit.cancelEdit("recursos")}
        readContent={
          <RevisaoRecursosSection
            embeddedInCard
            readOnly
            revisaoId={revisao.revisao_id}
            options={options}
            recursos={recursos}
            vinculos={vinculos}
            getAccessToken={getAccessToken}
            onError={onError}
            onReload={load}
          />
        }
        editContent={
          <RevisaoRecursosSection
            embeddedInCard
            revisaoId={revisao.revisao_id}
            options={options}
            recursos={recursos}
            vinculos={vinculos}
            getAccessToken={getAccessToken}
            onError={onError}
            onReload={load}
          />
        }
      />

      <EditableSectionCard
        title={`Evidências${evidenciasCount ? ` (${evidenciasCount})` : ""}`}
        description="Anexos, imagens e links que comprovam a melhoria."
        isEditing={sectionEdit.isEditing("evidencias")}
        onEdit={() => void sectionEdit.startEdit("evidencias")}
        onCancel={() => sectionEdit.cancelEdit("evidencias")}
        readContent={
          <RevisaoEvidenciasSection
            embeddedInCard
            readOnly
            revisaoId={revisao.revisao_id}
            getAccessToken={getAccessToken}
            onError={onError}
            onReload={load}
          />
        }
        editContent={
          <RevisaoEvidenciasSection
            embeddedInCard
            revisaoId={revisao.revisao_id}
            getAccessToken={getAccessToken}
            onError={onError}
            onReload={load}
          />
        }
      />
    </div>
  );
}
