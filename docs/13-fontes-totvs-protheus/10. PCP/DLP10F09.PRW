#INCLUDE "protheus.ch"
#INCLUDE "TopConn.ch"

//---------------------------------------------------------------------
// DLP10F09 - Impressao de etiqueta de apontamento de producao (Delpi)
//
// Base: YUD04R01 (YUDO) / padrao MSCBPRINTER.
//
// Roteamento fixo por filial (hardcoded, LPT mapeada no servidor):
//   Filial 01 -> LPT1  (\\srv-protheus01\Zebra_ZT231_SC)
//   Filial 02 -> LPT2  (\\srv-protheus01\ZT231-UES)
//
// Pre-requisito no servidor Protheus (srv-protheus01 / 192.168.1.231),
// com o usuario que executa o AppServer:
//   net use LPT1 \\srv-protheus01\Zebra_ZT231_SC /persistent:yes
//   net use LPT2 \\srv-protheus01\ZT231-UES     /persistent:yes
// O MV_ZDIMPOP guarda o nome do share e e lido apenas para log.
//
// Obs: o MSCBPRINTER so homologa portas COM e LPT. Os parametros
// nPorta/cServer/cEnv se referem a outro AppServer remoto (nao ao IP
// da impressora); tentar TCP direto (9100) retorna "falha na abertura
// da porta". IPs das Zebras, para referencia futura:
//   Filial 01 -> 192.168.1.195:9100
//   Filial 02 -> 192.168.4.240:9100
//---------------------------------------------------------------------
User Function DLP10F09(cPrdPA,cPrdApont,cOPApont,cTpApon,cDescAp,nQtd,;
                      cCDRec,sDesRec,cCDUsr,dDtApont,cHrApont,nQtdTOP,;
                      cDsCT1,cDsCT2,cDsCT3)

    DEFAULT cDsCT1 := ""
    DEFAULT cDsCT2 := ""
    DEFAULT cDsCT3 := ""

    ImpEtiq(cPrdPA,cPrdApont,cOPApont,cTpApon,cDescAp,nQtd,cCDRec,;
            sDesRec,cCDUsr,dDtApont,cHrApont,nQtdTOP,cDsCT1,cDsCT2,cDsCT3)

Return

Static Function ImpEtiq(cPrdPA,cPrdApont,cOPApont,cTpApon,cDescAp,nQtd,;
                        cCDRec,sDesRec,cCDUsr,dDtApont,cHrApont,nQtdTOP,;
                        cDsCT1,cDsCT2,cDsCT3)

    Local cModelo  := "ZEBRA"
    Local cPorta   := IIf(cFilAnt == "01", "LPT1", "LPT2")
    Local cImpress := ""
    Local cQtdTOP  := ""
    Local lSrv     := .T.    // LPT mapeada no servidor (net use LPTx)
    Local lDrvWin  := .F.    // comandos ZPL diretos (nao usa driver Windows)
    Local nLin     := 0

    // Log do compartilhamento cadastrado no MV (diagnostico)
    cImpress := AllTrim(SuperGetMV("MV_ZDIMPOP",.F.,""))
    conout("DLP10F09 fil=" + cFilAnt + " porta=" + cPorta + ;
           " share=" + cImpress + " OP=" + AllTrim(cOPApont))

    // Remapeia a LPT antes de cada impressao. A conexao SMB do share cai
    // por inatividade e, quando isso acontece, MSCBPRINTER trava com erro
    // de acesso a porta. Refazer o net use a cada job evita esse cenario.
    If !Empty(cImpress)
        conout("DLP10F09 remap " + cPorta + " -> " + cImpress)
        WaitRunSrv('cmd.exe /c net use ' + cPorta + ' /delete /yes', .T., "C:\Users\totvs01")
        WaitRunSrv('cmd.exe /c net use ' + cPorta + ' "' + cImpress + '" /persistent:yes', .T., "C:\Users\totvs01")
    Else
        conout("DLP10F09 AVISO: MV_ZDIMPOP vazio para filial " + cFilAnt + " - sem remap")
    EndIf

    cQtdTOP := CValToChar(nQtdTOP * 1000)

    // Abertura da impressora - ZEBRA via LPT mapeada no servidor Protheus
    // MSCBPRINTER(cModelo, cPorta, nDensidade, nTamanho, lSrv, nPorta, cServer, cEnv, nMemoria, cFila, lDrvWin, cPathSpool)
    MSCBPRINTER(cModelo, cPorta, , , lSrv, , , , , , lDrvWin, )
    // Tentativa TCP direto (retorna "falha na abertura da porta" - nao homologado):
    // MSCBPRINTER(cModelo, "", , , .F., 9100, IIf(cFilAnt=="01","192.168.1.195","192.168.4.240"), , , , .F., )
    MSCBCHKSTATUS(.F.)

    // Inicio da etiqueta (1 etiqueta por chamada, gap 1mm)
    MSCBBEGIN(1, 1)

    cZpl := BuildZPL(cPrdPA, cPrdApont, cOPApont, cTpApon, cDescAp, nQtd,;
                      sDesRec, cCDUsr, dDtApont, cHrApont, nQtdTOP,;
                      cDsCT1, cDsCT2, cDsCT3)

    MSCBWRITE(cZpl)

    // Finaliza e envia o job a impressora
    MSCBEND()
    MSCBCLOSEPRINTER()

