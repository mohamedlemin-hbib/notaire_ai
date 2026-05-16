from app.services.rag_service import identify_missing_fields

parties = {"testateur": {"nom": "Testateur"}, "beneficiaire": {"nom": "Beneficiaire"}}
sc = "Acte de testament généré."
print(identify_missing_fields(parties, sc, "testament"))
