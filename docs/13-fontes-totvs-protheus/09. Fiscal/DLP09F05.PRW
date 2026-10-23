

/*/{Protheus.doc} DLP09F05
@Description
@Author 	 TSC - Gabriel Araujo
@Since  	 05/05/2025
@Cliente	 Delpi

C:\Users\Gabriel\OneDrive\Protheus\Fontes\Padrao2025\2310\Master\Fontes\Livros Fiscais\matxfis.prx
C:\Users\Gabriel\OneDrive\Protheus\Fontes\Padrao2025\2310\Master\Fontes\Livros Fiscais\IMPXFIS.prw
//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
				//³ Inicializa a gravacao nas funcoes Fiscais               ³
				//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
				MaFisWrite()
		        MAFISCDA(,,.T.,(cAlias)->("E"+F1_ESPECIE+F1_FORMUL+F1_DOC+F1_SERIE+F1_FORNECE+F1_LOJA),(cAlias)->F1_FORMUL,cAlias,.T.)
		        MAFISCDA(,2,,(cAlias)->("E"+F1_ESPECIE+F1_FORMUL+F1_DOC+F1_SERIE+F1_FORNECE+F1_LOJA),(cAlias)->F1_FORMUL,cAlias,.T.)
#include 'rwmake.ch'
#include 'topconn.ch'
#INCLUDE 'SET.CH'
#INCLUDE 'protheus.CH'
#Include 'FWMVCDef.ch'
/*/
User Function DLP09F05()

Return
