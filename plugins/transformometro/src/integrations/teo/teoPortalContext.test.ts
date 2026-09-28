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
