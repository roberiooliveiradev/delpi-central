import { describe, expect, it } from "vitest";

import { TRANSFORMOMETRO_ROUTES } from "../../constants/routes";
import {
  PROCESSO_WORKSPACE_SECTIONS,
  PROCESSO_HASH_TO_PRIMARY,
} from "../../ui/processes/processWorkspaceNav";
import {
  buildTeoContextClipboardText,
  resolveTeoPortalContext,
  teoAreaLabel,
  type TeoPortalContext,
} from "./teoPortalContext";

const BASE = TRANSFORMOMETRO_ROUTES.processes;
const PROCESS = `${BASE}/proc-1`;
const INSTANCE = `${PROCESS}/instances/inst-1`;
const REVISION = `${INSTANCE}/revisions/rev-1`;

describe("resolveTeoPortalContext", () => {
  it("A: processo sem melhoria/revisão expõe só process_id", () => {
    const ctx = resolveTeoPortalContext(PROCESS, "");
    expect(ctx.process_id).toBe("proc-1");
    expect(ctx.instance_id).toBeNull();
    expect(ctx.revision_id).toBeNull();
    expect(ctx.area).toBe("visao-geral");
    expect(ctx.canonical_path).toBe(PROCESS);
    expect(ctx.version).toBe("1");
    expect(ctx.product).toBe("transformometro");
  });

  it("B: melhoria expõe process_id + instance_id sem revision_id", () => {
    const ctx = resolveTeoPortalContext(INSTANCE, "");
    expect(ctx.process_id).toBe("proc-1");
    expect(ctx.instance_id).toBe("inst-1");
    expect(ctx.revision_id).toBeNull();
    expect(ctx.area).toBe("dados");
  });

  it("C: revisão expõe os três IDs", () => {
    const ctx = resolveTeoPortalContext(REVISION, "");
    expect(ctx.process_id).toBe("proc-1");
    expect(ctx.instance_id).toBe("inst-1");
    expect(ctx.revision_id).toBe("rev-1");
    expect(ctx.area).toBe("vigencia");
  });

  it("D: cada seção canônica do processo vira area", () => {
    for (const section of PROCESSO_WORKSPACE_SECTIONS) {
      const ctx = resolveTeoPortalContext(PROCESS, `#${section.id}`);
      expect(ctx.area).toBe(section.id);
    }
  });

  it("E: aliases legados de hash normalizam para a seção canônica", () => {
    expect(resolveTeoPortalContext(PROCESS, "#diagrama").area).toBe("mapeamento");
    expect(resolveTeoPortalContext(PROCESS, "#arquivos").area).toBe("documentacao");
    expect(resolveTeoPortalContext(PROCESS, "#priorizacao").area).toBe("melhorias");
    expect(resolveTeoPortalContext(PROCESS, "#dados").area).toBe("visao-geral");
    expect(resolveTeoPortalContext(PROCESS, "#timeline").area).toBe("historico");
    for (const [hash, primary] of Object.entries(PROCESSO_HASH_TO_PRIMARY)) {
      expect(resolveTeoPortalContext(PROCESS, `#${hash}`).area).toBe(primary);
    }
  });

  it("F: mudança de rota atualiza o contexto (não há cache)", () => {
    const r1 = resolveTeoPortalContext(`${INSTANCE}/revisions/rev-1`, "");
    const r2 = resolveTeoPortalContext(`${INSTANCE}/revisions/rev-2`, "");
    expect(r1.revision_id).toBe("rev-1");
    expect(r2.revision_id).toBe("rev-2");
  });

  it("G: sair da revisão remove revision_id (sem stale)", () => {
    const ctx = resolveTeoPortalContext(INSTANCE, "");
    expect(ctx.revision_id).toBeNull();
    expect(ctx.instance_id).toBe("inst-1");
  });

  it("H: sair da melhoria remove instance_id e revision_id", () => {
    const ctx = resolveTeoPortalContext(PROCESS, "");
    expect(ctx.instance_id).toBeNull();
    expect(ctx.revision_id).toBeNull();
  });

  it("I: páginas fora do workspace de processo não carregam IDs", () => {
    for (const path of [
      TRANSFORMOMETRO_ROUTES.home,
      TRANSFORMOMETRO_ROUTES.dashboard,
      TRANSFORMOMETRO_ROUTES.settingsUnits,
      TRANSFORMOMETRO_ROUTES.meetingMinutes,
      `${TRANSFORMOMETRO_ROUTES.meetingMinutes}/ata-1`,
      BASE,
    ]) {
      const ctx = resolveTeoPortalContext(path, "");
      expect(ctx.process_id).toBeNull();
      expect(ctx.instance_id).toBeNull();
      expect(ctx.revision_id).toBeNull();
      expect(ctx.area).toBeNull();
      expect(ctx.canonical_path).toBe(path);
    }
  });

  it("J: o contrato não carrega token, permissão ou PII", () => {
    const ctx = resolveTeoPortalContext(REVISION, "#medicao");
    expect(Object.keys(ctx).sort()).toEqual([
      "area",
      "canonical_path",
      "instance_id",
      "process_id",
      "product",
      "revision_id",
      "version",
    ]);
    const serialized = JSON.stringify(ctx).toLowerCase();
    for (const forbidden of ["token", "authorization", "permission", "email", "cookie"]) {
      expect(serialized).not.toContain(forbidden);
    }
  });

  it("rotas PT legadas resolvem os mesmos IDs e canonical_path EN", () => {
    const ctx = resolveTeoPortalContext(
      "/apps/transformometro/processos/proc-1/instancias/inst-1/revisoes/rev-1",
      "",
    );
    expect(ctx.process_id).toBe("proc-1");
    expect(ctx.instance_id).toBe("inst-1");
    expect(ctx.revision_id).toBe("rev-1");
    expect(ctx.canonical_path).toBe(REVISION);
  });

  it("edição de diagrama mapeia para a área dona", () => {
    expect(resolveTeoPortalContext(`${PROCESS}/diagram/edit`, "").area).toBe("mapeamento");
    expect(resolveTeoPortalContext(`${INSTANCE}/diagram/edit`, "").area).toBe("diagrama");
    expect(resolveTeoPortalContext(`${REVISION}/diagram/edit`, "").area).toBe("diagrama");
  });

  it("canonical_path preserva o hash para deep link", () => {
    const ctx = resolveTeoPortalContext(PROCESS, "#resultados");
    expect(ctx.canonical_path).toBe(`${PROCESS}#resultados`);
  });
});

