#include 'protheus.ch'
#include 'parmtype.ch'

user function DLP036()

	Local cOpc     := &(ReadVar())
	Local nTamB1   := TAMSX3("B1_DESC")[1]
	Local cDesc    := "ROHS"
//	lOCAL cDescB1  := ALLTRIM(IIF(INCLUI,M->B1_DESC,SB1->B1_DESC))
Local oModel

	oModel  := FwModelActive()
	cDescB1 := oModel:GetValue("SB1MASTER","B1_DESC")

	IF  ! EMPTY (cOpc )

		IF cOpc $ "S"
		
			IF !(   cDesc $ cDescB1)
		
				cDescB1 := padr ( alltrim ( cDescB1 ) + " - " + cDesc , nTamB1 )
		
			ENDIF
		
		ELSE
		
			IF (cDesc $ cDescB1)
			
				cDescB1 := padr ( STRTRAN(cDescB1,+ " - " +cDesc,"")  , nTamB1 )
				//substr(cDescB1,1,len(cDescB1)-len(cDesc))
				
			ENDIF
		
		ENDIF

	ENDIF
		
return cDescB1 