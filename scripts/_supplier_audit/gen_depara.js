#!/usr/bin/env node
// Generates the FINAL SUPPLIER FIELD MAPPING markdown from SX3 dump.
// Input: scripts/_supplier_audit/.work/sa2_full.txt (pipe-separated, CP1252)
const fs = require('fs');
const raw = fs.readFileSync('scripts/_supplier_audit/.work/sa2_full.txt', 'latin1').split(/\r?\n/);
const ROWS = [];
for (const line of raw) {
  const pr = line.split('|'); const p = pr.map(c => c.trim());
  if (p.length < 17 || !p[1] || !p[1].startsWith('A2_')) continue;
  ROWS.push({ ord:p[0], campo:p[1], tipo:p[2], tam:p[3], dec:p[4], titulo:p[5], descr:p[6],
    picture:p[7], valid:p[8], relacao:p[9], f3:p[10], cbox:p[11], when:p[12],
    obrigat:pr[13], propri:p[14], usado:p[15], browse:p[16] });
}

const VIRTUAL = new Set(['A2_DTPAWB','A2_NOMFAV','A2_PAISDES']);
const ACCUM = new Set(['A2_LC','A2_MATR','A2_MCOMPRA','A2_METR','A2_MSALDO','A2_NROCOM','A2_PRICOM',
  'A2_SALDUP','A2_SALDUPM','A2_ULTCOM','A2_DESVIO','A2_MNOTA','A2_DATBLO','A2_OK','A2_INCLTMG',
  'A2_FILDEB','A2_FILTRF']);
const ONLY_0105 = new Set(['A2_YROHS','A2_YFGEN','A2_PABCB','A2_ECDTEX','A2_ECSEQ','A2_ECFLAG']);
const BANK = new Set(['A2_BANCO','A2_AGENCIA','A2_DVAGE','A2_NUMCON','A2_DVCTA','A2_TIPCTA','A2_TPCONTA','A2_SWIFT','A2_CODFAV','A2_LOJFAV']);
const SENS_DOC = new Set(['A2_CGC','A2_PFISICA','A2_INSCR','A2_INSCRM','A2_NIFEX','A2_CGCEX','A2_CODNIT','A2_DTNASC','A2_CIVIL','A2_SEXO','A2_CBO']);
const CONTACT = new Set(['A2_TEL','A2_DDD','A2_DDI','A2_FAX','A2_TELEX','A2_EMAIL','A2_HPAGE','A2_NOMRESP','A2_CONTCOM','A2_CONTATO']);

const LOOKUP = {
 A2_EST:['SX5','12+UF'], A2_COD_MUN:['CC2','EST+CODMUN'], A2_CODPAIS:['CCH','CODIGO'],
 A2_PAIS:['SYA','CODGI'], A2_COND:['SE4','CODIGO'], A2_NATUREZ:['SED','CODIGO'],
 A2_BANCO:['SA6','COD+AGENCIA+NUMCON'], A2_CONTA:['CT1','CONTA'], A2_FORMPAG:['SX5','58+CHAVE'],
 A2_TRANSP:['SA4','COD'], A2_GRUPO:['SX5','Y7+CHAVE'], A2_SATIV1:['SX5','T3+CHAVE'],
 A2_CLIENTE:['SA1','COD+LOJA'], A2_NUMRA:['SRA','RA_MAT'], A2_CODADM:['SAE','COD'],
 A2_DDI:['ACJ','DDI'], A2_ORIG_1:['SYR','ORIGEM'], A2_ORIG_2:['SYR','ORIGEM'], A2_ORIG_3:['SYR','ORIGEM'],
 A2_SIGLCR:['BA4','SIGLCR+CONREG (tabela ausente)'], A2_ZTABPRC:['AIA','CODFOR+LOJFOR+CODTAB'],
 A2_CATEFD:['S049BR','eSocial categoria'], A2_IBGE:['AM1','IBGE'], A2_VINCULO:['CC1','CODIGO'],
 A2_CODFAV:['SA2','COD+LOJA (self)'], A2_REPRES:['SA2','COD+LOJA (self)'], A2_PAISEX:['SYA','CODGI'],
 A2_REPPAIS:['SYA','CODGI'], A2_PAISSUB:['SYA','CODGI'], A2_RESPTRI:['SX5','83+CHAVE'],
 A2_TIPAWB:['SX5','MF+CHAVE'], A2_CODMUN:['S1','municipio ZF'], A2_GENTIL1:['SX5','48+CHAVE'],
};