describe("resolveTeoPortalContext + workspace selection", () => {
  it("A: rota process-only sem seleção publicada", () => {
    const ctx = resolveTeoPortalContext(PROCESS, "#resultados", null);
    expect(ctx.process_id).toBe("proc-1");
    expect(ctx.instance_id).toBeNull();
    expect(ctx.revision_id).toBeNull();
    expect(ctx.area).toBe("resultados");
  });

  it("B: rota process + melhoria selecionada no workspace", () => {
    const ctx = resolveTeoPortalContext(PROCESS, "#resultados", {
      process_id: "proc-1",
      instance_id: "inst-1",
      revision_id: null,
    });
    expect(ctx.instance_id).toBe("inst-1");
    expect(ctx.revision_id).toBeNull();
  });

  it("C: rota process + melhoria + cenário selecionados", () => {
    const ctx = resolveTeoPortalContext(PROCESS, "#resultados", {
      process_id: "proc-1",
      instance_id: "inst-1",
      revision_id: "rev-1",
    });
    expect(ctx.process_id).toBe("proc-1");
    expect(ctx.instance_id).toBe("inst-1");
    expect(ctx.revision_id).toBe("rev-1");
  });

  it("D: troca de cenário R1→R2 sem mudar rota atualiza o contexto", () => {
    const r1 = resolveTeoPortalContext(PROCESS, "#resultados", {
      process_id: "proc-1",
      instance_id: "inst-1",
      revision_id: "rev-1",
    });
    const r2 = resolveTeoPortalContext(PROCESS, "#resultados", {
      process_id: "proc-1",
      instance_id: "inst-1",
      revision_id: "rev-2",
    });
    expect(r1.revision_id).toBe("rev-1");
    expect(r2.revision_id).toBe("rev-2");
  });

  it("E: troca de melhoria nunca mistura revisão da melhoria anterior", () => {
    const mixed = resolveTeoPortalContext(PROCESS, "#resultados", {
      process_id: "proc-1",
      instance_id: "inst-2",
      revision_id: null,
    });
    expect(mixed.instance_id).toBe("inst-2");
    expect(mixed.revision_id).toBeNull();

    const selected = resolveTeoPortalContext(PROCESS, "#resultados", {
      process_id: "proc-1",
      instance_id: "inst-2",
      revision_id: "rev-9",
    });
    expect(selected.revision_id).toBe("rev-9");
  });

  it("F: limpar cenário remove revision_id", () => {
    const ctx = resolveTeoPortalContext(PROCESS, "#resultados", {
      process_id: "proc-1",
      instance_id: "inst-1",
      revision_id: null,
    });
    expect(ctx.revision_id).toBeNull();
  });

  it("G: limpar melhoria remove instance_id e revision_id", () => {
    const ctx = resolveTeoPortalContext(PROCESS, "#resultados", {
      process_id: "proc-1",
      instance_id: null,
      revision_id: null,
    });
    expect(ctx.instance_id).toBeNull();
    expect(ctx.revision_id).toBeNull();
  });

  it("H: troca de seção mantém a seleção e muda area", () => {
    const selection = {
      process_id: "proc-1",
      instance_id: "inst-1",
      revision_id: "rev-1",
    };
    const resultados = resolveTeoPortalContext(PROCESS, "#resultados", selection);
    const mapeamento = resolveTeoPortalContext(PROCESS, "#mapeamento", selection);
    expect(resultados.area).toBe("resultados");
    expect(mapeamento.area).toBe("mapeamento");
    expect(resultados.revision_id).toBe("rev-1");
    expect(mapeamento.revision_id).toBe("rev-1");
  });

  it("I: rota explícita de revisão prevalece sobre a seleção", () => {
    const ctx = resolveTeoPortalContext(REVISION, "", {
      process_id: "proc-1",
      instance_id: "inst-9",
      revision_id: "rev-9",
    });
    expect(ctx.process_id).toBe("proc-1");
    expect(ctx.instance_id).toBe("inst-1");
    expect(ctx.revision_id).toBe("rev-1");
  });

  it("rota de instância explícita não herda revisão de outra melhoria", () => {
    const ctx = resolveTeoPortalContext(`${BASE}/proc-1/instances/inst-2`, "", {
      process_id: "proc-1",
      instance_id: "inst-1",
      revision_id: "rev-1",
    });
    expect(ctx.instance_id).toBe("inst-2");
    expect(ctx.revision_id).toBeNull();
  });

  it("rota de instância explícita aceita revisão da mesma melhoria selecionada", () => {
    const ctx = resolveTeoPortalContext(INSTANCE, "", {
      process_id: "proc-1",
      instance_id: "inst-1",
      revision_id: "rev-1",
    });
    expect(ctx.instance_id).toBe("inst-1");
    expect(ctx.revision_id).toBe("rev-1");
  });

  it("seleção de outro processo é ignorada", () => {
    const ctx = resolveTeoPortalContext(PROCESS, "#resultados", {
      process_id: "proc-outro",
      instance_id: "inst-x",
      revision_id: "rev-x",
    });
    expect(ctx.process_id).toBe("proc-1");
    expect(ctx.instance_id).toBeNull();
    expect(ctx.revision_id).toBeNull();
  });

  it("M: múltiplas melhorias sem seleção explícita — sem fallback", () => {
    const ctx = resolveTeoPortalContext(PROCESS, "#resultados", {
      process_id: "proc-1",
      instance_id: null,
      revision_id: null,
    });
    expect(ctx.instance_id).toBeNull();
    expect(ctx.revision_id).toBeNull();
  });

  it("não aplica seleção fora do workspace de processo", () => {
    const ctx = resolveTeoPortalContext(TRANSFORMOMETRO_ROUTES.dashboard, "", {
      process_id: "proc-1",
      instance_id: "inst-1",
      revision_id: "rev-1",
    });
    expect(ctx.process_id).toBeNull();
    expect(ctx.instance_id).toBeNull();
    expect(ctx.revision_id).toBeNull();
  });
});