Return

//---------------------------------------------------------------------
// Monta a string ZPL II da etiqueta 90x50mm.
// Medidas em dots; 8 dots/mm -> 720 x 400 dots.
// Fonte escalavel A0 em alturas variadas; CODE128 com texto embaixo.
//---------------------------------------------------------------------
Static Function BuildZPL(cPrdPA, cPrdApont, cOPApont, cTpApon, cDescAp, nQtd,;
                         sDesRec, cCDUsr, dDtApont, cHrApont, nQtdTOP,;
                         cDsCT1, cDsCT2, cDsCT3)

    Local cZPL     := ""
    Local cCR      := Chr(13) + Chr(10)
    Local cQtdTOP  := AllTrim(Transform(nQtdTOP * 1000, "@E 999,999,999"))
    Local cQtdAPT  := AllTrim(Transform(nQtd,           "@E 999,999,999"))
    Local cDesc    := AllTrim(cDescAp)
    Local cCTs     := ""

    // Concatena os 3 centros de trabalho (ignora vazios)
    If !Empty(cDsCT1)
        cCTs := AllTrim(cDsCT1)
    EndIf
    If !Empty(cDsCT2)
        cCTs += IIf(Empty(cCTs), "", " / ") + AllTrim(cDsCT2)
    EndIf
    If !Empty(cDsCT3)
        cCTs += IIf(Empty(cCTs), "", " / ") + AllTrim(cDsCT3)
    EndIf

    // Cabecalho ZPL
    cZPL := "^XA" + cCR
    cZPL += "^CI27" + cCR               // code page Windows-1252 (acentos)
    cZPL += "^PW720" + cCR              // largura 720 dots (~90mm)
    cZPL += "^LL400" + cCR              // altura  400 dots (~50mm)
    cZPL += "^LH100,0" + cCR            // desloca o origem 100 dots a direita (ajuste fino do offset fisico)
    cZPL += "^LS0" + cCR                // sem shift horizontal
    cZPL += "^PR4" + cCR                // velocidade (4ips, ajustar se precisar)

    // Topo esquerdo - codigo do PA em destaque
    cZPL += "^FO0,15^A0N,55,55^FD"      + AllTrim(cPrdPA) + "^FS" + cCR

    // Topo direito - QTD OP e QTD APT
    cZPL += "^FO370,15^A0N,30,30^FDQTD OP "  + cQtdTOP + "^FS" + cCR
    cZPL += "^FO370,55^A0N,30,30^FDQTD APT: " + cQtdAPT + "^FS" + cCR

    // Codigo de barras CODE128 do numero da OP (com interpretacao embaixo)
    cZPL += "^BY2,2,70" + cCR
    cZPL += "^FO0,100^BCN,70,Y,N,N^FD"   + AllTrim(cOPApont) + "^FS" + cCR

    // Tipo:Apontado (logo abaixo do barcode, ao lado do numero da OP interpretado)
    cZPL += "^FO0,210^A0N,24,24^FD"      + AllTrim(cTpApon) + ": " + AllTrim(cPrdApont) + "^FS" + cCR

    // Descricao, Operacao, CTs
    cZPL += "^FO0,245^A0N,22,22^FDDescricao: " + SubStr(cDesc, 1, 60) + "^FS" + cCR
    cZPL += "^FO0,275^A0N,22,22^FDOperacao: "  + AllTrim(sDesRec)     + "^FS" + cCR

    If !Empty(cCTs)
        cZPL += "^FO0,305^A0N,22,22^FD" + cCTs + "^FS" + cCR
    EndIf

    // Data / Hora / Operador
    cZPL += "^FO0,335^A0N,22,22^FDData: " + DToC(dDtApont) + "  Hora: " + AllTrim(cHrApont) + "^FS" + cCR
    cZPL += "^FO0,365^A0N,22,22^FDOperador: " + AllTrim(cCDUsr) + "^FS" + cCR

    cZPL += "^XZ" + cCR

Return cZPL
