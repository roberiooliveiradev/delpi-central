#include "rwmake.ch"        // incluido pelo assistente de conversao do AP5 IDE em 25/08/01
#include "colors.ch"        // incluido pelo assistente de conversao do AP5 IDE em 20/04/01
#include "sigawin.ch"
#include "topconn.ch"

User Function DLP014()        // incluido pelo assistente de conversao do AP5 IDE em 25/08/01

/*MSSOLUTION
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Cliente      ³ FARBEN  S/A                                             ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Programa     ³ DLP014           ³ Responsavel ³ MARCIO SILVA           ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Programa De Atualizacao de arquivo SC9-> empenho de pedidos Expedicao ³±±
±±³                                                                       ³±±
±±³                                                                       ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/


tContinua := .T.
While tContinua
      tLerBar  := .f.
      sNumOp   := Space(15)
      sCodCra  := space(6)
      sOperado := Space(10)

      sCodPro  := Space(15)
      sDesPro  := Space(15)
      sCodRec  := Space(6)
      sDesRec  := Space(30)

      dPDatIni  := ctod("  /  /  ")
      dPDatFin  := ctod("  /  /  ")
      sPHorIni  := "  :  "
      sPHorFin  := "  :  "
      sPTempo   := "   :  "

      dRDatIni  := ctod("  /  /  ")
      dRDatFin  := ctod("  /  /  ")
      sRHorIni  := "  :  "
      sRHorFin  := "  :  "
      sRTempo   := "   :  "
      tStart := .F.

      sObsRec   := ""

      oFont := CreatFontw("TIMES NEW ROMAN",10,-15)

      @ 0,0 TO 600,840 DIALOG oDlg1 TITLE "APONTAMENTO DE RECURSOS OP."
      oDlg1:oFont := oFont // se a fonte for colocada na janela todos os controles criados usarao a mesma fonte


      @ 010,020 SAY "OP "                   SIZE 080,10        colors 32896
      @ 010,220 SAY "CRACHA "               SIZE 080,10        colors 32896

      @ 030,020 TO 070,400 TITLE "DADOS DO APONTAMENTO A SER EXECUTADO"
      @ 040,030 SAY "Produto "              SIZE 080,10        colors 8388608
      @ 055,030 SAY "Recurso "              SIZE 080,10        colors 8388608                    //colors 8388608

      @ 080,020 TO 140,400 TITLE "TEMPO PREVISTO"
      @ 090,030 SAY "Data Inicial "         SIZE 080,40        colors 8388608
      @ 090,220 SAY "Hora Inicial "         SIZE 080,40        colors 8388608
      @ 105,030 SAY "Data Final "           SIZE 080,40        colors 8388608
      @ 105,220 SAY "Hora Final "           SIZE 080,40        colors 8388608
      @ 120,030 SAY "Tempo "                SIZE 080,40        colors 8388608


      @ 150,020 TO 210,400 TITLE "TEMPO REALIZADO"
      @ 160,030 SAY "Data Inicial "         SIZE 080,40        colors 8388608
      @ 160,220 SAY "Hora Inicial "         SIZE 080,40        colors 8388608
      @ 175,030 SAY "Data Final "           SIZE 080,40        colors 8388608
      @ 175,220 SAY "Hora Final "           SIZE 080,40        colors 8388608
      @ 190,030 SAY "Tempo "                SIZE 080,40        colors 8388608

      @ 220,020 TO 255,400 TITLE "OBS. PROCESSO"

      @ 010,100 GET sNumOp     VALID fNumOP()                             SIZE 100,40
      @ 010,300 GET sCodCra    Valid fCodCra()  picture "@!"  PASSWORD    SIZE 090,40

      @ 235,030 Get sObsRec    when .F.    SIZE 360,60   Object oAtualizar

      @ 040,100 GET sCodPro    when .F.    SIZE 100,40                      Object oAtualizar
      @ 040,220 GET sDesPro    when .F.    SIZE 170,40                      Object oAtualizar
      @ 055,100 GET sCodRec    when .F.    SIZE 100,40                      Object oAtualizar
      @ 055,220 GET sDesRec    when .F.    SIZE 170,40                      Object oAtualizar

      @ 090,100 GET dPDatIni    PICTURE "99/99/99"  when .F.    SIZE 070,40 Object oAtualizar
      @ 090,300 GET sPHorIni    PICTURE "99:99"     when .F.    SIZE 040,40 Object oAtualizar
      @ 105,100 GET dPDatFin    PICTURE "99/99/99"  when .F.    SIZE 070,40 Object oAtualizar
      @ 105,300 GET sPHorFin    PICTURE "99:99"     when .F.    SIZE 040,40 Object oAtualizar
      @ 120,100 GET sPTempo     PICTURE "999:99"    when .F.    SIZE 070,40 Object oAtualizar
                            	
      @ 160,100 GET dRDatIni    PICTURE "99/99/99"  when .F.    SIZE 070,40 Object oAtualizar
      @ 160,300 GET sRHorIni    PICTURE "99:99"     when .F.    SIZE 040,40 Object oAtualizar
      @ 175,100 GET dRDatFin    PICTURE "99/99/99"  when .F.    SIZE 070,40 Object oAtualizar
      @ 175,300 GET sRHorFin    PICTURE "99:99"     when .F.    SIZE 040,40 Object oAtualizar
      @ 190,100 GET sRTempo     PICTURE "999:99"    when .F.    SIZE 070,40 Object oAtualizar

      @ 265,050 BUTTON "_OK"      SIZE 100,30 ACTION fOkApontamento()
      @ 265,250 BUTTON "_CANCELA" SIZE 100,30 ACTION fSair()

      ACTIVATE DIALOG oDlg1 CENTER
End
Return

*************************
Static Function fCodCra()
***************
If Empty(sCodCra)
   Return(.T.)
EndIf
DbSelectArea("SRA")
DbSetOrder(9)
DbSeek(Alltrim(sCodCra),.T.)
If !Alltrim(sCodCra) == Alltrim(SRA->RA_CRACHA) //.Or. !Empty(SRA->RA_DEMISSA)
   Msgbox('Funcionario Nao Cadastrado, ou Nao Autorizado!')
   Return (.F.)
EndIf
sOperado := Left(SRA->RA_NOME,10)
Return (.T.)

********************************
Static Function fSair()
***************
tContinua := .F.
Close(oDlg1)
Return

********************************
Static Function fOkApontamento()
***************
If Empty(sNumOp)
   Msgbox("Op Nao Cadastrada!")
   Return
EndIf
If Empty(sCodCra)
   Msgbox("Funcionario Nao Cadastrado!")
   Return
EndIf
iF sRTempo == '000:00'
   Msgbox("Tempo Realizado nao e maior que 000:00!")
   Return
EndIf
DbSelectArea("SH8")
DbSetOrder(1)
dbseek(xfilial('SH8')+SC2->C2_NUM+SC2->C2_ITEM+SC2->C2_SEQUEN,.T.)
While xfilial('SH8')+Alltrim(SC2->C2_NUM+SC2->C2_ITEM+SC2->C2_SEQUEN) == SH8->H8_FILIAL + Alltrim(SH8->H8_OP)
      nRecno:=RECNO()
      If SH8->H8_RECURSO == sCodRec
         If tStart
            RecLock("SH8",.F.)
            SH8->H8_DTINIOP := dRDatIni
            SH8->H8_HRINIOP := sRHorIni
            MsUnlock("SH8")
         Else        
           aVetor := {}
           lMsErroAuto := .F.
           aVetor := { {"H6_OP"      ,SH8->H8_OP       ,NIL},;
                       {"H6_PRODUTO" ,SC2->C2_PRODUTO  ,NIL},;
                       {"H6_OPERAC"  ,SH8->H8_OPER     ,NIL},;
                       {"H6_OPERADO" ,sCodCra          ,NIL},;
                       {"H6_RECURSO" ,SH8->H8_RECURSO  ,NIL},;
                       {"H6_DATAINI" ,SH8->H8_DTINIOP  ,NIL},;
                       {"H6_HORAINI" ,SH8->H8_HRINIOP  ,NIL},;
                       {"H6_DATAFIN" ,dRDatFin         ,NIL},;
                       {"H6_HORAFIN" ,sRHorFin         ,NIL},;
                       {"H6_TEMPO"   ,sRTempo          ,NIL},;
                       {"H6_QTDPROD" ,SH8->H8_QUANT    ,NIL},;
                       {"H6_QTDPERD" ,0                ,NIL},;
                       {"H6_HT"      ,"T"              ,NIL},;
                       {"H6_PT"      ,"T"              ,NIL},;
                       {"H6_DTAPONT" ,dDataBase        ,NIL}}
           MSExecAuto({|x| mata680(x)},aVetor,3)
           If lMsErroAuto
             Mostraerro()
             Disarmtransaction()
             break
           Endif
         EndIf
      EndIf
      DbSelectArea("SH8")
      DBGOTO(nRecno)
      DbSkip()
EndDo
tContinua := .F.
Close(oDlg1)
Return


************************
Static Function fNumOP()
***************
       If Empty(sNumOp)
          Return(.T.)
       EndIf
       DbSelectArea("SC2")
       DbSetOrder(1)
       dbseek(xfilial('SC2')+Alltrim(sNumOP),.T.)
       If !xfilial('SC2')+Alltrim(sNumOP) == SC2->C2_FILIAL+Alltrim(SC2->C2_NUM+SC2->C2_ITEM+SC2->C2_SEQUEN)
          Msgbox('Op Invalida!')
          Close(oDlg1)
          Return(.F.)
       EndIf

       tLaco:= .T.
       tSh8 := .F.
       sErro := ''
       sRecurso := ''
       DbSelectArea("SH8")
       DbSetOrder(1)
       dbseek(xfilial('SH8')+SC2->C2_NUM+SC2->C2_ITEM+SC2->C2_SEQUEN,.T.)
       While xfilial('SH8')+Alltrim(SC2->C2_NUM+SC2->C2_ITEM+SC2->C2_SEQUEN) == SH8->H8_FILIAL + Alltrim(SH8->H8_OP) .And. tLaco
             tSh8 := .T.
             If Empty(SH8->H8_STATUS)
                sErro := 'Op, Nao Sacramentada! - Chamar PCP'
                tLaco := .F.
                Loop
             EndIf
             iF Empty(dPDatIni)
                DbSelectArea("SH6")
                DbSetOrder(1)
                dbseek(xfilial('SH6')+SH8->H8_OP+SC2->C2_PRODUTO+SH8->H8_OPER,.T.)
                If !xfilial('SH6')+SH8->H8_OP+SC2->C2_PRODUTO+SH8->H8_OPER == SH6->H6_FILIAL+SH6->H6_OP+SH6->H6_PRODUTO+SH6->H6_OPERAC
                   dPDatIni := SH8->H8_DTINI
                   sPHorIni := SH8->H8_HRINI
                   sCodRec  := SH8->H8_RECURSO
                EndIf
             EndIf
             iF !Empty(dPDatIni)
                iF !Empty(sCodRec)
                   If SH8->H8_RECURSO == sCodRec
                      If Empty(SH8->H8_DTINIOP)
                         iF Empty(dPDatFin)
                            dRDatIni  := dDataBase
                            sRHorIni  := SubStr(Time(),1,5)
                            tStart := .T.
                         EndIf
                      Else
                         If Empty(dRDatIni)
                            dRDatIni  := SH8->H8_DTINIOP
                            sRHorIni  := SH8->H8_HRINIOP
                            dRDatFin  := dDataBase
                            sRHorFin  := SubStr(Time(),1,5)
                            sRTempo   := U_fDifTempo(dTos(dRDatIni),sRHorIni,dTos(dRDatFin),sRHorFin) // Retorna Diferenca de Tempo
//                            iF Len(Alltrim(SC2->C2_PRODUTO)) > 7
//                               sErro := 'Nao Pode Ser Finalizada OP, Neste Programa'
//                            EndIf
                         EndIf
                      EndIf
                      dPDatFin := SH8->H8_DTINI
                      sPHorFin := SH8->H8_HRFIM
                      sPTempo  := ''
                   Else
                      tLaco := .F.
                      Loop
                   EndIf
                EndIf
             EndIf
             DbSelectArea("SH8")
             DbSkip()
       EndDo
       iF !tSh8
          sErro := 'Carga Maquina Nao Gerada!'
       EndIf
       iF Empty(dPDatIni) .And. Empty(sErro)
          sErro := 'Op Ja Finalizada!'
       EndIf
       iF !Empty(sErro)
          Msgbox(sErro)
          Close(oDlg1)
          Return(.F.)
       Else
//          If Empty(sRecurso)
//             Msgbox("OP, com todos os recursos apontados.")
//             Close(oDlg1)
//             Return(.F.)
//          EndIf
          If tStart
             sObsRec := "Apontamento de Inicializacao de processo Em Recurso"
          Else
             sObsRec := "Apontamento de Finalizacao de processo Em Recurso"
          	 sPTempo := U_fDifTempo(dTos(dPDatIni),sPHorIni,dTos(dPDatFin),sPHorFin) // Retorna Diferenca de Tempo
          EndIf

          DbSelectArea("SB1")
          DbSetOrder(1)
          IF (DbSeek(xFilial('SB1')+SC2->C2_PRODUTO))
             sCodPro := SC2->C2_PRODUTO
             sDesPro := SB1->B1_DESC
          EndIf
          DbSelectArea("SH1")
          DbSetOrder(1)
          IF (DbSeek(xFilial('SH1')+sCodRec))
             sDesRec := SH1->H1_DESCRI
          EndIf
          ObjectMethod(oAtualizar,"Refresh()")
       EndIf
Return(.T.)           
//Positivo() .And. A680Quant() .And. DigiPerda(M->H6_PRODUTO,M->H6_OP,M->H6_QTDPERD)                                              