describe("teoAreaLabel", () => {
  it("rotula a seção conforme a view", () => {
    expect(teoAreaLabel("processo", "resultados")).toBe("Resultados");
    expect(teoAreaLabel("instancia", "contexto")).toBe("Contexto operacional");
    expect(teoAreaLabel("revisao", "medicao")).toBe("Medição operacional");
  });

  it("retorna null sem área", () => {
    expect(teoAreaLabel("processo", null)).toBeNull();
  });
});

describe("buildTeoContextClipboardText", () => {
  it("K: copia só campos preenchidos, sem token nem payload completo", () => {
    const full = buildTeoContextClipboardText(
      resolveTeoPortalContext(REVISION, "#medicao"),
    );
    expect(full).toContain("process_id=proc-1");
    expect(full).toContain("instance_id=inst-1");
    expect(full).toContain("revision_id=rev-1");
    expect(full).toContain("area=medicao");
    expect(full).not.toMatch(/token|authorization|cookie|permission/i);

    const partial = buildTeoContextClipboardText(resolveTeoPortalContext(PROCESS, ""));
    expect(partial).toContain("process_id=proc-1");
    expect(partial).not.toContain("instance_id");
    expect(partial).not.toContain("revision_id");
    expect(partial).not.toContain("null");
    expect(partial).not.toContain("undefined");
  });
});