const SEM = {
 A2_FILIAL:'branch', A2_COD:'supplier_code', A2_LOJA:'supplier_store', A2_NOME:'legal_name',
 A2_NREDUZ:'trade_name', A2_CGC:'tax_document', A2_TIPO:'person_type', A2_INSCR:'state_registration',
 A2_INSCRM:'city_registration', A2_END:'street', A2_NR_END:'street_number', A2_ENDCOMP:'complement',
 A2_COMPLEM:'complement_alt', A2_BAIRRO:'district', A2_CEP:'postal_code', A2_MUN:'city',
 A2_COD_MUN:'city_ibge_code', A2_EST:'state', A2_ESTADO:'state_name', A2_CODPAIS:'country_bacen_code',
 A2_PAIS:'country_code', A2_CX_POST:'po_box', A2_TPLOGR:'street_type', A2_IBGE:'ibge_code',
 A2_MUNSC:'city_code_sc', A2_CODSIAF:'city_code_siaf',
 A2_CONTATO:'contact_person', A2_CONTCOM:'commercial_contact', A2_TEL:'phone', A2_DDD:'phone_ddd',
 A2_DDI:'phone_ddi', A2_FAX:'fax', A2_TELEX:'telex', A2_EMAIL:'email', A2_HPAGE:'website',
 A2_NOMRESP:'responsible_name', A2_CARGO:'responsible_role', A2_MSBLQL:'blocked_flag',
 A2_COND:'payment_condition', A2_FORMPAG:'payment_method', A2_NATUREZ:'finance_nature',
 A2_CONTA:'ledger_account', A2_TRANSP:'carrier_code', A2_GRUPO:'group_code', A2_SATIV1:'segment_code',
 A2_CLIENTE:'linked_customer_code', A2_LOJCLI:'linked_customer_store', A2_NUMRA:'linked_employee',
 A2_CODADM:'administrator_code', A2_VINCULO:'link_type', A2_BANCO:'bank_code', A2_AGENCIA:'bank_branch',
 A2_DVAGE:'bank_branch_digit', A2_NUMCON:'bank_account', A2_DVCTA:'bank_account_digit',
 A2_TIPCTA:'account_type', A2_TPCONTA:'account_type_alt', A2_SWIFT:'swift_code',
 A2_CODFAV:'payee_code', A2_LOJFAV:'payee_store', A2_NOMFAV:'payee_name',
 A2_YROHS:'rohs_flag', A2_YFGEN:'generic_supplier_flag', A2_ZTABPRC:'purchase_price_table',
 A2_TPESSOA:'person_category', A2_CONTRIB:'icms_contributor', A2_GRPTRIB:'tax_group',
 A2_CNAE:'cnae', A2_CBO:'cbo', A2_CIVIL:'civil_status', A2_SEXO:'gender', A2_DTNASC:'birth_date',
 A2_SIMPNAC:'simples_nacional', A2_TPJ:'legal_entity_type', A2_REGESIM:'simp_regime',
 A2_REGPB:'regime_pb', A2_RESPTRI:'tax_regime_resp', A2_TPCON:'contract_type', A2_CTARE:'ct_are',
 A2_PFISICA:'national_id_doc', A2_NIFEX:'foreign_tax_id', A2_CGCEX:'foreign_doc', A2_MOTNIF:'nif_reason',
 A2_NEMPR:'foreign_company_name', A2_BREEX:'foreign_branch', A2_TPREX:'foreign_type',
 A2_TRBEX:'foreign_trib', A2_UFFIC:'fiscal_uf', A2_PAISEX:'foreign_country', A2_PAISSUB:'country_subst',
 A2_LOGEX:'foreign_street', A2_NUMEX:'foreign_number', A2_COMPLR:'foreign_complement',
 A2_BAIEX:'foreign_district', A2_POSEX:'foreign_postal', A2_CIDEX:'foreign_city', A2_ESTEX:'foreign_state',
 A2_CONREG:'council_reg_number', A2_SIGLCR:'council_sigla', A2_PAGAMEN:'payment_freq',
 A2_ROYMIN:'min_royalty', A2_SUBCOD:'sub_code', A2_ABICS:'abics_code', A2_DATBLO:'blocked_since',
 A2_NUMDEP:'dependents', A2_CODNIT:'nit_pis', A2_CPFRUR:'rural_cpf', A2_CPFIRP:'irpf_cpf',
 A2_IRPROG:'ir_prog_flag', A2_OCORREN:'occurrence', A2_ECFLAG:'ecommerce_flag',
 A2_IDHIST:'history_id', A2_ID_FBFN:'fiscal_id', A2_PABCB:'bc_pa', A2_ECDTEX:'ec_dt',
 A2_ECSEQ:'ec_seq', A2_DTVAL:'valid_until', A2_FATAVA:'eval_factor', A2_DTAVA:'eval_date',
 A2_RISCO:'risk_code', A2_STATUS:'status', A2_LC:'credit_limit', A2_ORIG_1:'origin_1',
 A2_ORIG_2:'origin_2', A2_ORIG_3:'origin_3', A2_PLFIL:'pl_fil', A2_PLPEDES:'pl_pedes',
 A2_PLGRUPO:'pl_group', A2_PLCRRES:'pl_crres', A2_MJURIDI:'legal_month', A2_DESBLO:'unblock',
 A2_NIF:'nif', A2_INOVAUT:'inova_auto', A2_INDRUR:'rural_indicator', A2_INDCP:'cp_indicator',
 A2_MINIRF:'min_irf', A2_MINPUB:'min_pub', A2_IMPIP:'imp_ip', A2_GROSSIR:'gross_ir',
 A2_FORNEMA:'forn_ma', A2_DEDBSPC:'ded_bspc', A2_CPRB:'cprb',
 A2_CATEFD:'esocial_category', A2_CODPUR:'purchase_code', A2_RECISS:'iss_withholding',
 A2_RECINSS:'inss_withholding', A2_RECFET:'fet_withholding', A2_RECSEST:'senat_sest',
 A2_RECCIDE:'cide_withholding', A2_RECFMD:'fmd_withholding', A2_RFACS:'rf_acs', A2_RFABOV:'rf_abov',
 A2_RFUNDES:'r_fundes', A2_RFASEMT:'rf_asemt', A2_RIMAMT:'ri_mamt', A2_INCULT:'incult_flag',
 A2_FOMEZER:'fome_zero', A2_CONTPRE:'contract_prev', A2_CALCIRF:'calc_irf', A2_CALCINP:'calc_inp',
 A2_PAGGFE:'pag_gfe', A2_RECCSLL:'csll_withholding', A2_RECCOFI:'cofins_withholding',
 A2_RECPIS:'pis_withholding', A2_TIPORUR:'rural_type', A2_B2B:'b2b_flag', A2_VINCULA:'vincula_flag',
 A2_ID_REPR:'repr_id', A2_REPRES:'representative_code', A2_REPCONT:'repr_contact',
 A2_REPRTEL:'repr_phone', A2_REPRFAX:'repr_fax', A2_REPR_EM:'repr_email', A2_REPR_EN:'repr_street',
 A2_REPR_BA:'repr_district', A2_REPR_MU:'repr_city', A2_REPR_ET:'repr_state', A2_REPR_CE:'repr_postal',
 A2_REPR_PA:'repr_country', A2_REPRCGC:'repr_tax_doc', A2_NUMPRO:'process_number', A2_DOSSIE:'dossier',
 A2_PUBLI:'publish_flag', A2_DTINIR:'risk_start', A2_DTFIMR:'risk_end', A2_MOTBLO:'block_reason',
 A2_SITEXP:'export_situation', A2_ORIGEM:'origin', A2_CTRLDOC:'doc_control', A2_ENVCATP:'env_catp',
 A2_BOLINSS:'inss_bill', A2_FILDEB:'debit_branch', A2_FILTRF:'transfer_branch', A2_SATIV2:'segment2',
 A2_SATIV3:'segment3', A2_MUN_ENT:'delivery_city', A2_CODMUN:'zf_city_code', A2_GENTIL1:'gentileza1',
 A2_TELCOM:'commercial_phone', A2_CPFCNPJ:'cpf_cnpj_alt', A2_FRET:'freight', A2_MOEDA:'currency',
 A2_IDPAIS:'country_id', A2_USALIB:'release_use', A2_LISCTP:'ctp_list', A2_EMPTIT:'title_company',
};

