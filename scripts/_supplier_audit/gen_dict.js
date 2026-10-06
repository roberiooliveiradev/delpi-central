#!/usr/bin/env node
// Generates PUBLIC_DICTIONARY rows for cadastro-fornecedor.md from SX3 dump.
const fs=require('fs');
const raw=fs.readFileSync('scripts/_supplier_audit/.work/sa2_full.txt','latin1').split(/\r?\n/);
const R={};
for(const line of raw){
  const pr=line.split('|'); const p=pr.map(c=>c.trim());
  if(p.length<17||!p[1]||!p[1].startsWith('A2_'))continue;
  R[p[1]]={campo:p[1],tipo:p[2],tam:p[3].split('.')[0],dec:p[4].split('.')[0],
    titulo:p[5],descr:p[6],valid:p[8],relacao:p[9],f3:p[10],cbox:p[11],when:p[12],
    obrigat:pr[13],propri:p[14]};
}
// [totvs, minha_delpi_field, label_pt_br, business_description, naming_status, note_extra]
const D=[
['A2_FILIAL','branch','Filial','Filial do registro no Protheus (branco = compartilhado, MODO=C).','NEW_CANONICAL','system — não enviar'],
['A2_COD','supplier_code','Código','Código do fornecedor; gerado por GETSXENUM("SA2") nas empresas 01/05.','REUSED_PROVEN','totvs_supplier_repository.py'],
['A2_LOJA','supplier_store','Loja','Loja do fornecedor; compõe a identidade junto de supplier_code.','REUSED_PROVEN','padding inconsistente — normalizar'],
['A2_NOME','supplier_name','Razão social','Razão social do fornecedor.','REUSED_PROVEN',''],
['A2_NREDUZ','supplier_short_name','Nome fantasia','Nome reduzido/fantasia. Conflito: safety_stock_sql usa trade_name para o mesmo campo.','REUSED_PROVEN','LEGACY_CONFLICT: trade_name'],
['A2_CGC','tax_id','CNPJ/CPF','CNPJ ou CPF do fornecedor (SX3 diz "do cliente" — metadata TOTVS incorreta preservada em sx3_description).','REUSED_PROVEN','não é chave; sinal de duplicidade'],
['A2_TIPO','person_type','Tipo de pessoa','F= física, J= jurídica, X= exterior/outros.','NEW_CANONICAL','CBOX/enum'],
['A2_END','address','Endereço','Logradouro.','NEW_CANONICAL',''],
['A2_NR_END','address_number','Número','Número do endereço (0% de uso observado).','NEW_CANONICAL',''],
['A2_ENDCOMP','address_complement','Complemento','Complemento do endereço. Conflito de campo: A2_ENDCOMP × A2_COMPLEM.','NEEDS_REVIEW','par ENDCOMP/COMPLEM'],
['A2_BAIRRO','district','Bairro','Bairro.','NEW_CANONICAL',''],
['A2_CEP','postal_code','CEP','Código postal (dígitos).','NEW_CANONICAL',''],
['A2_MUN','city','Município','Nome do município.','NEW_CANONICAL',''],
['A2_COD_MUN','city_code','Código do município','Código do município (CC2, por UF).','NEW_CANONICAL','OBRIGAT flag'],
['A2_EST','state','UF','Unidade federativa; EX=exterior.','REUSED_PROVEN','lookup SX5-12'],
['A2_PAIS','country_code','País','Código do país (SYA) — usado para estrangeiros.','NEW_CANONICAL',''],
['A2_CODPAIS','bacen_country_code','País BACEN','Código BACEN do país (CCH); 01058=Brasil observado em 100%.','NEW_CANONICAL','OBRIGAT flag; OBSERVED_CONVENTION'],
['A2_CX_POST','po_box','Caixa postal','Caixa postal.','NEW_CANONICAL',''],
['A2_INSCR','state_registration','Inscrição estadual','Inscrição estadual (IE() por UF).','NEW_CANONICAL','WHEN condicional'],
['A2_INSCRM','municipal_registration','Inscrição municipal','Inscrição municipal.','NEW_CANONICAL',''],
['A2_CONTRIB','icms_contributor','Contribuinte ICMS','Indicador de contribuinte (CBOX 1/2).','NEW_CANONICAL',''],
['A2_SIMPNAC','simples_nacional','Simples Nacional','Indicador Simples Nacional.','NEW_CANONICAL',''],
['A2_CNAE','cnae_code','CNAE','Código CNAE (WHEN TIPO J/X).','NEW_CANONICAL',''],
['A2_TPJ','legal_entity_type','Tipo jurídico','Tipo de pessoa jurídica.','NEEDS_REVIEW','semântica SX3 ampla'],
['A2_TPESSOA','person_category','Categoria de pessoa','Categoria de pessoa (99,9% vazio).','NEEDS_REVIEW',''],
['A2_REGESIM','simp_regime_code','Regime SIMP','Regime tributário SIMP.','NEEDS_REVIEW','default SX3 "2"'],
['A2_REGPB','pb_regime_code','Regime PB','Regime PB.','NEEDS_REVIEW',''],
['A2_NATUREZ','financial_nature_code','Natureza financeira','Natureza financeira (lookup SED).','NEW_CANONICAL','OBRIGAT flag; RESTRICTED update'],
['A2_RECINSS','inss_withholding','Retenção INSS','Flag de retenção INSS.','NEW_CANONICAL','default SX3'],
['A2_RECISS','iss_withholding','Retenção ISS','Flag de retenção ISS.','NEW_CANONICAL',''],
['A2_RECCSLL','csll_withholding','Retenção CSLL','Flag de retenção CSLL.','NEW_CANONICAL','default SX3 "1"'],
['A2_RECCOFI','cofins_withholding','Retenção COFINS','Flag de retenção COFINS.','NEW_CANONICAL','default SX3 "1"'],
['A2_RECPIS','pis_withholding','Retenção PIS','Flag de retenção PIS.','NEW_CANONICAL','default SX3 "1"'],
['A2_CALCIRF','irf_calculation','Calcula IRRF','Flag de cálculo IRRF.','NEW_CANONICAL',''],
['A2_CALCINP','inp_calculation','Calcula INSS','Flag de cálculo INSS patronal.','NEW_CANONICAL',''],
['A2_GRPTRIB','tax_group_code','Grupo tributário','Grupo de tributação.','NEW_CANONICAL',''],
['A2_CATEFD','esocial_category_code','Categoria eSocial','Categoria eSocial (S049BR).','NEW_CANONICAL',''],
['A2_CONTATO','contact_name','Contato','Pessoa de contato.','REUSED_PROVEN','OBRIGAT flag'],
['A2_CONTCOM','commercial_contact_name','Contato comercial','Contato comercial.','NEW_CANONICAL',''],
['A2_DDD','area_code','DDD','Código de área.','REUSED_PROVEN','46 ocorrências em código'],
['A2_DDI','country_calling_code','DDI','Código de país para chamadas (ACJ).','NEW_CANONICAL',''],
['A2_TEL','phone','Telefone','Telefone (dígitos).','NEW_CANONICAL','OBRIGAT flag'],
['A2_FAX','fax','Fax','Fax.','NEW_CANONICAL',''],
['A2_EMAIL','email','E-mail','E-mail (lowercase).','REUSED_PROVEN','OBRIGAT flag'],
['A2_HPAGE','website','Site','Home-page.','REUSED_PROVEN',''],
['A2_NOMRESP','responsible_name','Responsável','Nome do responsável.','NEW_CANONICAL',''],
['A2_COND','payment_condition_code','Condição de pagamento','Condição de pagamento (SE4).','NEW_CANONICAL',''],
['A2_FORMPAG','payment_method_code','Forma de pagamento','Forma de pagamento (SX5-58).','NEW_CANONICAL','OBRIGAT flag'],
['A2_CONTA','accounting_account','Conta contábil','Conta contábil (CT1).','REUSED_PROVEN','OBRIGAT flag; RESTRICTED'],
['A2_LC','credit_limit_amount','Limite de crédito','Limite de crédito (acumulador estatístico).','NEEDS_REVIEW','provável DO_NOT_SEND'],
['A2_RISCO','risk_code','Risco','Código de risco.','NEW_CANONICAL',''],
['A2_BANCO','bank_code','Banco','Código do banco (SA6).','NEW_CANONICAL','sensível'],
['A2_AGENCIA','bank_branch','Agência','Agência bancária (SA6).','NEW_CANONICAL','sensível'],
['A2_DVAGE','bank_branch_digit','DV agência','Dígito verificador da agência.','NEW_CANONICAL','sensível'],
['A2_NUMCON','bank_account','Conta bancária','Número da conta (SA6).','NEW_CANONICAL','sensível'],
['A2_DVCTA','bank_account_digit','DV conta','Dígito verificador da conta.','NEW_CANONICAL','sensível'],
['A2_TIPCTA','bank_account_type','Tipo de conta','Tipo de conta (CBOX). Conflito: A2_TIPCTA × A2_TPCONTA.','NEEDS_REVIEW','par TIPCTA/TPCONTA'],
['A2_SWIFT','swift_code','SWIFT','Código SWIFT (exterior).','NEW_CANONICAL','uppercase'],
['A2_CODFAV','payee_code','Favorecido','Código do favorecido de pagamento (self-SA2).','NEW_CANONICAL',''],
['A2_LOJFAV','payee_store','Loja favorecido','Loja do favorecido.','NEW_CANONICAL',''],
['A2_MSBLQL','blocked','Bloqueado','Flag de bloqueio (1=bloqueado, 2=ativo; ~4% vazio).','REUSED_PROVEN','SYSTEM_GENERATED; RESTRICTED'],
['A2_YROHS','rohs_indicator','RoHS','Indicador RoHS DELPI (só 01/05).','NEW_CANONICAL','OBRIGAT flag; DELPI'],
['A2_YFGEN','generic_supplier','Fornecedor genérico','Flag de fornecedor genérico DELPI (só 01/05).','NEW_CANONICAL','DELPI'],
['A2_ZTABPRC','purchase_price_table_code','Tabela de preço','Tabela de preço de compra (AIA).','NEW_CANONICAL','DELPI'],
['A2_TRANSP','carrier_code','Transportadora','Transportadora padrão (SA4).','REUSED_PROVEN',''],
['A2_GRUPO','group_code','Grupo','Código de grupo — 0% povoado; grupos reais em SAD.','NEEDS_REVIEW','não povoado; ver SAD'],
['A2_SATIV1','segment_code','Segmento','Segmento de atividade (SX5-T3).','NEW_CANONICAL',''],
['A2_VINCULO','link_type_code','Vínculo','Tipo de vínculo (CC1).','NEW_CANONICAL',''],
['A2_CODADM','administrator_code','Administrador','Código do administrador (SAE).','NEW_CANONICAL',''],
['A2_CLIENTE','linked_customer_code','Cliente vinculado','Cliente vinculado ao fornecedor (SA1; par com loja).','NEW_CANONICAL',''],
['A2_LOJCLI','linked_customer_store','Loja do cliente','Loja do cliente vinculado.','NEW_CANONICAL',''],
['A2_NUMRA','linked_employee_code','Funcionário vinculado','Funcionário vinculado (SRA).','NEW_CANONICAL',''],
];
const LOOKUP={A2_EST:'SX5-12',A2_COD_MUN:'CC2',A2_CODPAIS:'CCH',A2_PAIS:'SYA',A2_COND:'SE4',A2_NATUREZ:'SED',A2_BANCO:'SA6',A2_CONTA:'CT1',A2_FORMPAG:'SX5-58',A2_TRANSP:'SA4',A2_GRUPO:'SX5-Y7',A2_SATIV1:'SX5-T3',A2_CLIENTE:'SA1',A2_LOJCLI:'SA1',A2_NUMRA:'SRA',A2_CODADM:'SAE',A2_DDI:'ACJ',A2_ZTABPRC:'AIA',A2_VINCULO:'CC1',A2_CATEFD:'S049BR',A2_CODFAV:'SA2',A2_TIPCTA:'CBOX'};
const ONLY_0105=new Set(['A2_YROHS','A2_YFGEN']);
const CLSC={A2_FILIAL:'SYSTEM_GENERATED',A2_COD:'SYSTEM_GENERATED',A2_LOJA:'UNKNOWN',A2_MSBLQL:'SYSTEM_GENERATED',A2_LC:'DO_NOT_SEND'};
function cl(c,r){if(CLSC[c])return CLSC[c];if(r.when.trim())return 'CONDITIONAL';if(r.obrigat.charAt(0)==='x')return 'CANDIDATE_REQUIRED';if(['A2_NOME','A2_NREDUZ','A2_TIPO','A2_EST','A2_MUN','A2_END','A2_BAIRRO','A2_CEP','A2_COD_MUN','A2_CODPAIS','A2_CONTA','A2_NATUREZ'].includes(c))return 'CANDIDATE_REQUIRED';return 'PROVEN_OPTIONAL';}
function ds(c,r){const rel=r.relacao.trim();if(rel&&c!=='A2_FILIAL'){if(rel.includes('GETSXENUM'))return['SX3_DEFAULT','GETSXENUM("SA2")'];return['SX3_DEFAULT',rel.slice(0,30)];}
 if(c==='A2_LOJA')return['OBSERVED_CONVENTION',"'01'"];if(c==='A2_CODPAIS')return['OBSERVED_CONVENTION',"'01058'"];if(c==='A2_FILIAL')return['RUNTIME_RULE','blank=shared'];return['NONE','—'];}
