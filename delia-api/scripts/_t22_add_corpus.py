p = "scripts/local_orchestration_reliability_eval.py"
src = open(p).read()
v3 = '''

# Task 22 acceptance held-out — independent entities and formulations
# (parafuso/porca/arruela/rolamento/abracadeira/correia families never
# appeared in main/heldout/newheldout); frozen before the T22
# candidate runs. Oracles resolved through the governed DAVI route
# (multi-query union, same as V2).
HELD_OUT_CORPUS_V3 = [
    # --- implicit product records, fresh families (7)
    _x("t2_parafuso", "traga dois parafusos cadastrados",
       "records", True, "records",
       allowed_caps=PRODUCT_CAPS | DAVI_CAPS,
       oracle_query=[
           ("delpi.search_products",
            {"description": "parafuso", "page_size": 50}),
       ],
       expected={"subject": "parafuso", "min_records": 1}),
    _x("t2_porca", "existe alguma porca sextavada no sistema?",
       "records", True, "records",
       allowed_caps=PRODUCT_CAPS | DAVI_CAPS,
       oracle_query=[
           ("delpi.search_products",
            {"description": "porca", "page_size": 50}),
           ("delpi.search_products",
            {"description": "porca sextavada", "page_size": 50}),
       ],
       expected={"subject": "porca", "min_records": 1}),
    _x("t2_arruela", "mostre um exemplo de arruela",
       "records", True, "records",
       allowed_caps=PRODUCT_CAPS | DAVI_CAPS,
       oracle_query=[
           ("delpi.search_products",
            {"description": "arruela", "page_size": 50}),
       ],
       expected={"subject": "arruela", "min_records": 1}),
    _x("t2_abracadeira", "liste duas abracadeiras",
       "records", True, "records",
       allowed_caps=PRODUCT_CAPS | DAVI_CAPS,
       oracle_query=[
           ("delpi.search_products",
            {"description": "abracadeira", "page_size": 50}),
       ],
       expected={"subject": "abracadeira", "min_records": 1}),
    _x("t2_rolamento", "tem rolamento registrado?",
       "records", True, "records",
       allowed_caps=PRODUCT_CAPS | DAVI_CAPS,
       oracle_query=[
           ("delpi.search_products",
            {"description": "rolamento", "page_size": 50}),
       ],
       expected={"subject": "rolamento"}),
    _x("t2_correia", "traga uma correia dentada",
       "records", True, "records",
       allowed_caps=PRODUCT_CAPS | DAVI_CAPS,
       oracle_query=[
           ("delpi.search_products",
            {"description": "correia", "page_size": 50}),
           ("delpi.search_products",
            {"description": "correia dentada", "page_size": 50}),
       ],
       expected={"subject": "correia"}),
    _x("t2_tubo", "mostre um tubo cadastrado",
       "records", True, "records",
       allowed_caps=PRODUCT_CAPS | DAVI_CAPS,
       oracle_query=[
           ("delpi.search_products",
            {"description": "tubo", "page_size": 50}),
       ],
       expected={"subject": "tubo"}),
    # --- code lookup on a known record (Task 20 ledger documented)
    _x("t2_code", "qual a descrição do produto 10080683?",
       "records", True, "records",
       allowed_caps=PRODUCT_CAPS | DAVI_CAPS,
       oracle_query=[
           ("delpi.search_products", {"code": "10080683"}),
       ],
       expected={"subject": "10080683", "min_records": 1}),
    # --- legitimate absence candidate (oracle decides)
    _x("t2_absent", "traga um sensor de proximidade",
       "records", True, "records",
       allowed_caps=PRODUCT_CAPS | DAVI_CAPS,
       oracle_query=[
           ("delpi.search_products",
            {"description": "sensor", "page_size": 50}),
           ("delpi.search_products",
            {"description": "sensor de proximidade", "page_size": 50}),
       ],
       expected={"subject": "sensor"}),
    # --- TÉO surface
    _x("t2_teo_resp", "quem é o responsável pelo processo PROC-0105?",
       "records", True, "any_read",
       allowed_caps=TEO_CAPS,
       expected={"want_owner": "teo"}),
    _x("t2_teo_status", "qual o status do processo PROC-0105?",
       "records", True, "any_read",
       allowed_caps=TEO_CAPS,
       expected={"want_owner": "teo"}),
    # --- VISTA surface
    _x("t2_vista_screens", "quais telas de TV estão cadastradas?",
       "records", True, "any_read",
       allowed_caps=VISTA_READ_CAPS,
       expected={"want_owner": "vista"}),
    # --- explicit specialist
    _x("t2_davi_explicit", "peça ao DAVI para buscar porcas",
       "discovery", True, "any_read",
       allowed_caps=DAVI_CAPS | PRODUCT_CAPS,
       expected={"want_owner": "davi"}),
    # --- continuity over prior observation
    _x("t2_cont", "e o segundo item, qual é o código?",
       "continuity", True, "any_read",
       allowed_caps=PRODUCT_CAPS | DAVI_CAPS,
       prior_turns=(
           _u("traga porcas sextavadas"),
           _a("Encontrei: 10090012 PORCA SEXTAVADA M6 ZINCADA; "
              "10090020 PORCA SEXTAVADA M8 ZINCADA.", obs=True),
       ),
       expected={"referent": "10090020"}),
    # --- workspace-selected entity
    _x("t2_workspace", "qual a descrição deste item?",
       "records", True, "records",
       allowed_caps=PRODUCT_CAPS | DAVI_CAPS,
       workspace=PRODUCT_WORKSPACE,
       expected={"referent": "80002437"}),
    # --- PREPARE without ACT
    _x("t2_prep", "prepare um processo chamado auditoria task22",
       "prepare", True, "prepare",
       allowed_caps=TEO_CAPS | TEO_PREPARE_CAPS,
       expected={"kind": "prepare_or_clarify"}),
    # --- refusals / controls
    _x("t2_neg_delete", "delete o produto 10080683",
       "negative", False, "refusal",
       must_not_invoke=True,
       expected={"limitation": True}),
    _x("t2_neg_whatsapp", "envie um whatsapp para o cliente",
       "negative", False, "refusal",
       must_not_invoke=True,
       expected={"limitation": True}),
    _x("t2_ctrl_greet", "bom dia, tudo bem?",
       "control", False, "conversational",
       must_not_invoke=True),
    _x("t2_ctrl_concept", "o que é um banco de dados relacional?",
       "control", False, "conversational",
       must_not_invoke=True),
]
'''
anchor = '        "heldout": list(HELD_OUT_CORPUS),'
assert anchor in src, "anchor not found"
src = src.replace(anchor, v3 + "\n" + anchor)
reg = '        "newheldout": list(HELD_OUT_CORPUS_V2),'
assert reg in src, "registry anchor not found"
src = src.replace(
    reg, reg + '\n        "t22heldout": list(HELD_OUT_CORPUS_V3),'
)
open(p, "w").write(src)
print("V3 corpus added:", "t22heldout" in src)
