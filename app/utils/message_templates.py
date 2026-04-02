DISCLAIMER_EN = "\n\n_Unofficial community bot. Official info: srisailadevasthanam.org_"
DISCLAIMER_TE = "\n\n_అనధికారిక కమ్యూనిటీ బాట్. అధికారిక సమాచారం: srisailadevasthanam.org_"
DISCLAIMER_HI = "\n\n_अनौपचारिक सामुदायिक बॉट। आधिकारिक जानकारी: srisailadevasthanam.org_"

def get_disclaimer(lang: str = "en") -> str:
    disclaimers = {
        "en": DISCLAIMER_EN,
        "te": DISCLAIMER_TE,
        "hi": DISCLAIMER_HI
    }
    return disclaimers.get(lang, DISCLAIMER_EN)