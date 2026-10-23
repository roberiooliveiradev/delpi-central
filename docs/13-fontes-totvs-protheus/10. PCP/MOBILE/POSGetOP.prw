#INCLUDE "TOTVS.CH"

User Function POSGetOP()
    Local aItemsOP  := PARAMIXB[1]
    Local cForm     := PARAMIXB[2]
    Local nIndItem  := 0
    Local nLenArr   := Len(aItemsOP)
    nTmpPad :=0

    For nIndItem := 1 To nLenArr
        cCDPA      := ""

        dbSelectArea("SC2")
        SC2->(dbSetOrder(1))
        If   SC2->(dBSeek(xFilial("SC2")+SUBSTR(aItemsOP[nIndItem]["ProductionOrderNumber"],1,6)))
            cCDPA      := SC2->C2_PRODUTO
        endif
        dbSelectArea("SC2")
        SC2->(dbSetOrder(1))
        If   SC2->(dBSeek(xFilial("SC2")+aItemsOP[nIndItem]["ProductionOrderNumber"]))
            cCDRot      := SC2->C2_ROTEIRO
        endif

        dbSelectArea("SG2")

        SG2->(dbSetOrder(1))//G2_FILIAL, G2_PRODUTO, G2_CODIGO, G2_OPERAC, R_E_C_N_O_, D_E_L_E_T_
        If SG2->(dbSeek(xFilial("SG2")+ aItemsOP[nIndItem]["ItemCode"]+cCDRot+aItemsOP[nIndItem]["ActivityCode"]))

            nTmpPad:= ROUND(1000/SG2->G2_TEMPAD,0)

        endif

        aItemsOP[nIndItem]["CustomLabel1"] := "Meta/Hora"
        aItemsOP[nIndItem]["CustomValue1"] := CVALTOCHAR(nTmpPad)+" Peças"
        aItemsOP[nIndItem]["CustomLink1"]  := ""
        CONOUT("GDA FTP POSGetOP")
        CONOUT("ftp://totvs01:%283eTA4P%7CR1@ftp-totvs.delpi.com.br/"+alltrim(cCDPA)+".pdf")
        /*90262910 - https://drive.google.com/file/d/1jmHGqLTdgluTyVfL1nlhczyRhJfu6TdO/view?usp=drive_link
            90262793 - https://drive.google.com/file/d/1zFRYS4_uezZentgeAWFZgLzkaJpRdSJQ/view?usp=drive_link
            90261614 - https://drive.google.com/file/d/1LMaaAkYo6h-IqcfXAd_tVRgMKxkYQKJd/view?usp=drive_link
            90263912 - https://drive.google.com/file/d/1wqvTawUxXCOpQr41lgRG91455qc2Axna/view?usp=drive_link
            90263114 - https://drive.google.com/file/d/1dyKe-ekIjJUPiaB7a3Xx2eJCZqjcyXeu/view?usp=drive_link
        90480042 - https://drive.google.com/file/d/1VN7Tlsh7kmpYKlU0ys6EQ2CVpZ-36QK1/view?usp=drive_link*/
        cLink := ""

        if alltrim(cCDPA)=="90262793"
            cLink := "https://drive.google.com/file/d/1zFRYS4_uezZentgeAWFZgLzkaJpRdSJQ/view?usp=drive_link"
        elseif alltrim(cCDPA)=="90262910"
            cLink :="https://drive.google.com/file/d/1jmHGqLTdgluTyVfL1nlhczyRhJfu6TdO/view?usp=drive_link"
        elseif alltrim(cCDPA)=="90261614"
            cLink :="https://drive.google.com/file/d/1LMaaAkYo6h-IqcfXAd_tVRgMKxkYQKJd/view?usp=drive_link"
        elseif alltrim(cCDPA)=="90263912"
            cLink :="https://drive.google.com/file/d/1wqvTawUxXCOpQr41lgRG91455qc2Axna/view?usp=drive_link"
        elseif alltrim(cCDPA)=="90263114"
            cLink :="https://drive.google.com/file/d/1dyKe-ekIjJUPiaB7a3Xx2eJCZqjcyXeu/view?usp=drive_link"
        elseif alltrim(cCDPA)=="90263114"
            cLink :="https://drive.google.com/file/d/1VN7Tlsh7kmpYKlU0ys6EQ2CVpZ-36QK1/view?usp=drive_link"
        endif
        If FWIsAdmin()
            aItemsOP[nIndItem]["CustomLabel2"] := ""
            aItemsOP[nIndItem]["CustomValue2"] := "Desenho Tecnico PA"
            aItemsOP[nIndItem]["CustomLink2"]  :=  cLink

            aItemsOP[nIndItem]["CustomLabel3"] := ""
            aItemsOP[nIndItem]["CustomValue3"] := "Desenho Tecnico Intermediario"
            aItemsOP[nIndItem]["CustomLink3"]  :=  cLink
            // aItemsOP[nIndItem]["CustomLabel3"] := ""
            // aItemsOP[nIndItem]["CustomValue3"] := "Desenho Tecnico 3"
            // aItemsOP[nIndItem]["CustomLink3"]  := "http://totvs01:%283eTA4P%7CR1@ftp-totvs.delpi.com.br/"+alltrim(cCDPA)+".pdf"
            // aItemsOP[nIndItem]["CustomLabel4"] := ""
            // aItemsOP[nIndItem]["CustomValue4"] := "Desenho Tecnico 4"
            // aItemsOP[nIndItem]["CustomLink4"]  := "totvs01:%283eTA4P%7CR1@ftp-totvs.delpi.com.br/"+alltrim(cCDPA)+".pdf"
        endif

    Next nIndItem

Return aItemsOP