describe("TeoPortalContext shape", () => {
  it("mantém o contrato v1", () => {
    const ctx: TeoPortalContext = resolveTeoPortalContext(REVISION, "");
    expect(ctx).toMatchObject({
      version: "1",
      product: "transformometro",
      process_id: "proc-1",
      instance_id: "inst-1",
      revision_id: "rev-1",
    });
  });
});

describe("deep-linked selection — process sections on nested routes", () => {
  it("P: /P/I/R#resultados resolve P/I/R + area resultados direto da rota", () => {
    const ctx = resolveTeoPortalContext(REVISION, "#resultados");
    expect(ctx.process_id).toBe("proc-1");
    expect(ctx.instance_id).toBe("inst-1");
    expect(ctx.revision_id).toBe("rev-1");
    expect(ctx.area).toBe("resultados");
    expect(ctx.canonical_path).toBe(REVISION + "#resultados");
  });

  it("/P/I#resultados resolve P/I + area resultados", () => {
    const ctx = resolveTeoPortalContext(INSTANCE, "#resultados");
    expect(ctx.instance_id).toBe("inst-1");
    expect(ctx.revision_id).toBeNull();
    expect(ctx.area).toBe("resultados");
  });

  it("hash de seção do próprio nível continua área do nível", () => {
    expect(resolveTeoPortalContext(REVISION, "#medicao").area).toBe("medicao");
    expect(resolveTeoPortalContext(INSTANCE, "#contexto").area).toBe("contexto");
    // #mapeamento é ambíguo: level-wins mantém a seção do nível.
    expect(resolveTeoPortalContext(REVISION, "#mapeamento").area).toBe("mapeamento");
    expect(resolveTeoPortalContext(INSTANCE, "#mapeamento").area).toBe("mapeamento");
  });

  it("aliases legados de processo em rota aninhada resolvem a seção do processo", () => {
    expect(resolveTeoPortalContext(REVISION, "#timeline").area).toBe("historico");
    expect(resolveTeoPortalContext(INSTANCE, "#arquivos").area).toBe("documentacao");
  });

  it("contexto não depende da seleção publicada quando a rota já tem P/I/R", () => {
    const ctx = resolveTeoPortalContext(REVISION, "#resultados", null);
    expect(ctx).toMatchObject({
      process_id: "proc-1",
      instance_id: "inst-1",
      revision_id: "rev-1",
      area: "resultados",
    });
  });

  it("fixture de aceite real: URL completa produz o contexto esperado", () => {
    const path =
      "/apps/transformometro/processes/801f161a-71e6-4591-865c-eff294525420" +
      "/instances/b8625950-d369-471f-83f4-c15b7c72cae5" +
      "/revisions/4298dfe5-a615-4467-87c0-fc5323231973";
    const ctx = resolveTeoPortalContext(path, "#resultados");
    expect(ctx).toMatchObject({
      process_id: "801f161a-71e6-4591-865c-eff294525420",
      instance_id: "b8625950-d369-471f-83f4-c15b7c72cae5",
      revision_id: "4298dfe5-a615-4467-87c0-fc5323231973",
      area: "resultados",
      canonical_path: path + "#resultados",
    });
  });
});