const esc=s=>(s||'').replace(/\|/g,'/').trim()||'—';
let out='| minha_delpi_field | label_pt_br | business_description | totvs_alias | totvs_table | totvs_field | data_type | length | decimals | create_class | default_source | default_value | validation | lookup | normalization | company_scope | naming_status | evidence_status | notes |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n';
const stats={};
for(const[c,name,label,bd,ns,extra]of D){
 const r=R[c]; if(!r){console.error('MISSING',c);continue;}
 const[d,v]=ds(c,r);const lk=LOOKUP[c]||'—';
 const norm=[];if(['A2_COD','A2_LOJA'].includes(c))norm.push('RTRIM+zfill');
 if(['A2_CGC','A2_CEP','A2_TEL','A2_DDD','A2_FAX','A2_INSCR','A2_INSCRM','A2_NR_END'].includes(c))norm.push('digits-only');
 if(['A2_EST','A2_SWIFT'].includes(c))norm.push('uppercase');if(c==='A2_EMAIL')norm.push('lowercase');
 stats[ns]=(stats[ns]||0)+1;
 out+=`| ${name} | ${label} | ${bd} | SA2 | SA2010 | \`${c}\` | ${r.tipo} | ${r.tam} | ${r.dec} | ${cl(c,r)} | ${d} | ${esc(v)} | ${esc(r.valid.slice(0,50))} | ${lk} | ${norm.join(';')||'—'} | ${ONLY_0105.has(c)?'01,05':'01,03,04,05'} | ${ns} | PROVEN | ${esc([r.titulo,r.descr].filter((v,i,a)=>v).join(' / ').slice(0,40)+'|'+extra)} |\n`;
}
fs.writeFileSync('scripts/_supplier_audit/.work/dictionary.md',out);
console.log('rows:',Object.keys(D).length,'stats:',JSON.stringify(stats));

// slim handoff table
let h='| campo Minha DELPI | label | campo TOTVS | tabela | tipo | tam | obrigatoriedade | default | validação/lookup | observação |\n|---|---|---|---|---|---|---|---|---|---|\n';
for(const[c,name,label,bd,ns,extra]of D){
 const r=R[c]; if(!r)continue;
 const[d,v]=ds(c,r);const lk=LOOKUP[c]||'—';
 h+=`| ${name} | ${label} | \`${c}\` | SA2010 | ${r.tipo} | ${r.tam} | ${cl(c,r)} | ${d==='NONE'?'—':esc(v)} | ${esc(r.valid.slice(0,40))}${lk!=='—'?' / '+lk:''} | ${esc(extra)} |\n`;
}
fs.writeFileSync('scripts/_supplier_audit/.work/handoff.md',h);
console.log('handoff rows:',D.filter(x=>R[x[0]]).length);
