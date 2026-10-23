#INCLUDE "PROTHEUS.CH"
#INCLUDE "TOPCONN.ch"

User Function SPED1601()

    Local aReg1601  := {}


    // COD_PART_IP - COD_PART_IT - TOT_VS - TOT_ISS - TOT_OUTROS
    // Exemplo do Array
    // aAdd (aReg1601, {"CODIGO_CLIENTE_ADM_CARTAO","CODIGO_INTERMEDIADOR",0,0,0})
    // OBS:
    // COD_PART_IP: O valor informado deve existir no campo COD_PART do registro 0150.
    // COD_PART_IT: O valor informado deve existir no campo COD_PART do registro 0150.
    // TOT_VS : o valor deve ser preenchido com o total bruto de vendas que tiveram escrituração de ICMS , inclusive como ICMS Isento ou Outros
    // TOT_ISS: o valor deve ser preenchido com o total bruto de prestação de serviços que tiveram incidência de ISS.
    // TOT_OUTROS : o valor de ser preenchido com o total bruto das operações que não estejam no campo de incidência do ICMS ou ISS.

    /*
    No modulo SIGAFAT não há o controle de Administradoras de Cartão para poder fazer amarração, portanto a ideia é fazer um DEPARA com a condição de pagamento
    e ter um registro na tabela SA1 que corresponda a operadora.
    Ex.: Foi criado a Condição de Pagamento "002" que corresponde as vendas de Cartão de Credito, também foi criado um registro na tabela SA1 com as informações
    da operadora de Cartão de Credito.
    Sugestão para montagem da Consulta no banco de Dados:
    */
    if cEmpAnt == '01'  .and. xFilial("SD2") == '01'
        aADD(aReg1601, {'01' , '001   01' , '' , 310956.37 ,0.00, 0.00 , 0.00 } )
        aADD(aReg1601, {'01' , '002   01' , '' , 4721.87 ,0.00, 0.00 , 0.00 } )

    elseif cEmpAnt == '01'  .and. xFilial("SD2") == '02'
        aADD(aReg1601, {'02' , '001   01' , '' , 42569.35 ,0.00 , 0.00 , 0.00 } )
        aADD(aReg1601, {'02' , '002   01' , '' , 24334.35 , 0.00 , 0.00 , 0.00} )
        aADD(aReg1601, {'02' , '003   01' , '' , 1555198.69 ,0.00, 0.00 , 0.00 } )
        //  aADD(aReg1601, {(cAliasTrb)->FILIAL,cCodAdm,(cAliasTrb)->INTERMEDIADOR,(cAliasTrb)->TOT_VS,(cAliasTrb)->TOT_ISS,(cAliasTrb)->TOT_OUT})
    elseif cEmpAnt == '04'  .and. xFilial("SD2") == '01'
        aADD(aReg1601, {'01' , '101   01' , '      ' , 125205.55 , 0.00 , 125205.55 } )
        aADD(aReg1601, {'01' , '756   01' , '      ' , 27012.61 , 0.00 , 27012.61 } )
    elseif cEmpAnt == '04'  .and. xFilial("SD2") == '02'
        aADD(aReg1601, {'02' , '101   01' , '      ' , 1000.00 , 0.00 , 1000.00 } )
        aADD(aReg1601, {'02' , '756   01' , '      ' , 138153.16 , 0.00 , 138153.16 } )

    elseif cEmpAnt == '05'  .and. xFilial("SD2") == '01'
        aADD(aReg1601, {'01' , '756   01' , '      ' , 104044.69 , 0.00 , 104044.69 } )
    ENDIF
Return aReg1601
