/**
 * I18N-01..12 — regression gate da tradução PT-BR do chrome BPMN.
 *
 * O serviço `translate` é o extension point oficial do diagram-js: deve
 * devolver PT-BR para todo template user-facing conhecido, interpolar
 * `{key}` replacements como o stub do vendor e nunca quebrar em strings
 * desconhecidas (fallback = template original).
 */
import { describe, it, expect } from "vitest";
import { translate, bpmnTypeLabel, ptBrTranslateModule } from "./translate";

describe("translate — PT-BR", () => {
  it("I18N-01: grupos do properties panel", () => {
    expect(translate("General")).toBe("Geral");
    expect(translate("Documentation")).toBe("Documentação");
    expect(translate("Multi-instance")).toBe("Multi-instância");
    expect(translate("Timer")).toBe("Temporizador");
    expect(translate("Compensation")).toBe("Compensação");
  });

  it("I18N-02: campos e estados do panel", () => {
    expect(translate("Name")).toBe("Nome");
    expect(translate("Executable")).toBe("Executável");
    expect(translate("Global message reference")).toBe(
      "Referência global de mensagem",
    );
    expect(translate("Select an element to edit its properties.")).toBe(
      "Selecione um elemento para editar suas propriedades.",
    );
    expect(translate("<none>")).toBe("<nenhum>");
  });

  it("I18N-03: tipos de elemento (header do painel)", () => {
    expect(translate("Process")).toBe("Processo");
    expect(translate("Start Event")).toBe("Evento inicial");
    expect(translate("Task")).toBe("Tarefa");
    expect(translate("User Task")).toBe("Tarefa de usuário");
    expect(translate("Exclusive Gateway")).toBe("Gateway exclusivo");
    expect(translate("Event Based Gateway")).toBe("Gateway baseado em eventos");
    expect(translate("Expanded Sub Process")).toBe("Subprocesso expandido");
    expect(translate("Collapsed Sub Process")).toBe("Subprocesso recolhido");
    expect(translate("Sequence Flow")).toBe("Fluxo de sequência");
    expect(translate("Data Store Reference")).toBe(
      "Referência a armazenamento de dados",
    );
  });

  it("I18N-04: tipos compostos por event definition", () => {
    expect(translate("Message Start Event")).toBe(
      "Evento inicial de mensagem",
    );
    expect(translate("Timer Boundary Event")).toBe(
      "Evento de borda temporizado",
    );
    expect(translate("Error End Event")).toBe("Evento final de erro");
    expect(translate("Signal Intermediate Catch Event")).toBe(
      "Evento intermediário de sinal",
    );
  });

  it("I18N-05: sufixo non-interrupting do vendor", () => {
    expect(translate("Start Event (Non Interrupting)")).toBe(
      "Evento inicial (não interruptivo)",
    );
    expect(translate("Message Boundary Event (Non Interrupting)")).toBe(
      "Evento de borda de mensagem (não interruptivo)",
    );
  });

  it("I18N-06: strings do bpmn-js core (palette/context pad)", () => {
    expect(translate("Create task")).toBe("Criar tarefa");
    expect(translate("Append gateway")).toBe("Adicionar gateway");
    expect(translate("Connect to other element")).toBe(
      "Conectar a outro elemento",
    );
    expect(translate("Delete")).toBe("Excluir");
    expect(translate("Change element")).toBe("Trocar elemento");
  });

  it("I18N-07: interpolação de replacements igual ao stub vendor", () => {
    expect(translate("Open {element}", { element: "X" })).toBe("Abrir X");
    // placeholder sem replacement permanece intacto (comportamento vendor)
    expect(translate("Open {element}")).toBe("Abrir {element}");
  });

  it("I18N-08: fallback seguro para string desconhecida", () => {
    expect(translate("Unknown Vendor String")).toBe("Unknown Vendor String");
    expect(translate("Create {type}", { type: "Pool" })).toBe("Create Pool");
  });

  it("I18N-09: módulo didi expõe translate como value", () => {
    expect(ptBrTranslateModule.translate).toEqual(["value", translate]);
  });
});

describe("bpmnTypeLabel — tipos moddle brutos", () => {
  it("I18N-10: strip de prefixo bpmn: + camelCase", () => {
    expect(bpmnTypeLabel("bpmn:StartEvent")).toBe("Evento inicial");
    expect(bpmnTypeLabel("bpmn:ExclusiveGateway")).toBe("Gateway exclusivo");
    expect(bpmnTypeLabel("bpmn:DataStoreReference")).toBe(
      "Referência a armazenamento de dados",
    );
    expect(bpmnTypeLabel("bpmn:BusinessRuleTask")).toBe(
      "Tarefa de regra de negócio",
    );
  });

  it("I18N-11: tipos sem prefixo ou desconhecidos não quebram", () => {
    expect(bpmnTypeLabel("Task")).toBe("Tarefa");
    expect(bpmnTypeLabel("bpmn:CustomThing")).toBe("Custom Thing");
  });
});
