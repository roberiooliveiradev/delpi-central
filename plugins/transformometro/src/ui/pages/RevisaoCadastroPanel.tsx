import { useCallback, useEffect, useMemo, useState } from "react";
import type { AppProps } from "../../App";
import { LoadingActivityCard } from "../../components/LoadingActivityCard";
import {
  useLoadingProgress,
  useTrackedSingleFetchProgress,
} from "../../hooks/useSimulatedLoadingProgress";
import {
  activateRevisao,
  fetchInvestimentos,
  fetchMedicao,
  fetchRecursos,
  fetchRevisaoDiagnosticoRateio,
  fetchVinculos,
  updateRevisao,
  upsertMedicao,
  type Investimento,
  type Medicao,
  type OptionsData,
  type RateioDiagnostic,
  type RecursoCompartilhado,
  type Revisao,
  type VinculoRecurso,
} from "../../data/api/transformometroApi";
import { CadastroTabs, type CadastroTabId } from "../revisao/cadastro/CadastroTabs";
import { RevisaoInvestimentosSection } from "../revisao/cadastro/RevisaoInvestimentosSection";
import { RevisaoAtivarToolbar } from "../revisao/cadastro/RevisaoAtivarToolbar";
import { RevisaoMedicaoSection } from "../revisao/cadastro/RevisaoMedicaoSection";
import { RevisaoRecursosSection } from "../revisao/cadastro/RevisaoRecursosSection";
import {
  buildRevisaoVigenciaFromRevisao,
  RevisaoVigenciaSection,
  revisaoPayloadFromVigenciaForm,
} from "../revisao/cadastro/RevisaoVigenciaSection";

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
};

export function RevisaoCadastroPanel({
  revisao,
  options,
  getAccessToken,
  onError,
  onRevisaoUpdated,
}: Props) {
  const [activeTab, setActiveTab] = useState<CadastroTabId>("vigencia");
  const [medicao, setMedicao] = useState<Medicao>(() => emptyMedicao(revisao.revisao_id));
  const [investimentos, setInvestimentos] = useState<Investimento[]>([]);
  const [vinculos, setVinculos] = useState<VinculoRecurso[]>([]);
  const [recursos, setRecursos] = useState<RecursoCompartilhado[]>([]);
  const [loading, setLoading] = useState(true);
  const [rateioDiag, setRateioDiag] = useState<RateioDiagnostic | null>(null);
  const [revisaoVigencia, setRevisaoVigencia] = useState(() => buildRevisaoVigenciaFromRevisao(revisao));

  useEffect(() => {
    setRevisaoVigencia(buildRevisaoVigenciaFromRevisao(revisao));
  }, [
    revisao.revisao_id,
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
      const [med, inv, vin, rec, diag] = await Promise.all([
        fetchMedicao(revisao.revisao_id, getAccessToken),
        fetchInvestimentos(revisao.revisao_id, getAccessToken),
        fetchVinculos(revisao.revisao_id, getAccessToken),
        fetchRecursos(getAccessToken),
        fetchRevisaoDiagnosticoRateio(revisao.revisao_id, getAccessToken).catch(() => null),
      ]);
      setMedicao(med ? { ...med, revisao_id: revisao.revisao_id } : emptyMedicao(revisao.revisao_id));
      setInvestimentos(inv.items);
      setVinculos(vin.items);
      setRecursos(rec.items);
      setRateioDiag(diag);
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao carregar cadastro da revisão");
    } finally {
      setLoading(false);
    }
  }, [getAccessToken, onError, revisao.revisao_id]);

  useEffect(() => {
    void load();
  }, [load]);

  const tabs = useMemo(
    () => [
      { id: "vigencia" as const, label: "Vigência" },
      { id: "medicao" as const, label: "Medição" },
      { id: "investimentos" as const, label: "Investimentos", badge: investimentos.length },
      { id: "recursos" as const, label: "Recursos", badge: vinculos.length },
    ],
    [investimentos.length, vinculos.length]
  );

  async function handleSaveRevisaoDatas(e: React.FormEvent) {
    e.preventDefault();
    onError(null);
    try {
      await updateRevisao(
        revisao.revisao_id,
        {
          processo_id: revisao.processo_id,
          versao_revisao: revisao.versao_revisao,
          cenario_tipo: revisao.cenario_tipo,
          revisao_ativa: revisao.revisao_ativa,
          ...revisaoPayloadFromVigenciaForm(revisaoVigencia),
        },
        getAccessToken
      );
      onRevisaoUpdated();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao salvar vigência da revisão");
    }
  }

  async function handleSaveMedicao(e: React.FormEvent) {
    e.preventDefault();
    onError(null);
    try {
      await upsertMedicao(medicao, getAccessToken);
      await load();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao salvar medição");
    }
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
    <div className="ds-cadastro-panel">
      <RevisaoAtivarToolbar revisao={revisao} onError={onError} onActivate={handleActivate} />

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

      <CadastroTabs tabs={tabs} activeTab={activeTab} onTabChange={setActiveTab}>
        {activeTab === "vigencia" ? (
          <RevisaoVigenciaSection
            revisaoVigencia={revisaoVigencia}
            onChange={setRevisaoVigencia}
            onSubmit={handleSaveRevisaoDatas}
          />
        ) : null}
        {activeTab === "medicao" ? (
          <RevisaoMedicaoSection
            medicao={medicao}
            onChange={setMedicao}
            onSubmit={handleSaveMedicao}
          />
        ) : null}
        {activeTab === "investimentos" ? (
          <RevisaoInvestimentosSection
            revisaoId={revisao.revisao_id}
            options={options}
            investimentos={investimentos}
            getAccessToken={getAccessToken}
            onError={onError}
            onReload={load}
          />
        ) : null}
        {activeTab === "recursos" ? (
          <RevisaoRecursosSection
            revisaoId={revisao.revisao_id}
            options={options}
            recursos={recursos}
            vinculos={vinculos}
            getAccessToken={getAccessToken}
            onError={onError}
            onReload={load}
          />
        ) : null}
      </CadastroTabs>
    </div>
  );
}