function normz(r){
  const n=[];
  if(['A2_COD','A2_LOJA'].includes(r.campo)) n.push('RTRIM+zfill');
  if(['A2_CGC','A2_CEP','A2_TEL','A2_DDD','A2_FAX','A2_INSCR','A2_INSCRM','A2_PFISICA','A2_CODNIT','A2_NR_END','A2_CX_POST'].includes(r.campo)) n.push('digits-only');
  if(['A2_EST','A2_SWIFT','A2_SIGLCR'].includes(r.campo)) n.push('uppercase');
  if(r.campo==='A2_EMAIL') n.push('lowercase');
  if(r.tipo==='D') n.push('YYYYMMDD');
  if(r.picture && (r.picture.startsWith('@R')||r.picture.startsWith('@!'))) n.push('picture:'+r.picture.trim());
  return n.length?n.join('; '):'—';
}
function sens(r){
  if(BANK.has(r.campo)) return 'sensitive (banking)';
  if(SENS_DOC.has(r.campo)) return 'fiscal/PII';
  if(CONTACT.has(r.campo)) return 'contact PII';
  if(['A2_CONTA','A2_NATUREZ','A2_COND','A2_LC','A2_RISCO','A2_STATUS','A2_MSALDO','A2_SALDUP'].includes(r.campo)) return 'financial';
  return '—';
}
function cls(r){
  const c=r.campo;
  if(VIRTUAL.has(c)||ACCUM.has(c)) return 'DO_NOT_SEND';
  if(c==='A2_FILIAL'||c==='A2_COD') return 'SYSTEM_GENERATED';
  if(c==='A2_LOJA') return 'UNKNOWN';
  if(r.when.trim()) return 'CONDITIONAL';
  if(r.obrigat.charAt(0)==='x') return 'CANDIDATE_REQUIRED';
  if(['A2_NOME','A2_NREDUZ','A2_TIPO','A2_EST','A2_MUN','A2_END','A2_BAIRRO','A2_CEP','A2_COD_MUN','A2_CODPAIS','A2_CONTA','A2_NATUREZ'].includes(c))
    return 'CANDIDATE_REQUIRED';
  const v=r.valid.trim();
  if(!v || /^(vazio|IIF\(!?EMPTY)/i.test(v)) return 'PROVEN_OPTIONAL';
  return 'CONDITIONAL';
}
function dsrc(r){
  const rel=r.relacao.trim();
  if(rel && !VIRTUAL.has(r.campo)){
    if(rel.includes('GETSXENUM')) return ['SX3_DEFAULT','GETSXENUM("SA2")'];
    if(rel.includes('CTOD')) return ['SX3_DEFAULT','empty date'];
    return ['SX3_DEFAULT',rel.slice(0,40)];
  }
  if(r.campo==='A2_LOJA') return ['OBSERVED_CONVENTION',"'01'"];
  if(r.campo==='A2_CODPAIS') return ['OBSERVED_CONVENTION',"'01058'"];
  if(r.campo==='A2_FILIAL') return ['RUNTIME_RULE','branch context (blank=shared)'];
  if(VIRTUAL.has(r.campo)) return ['RUNTIME_RULE','virtual'];
  return ['NONE','—'];
}
const esc=s=>(s||'').replace(/\|/g,'/').trim()||'—';

const out=[];
out.push('| business_field | business_label | totvs_table | totvs_field | sx3_title | sx3_description | data_type | length | decimals | create_class | default_source | default_value | validation | lookup_table | lookup_key | allowed_values | normalization | sensitivity | company_scope | evidence_status | notes |');
out.push('|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|');
const counts={};
for(const r of ROWS){
  const c=r.campo;
  const bf=SEM[c]||c.toLowerCase();
  const [ds,dv]=dsrc(r);
  const [lt,lk]=LOOKUP[c]||['—','—'];
  const av=r.cbox.trim()?'CBOX':'—';
  const cs=ONLY_0105.has(c)?'01,05':'01,03,04,05';
  const notes=[];
  if(r.obrigat.charAt(0)==='x') notes.push('OBRIGAT flag');
  if(r.propri.trim()==='U') notes.push('DELPI custom');
  if(r.propri.trim()==='S') notes.push('SYS');
  if(VIRTUAL.has(c)) notes.push('virtual (no physical column)');
  if(ACCUM.has(c)) notes.push('system accumulator/screen flag');
  if(r.when.trim()) notes.push('WHEN: '+r.when.trim().slice(0,50));
  const cl=cls(r); counts[cl]=(counts[cl]||0)+1;
  out.push('| '+[bf,esc(r.descr),'SA2010','`'+c+'`',esc(r.titulo),esc(r.descr),
    r.tipo,r.tam.split('.')[0],r.dec.split('.')[0],
    cl,ds,esc(dv),esc(r.valid.slice(0,80)),lt,lk,av,
    normz(r),sens(r),cs,'PROVEN',notes.join('; ')||'—'].join(' | ')+' |');
}
// ---- emit all outputs ----
fs.writeFileSync('scripts/_supplier_audit/.work/full_mapping.md', out.join('\n')+'\n');

const byCampo = Object.fromEntries(ROWS.map(r=>[r.campo,r]));

// REQUIRED_AND_CANDIDATE_FIELDS
const req={PROVEN_REQUIRED:[],CANDIDATE_REQUIRED:[],CONDITIONAL:[],SYSTEM_GENERATED:[],DO_NOT_SEND:[],PROVEN_OPTIONAL:[],UNKNOWN:[]};
for(const r of ROWS) req[cls(r)].push(r.campo);
let reqMd='';
for(const k of ['PROVEN_REQUIRED','CANDIDATE_REQUIRED','CONDITIONAL','SYSTEM_GENERATED','UNKNOWN','DO_NOT_SEND','PROVEN_OPTIONAL']){
  reqMd+=`\n**${k}** (${req[k].length})\n\n`;
  reqMd+=req[k].map(c=>'`'+c+'`').join(' ')+'\n';
}
fs.writeFileSync('scripts/_supplier_audit/.work/required.md',reqMd);

// LOOKUP_MATRIX
let lk='| business_field | totvs_field | lookup_table | lookup_key | validation | notes |\n|---|---|---|---|---|---|\n';
for(const [c,[t,k]] of Object.entries(LOOKUP)){
  const r=byCampo[c]; if(!r) continue;
  lk+=`| ${SEM[c]||c.toLowerCase()} | \`${c}\` | ${t} | ${k} | ${esc(r.valid.slice(0,70))} | ${esc(r.descr)} |\n`;
}
fs.writeFileSync('scripts/_supplier_audit/.work/lookups.md',lk);

// DEFAULTS list (SX3 RELACAO non-empty)
let df='| totvs_field | default_source | default_value | notes |\n|---|---|---|---|\n';
for(const r of ROWS){
  const rel=r.relacao.trim();
  if(!rel && !['A2_LOJA','A2_CODPAIS','A2_FILIAL'].includes(r.campo)) continue;
  const [ds,dv]=dsrc(r);
  df+=`| \`${r.campo}\` | ${ds} | ${esc(dv)} | ${esc(r.descr)} |\n`;
}
fs.writeFileSync('scripts/_supplier_audit/.work/defaults.md',df);

// SYSTEM_OWNED_DO_NOT_SEND
let so='| totvs_field | type | length | reason |\n|---|---|---|---|\n';
for(const r of ROWS){
  if(cls(r)!=='DO_NOT_SEND' && r.campo!=='A2_FILIAL') continue;
  const reason=VIRTUAL.has(r.campo)?'campo virtual sem coluna física — derivado em runtime':
    ACCUM.has(r.campo)?'acumulador estatístico / flag interna mantida pelo Protheus':
    r.campo==='A2_FILIAL'?'contexto de filial — preenchido pelo runtime Protheus':
    'campo técnico de controle interno';
  so+=`| \`${r.campo}\` | ${r.tipo} | ${r.tam.split('.')[0]} | ${reason} |\n`;
}
// technical SQL-level cols (not in SX3)
for(const c of ['D_E_L_E_T_','R_E_C_N_O_','R_E_C_D_E_L_','S_T_A_M_P_','I_N_S_D_T_'])
  so+=`| \`${c}\` | - | - | coluna física de controle Protheus (deleção lógica, RECNO, timestamp) — gerida pelo DBMS/runtime |\n`;
fs.writeFileSync('scripts/_supplier_audit/.work/system.md',so);

// RECOMMENDED mapping grouped
const GROUPS={
 'IDENTITY':['A2_FILIAL','A2_COD','A2_LOJA'],
 'DADOS CADASTRAIS':['A2_NOME','A2_NREDUZ','A2_CGC','A2_TIPO','A2_END','A2_NR_END','A2_BAIRRO','A2_EST','A2_MUN','A2_COD_MUN','A2_CEP','A2_CODPAIS','A2_MSBLQL','A2_ORIGEM','A2_SATIV1','A2_CLIENTE','A2_LOJCLI','A2_NUMRA','A2_TRANSP','A2_GRUPO','A2_VINCULO','A2_CODADM'],
 'ENDEREÇO':['A2_END','A2_NR_END','A2_ENDCOMP','A2_BAIRRO','A2_CEP','A2_MUN','A2_COD_MUN','A2_EST','A2_CODPAIS','A2_PAIS','A2_CX_POST','A2_MUN_ENT'],
 'FISCAL':['A2_INSCR','A2_INSCRM','A2_CONTRIB','A2_SIMPNAC','A2_CNAE','A2_TPJ','A2_TPESSOA','A2_REGESIM','A2_REGPB','A2_NATUREZ','A2_RECINSS','A2_RECISS','A2_RECCSLL','A2_RECCOFI','A2_RECPIS','A2_CALCIRF','A2_CALCINP','A2_GRPTRIB','A2_CATEFD'],
 'CONTATO':['A2_CONTATO','A2_CONTCOM','A2_DDD','A2_TEL','A2_EMAIL','A2_HPAGE','A2_FAX','A2_NOMRESP'],
 'FINANCEIRO':['A2_COND','A2_FORMPAG','A2_NATUREZ','A2_CONTA','A2_LC','A2_RISCO'],
 'BANCÁRIO':['A2_BANCO','A2_AGENCIA','A2_DVAGE','A2_NUMCON','A2_DVCTA','A2_TIPCTA','A2_TPCONTA','A2_CODFAV','A2_LOJFAV','A2_SWIFT'],
 'FLAGS / DELPI':['A2_YROHS','A2_YFGEN','A2_ZTABPRC','A2_MSBLQL'],
};
let rec='';
const seen=new Set();
for(const [g,fields] of Object.entries(GROUPS)){
  rec+=`\n**${g}**\n\n| business_field | totvs_field | type | len | create_class | default | lookup | notes |\n|---|---|---|---|---|---|---|---|\n`;
  for(const c of fields){
    if(seen.has(c)) continue; seen.add(c);
    const r=byCampo[c]; if(!r) continue;
    const [ds,dv]=dsrc(r); const [lt]=LOOKUP[c]||['—'];
    rec+=`| ${SEM[c]||c.toLowerCase()} | \`${c}\` | ${r.tipo} | ${r.tam.split('.')[0]} | ${cls(r)} | ${ds==='NONE'?'—':esc(dv)} | ${lt} | ${r.obrigat.charAt(0)==='x'?'OBRIGAT flag':'—'} |\n`;
  }
}
fs.writeFileSync('scripts/_supplier_audit/.work/recommended.md',rec);
console.log('emitted all parts; recommended fields:',seen.size);
console.log(JSON.stringify(Object.fromEntries(Object.entries(req).map(([k,v])=>[k,v.length]))));
