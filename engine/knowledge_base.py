"""
knowledge_base.py — Structured Regulatory Knowledge Base

Each pillar contains a list of natural-language "anchor" sentences derived from
the specific regulatory frameworks:
  - WHO Guidance on Ethics and Governance of AI for Health (2021)
  - Cartagena Protocol on Biosafety (2000)
  - DURC Guidelines (ASPR/NSABB)
  - Declaration of Helsinki (WMA, 2013 rev.)
  - Biological Weapons Convention (BWC, 1972)

Anchors are NOT keywords — they are semantically rich sentences that a
sentence-transformer model can embed and compare against document chunks
via cosine similarity. This allows paraphrase understanding and contextual
reasoning rather than literal keyword matching.
"""

# ─────────────────────────────────────────────────────────────────────────────
# PILLAR 1: BIOSAFETY & BIOSECURITY
# Frameworks: DURC/ASPR, Cartagena Protocol, BWC
# ─────────────────────────────────────────────────────────────────────────────
BIOSAFETY_ANCHORS = [
    # Positive compliance anchors
    "All procedures were conducted under BSL-2 containment with enhanced biosafety protocols.",
    "The research was reviewed and approved by the Institutional Biosafety Committee prior to initiation.",
    "A dual-use research of concern review was completed in accordance with ASPR and NSABB guidance.",
    "The pathogen strain was attenuated and rendered non-pathogenic for vaccine development purposes.",
    "The modified organism is maintained under BSL-3 containment with select agent security protocols.",
    "Containment measures were established to prevent unintended release of biological materials.",
    "This research is subject to oversight by both the IBC and applicable select agent regulations.",
    "The study was conducted in a certified biosafety cabinet within a secured containment facility.",
    "All biological agents used were inactivated or deactivated prior to transport and secondary analysis.",
    "Risk assessment confirmed no enhanced pandemic potential was created during experimental procedures.",
    "The study complies with DURC policy guidelines and NSABB dual-use risk evaluation criteria.",
    "Biosafety protocols were implemented to prevent occupational exposure and environmental contamination.",
    "Select agent enumeration and security protocols were followed throughout the experimental workflow.",

    # Negative / risk anchors (for detecting absence of safety or misuse potential)
    "This research involves gain-of-function modifications to increase transmissibility of the pathogen.",
    "The experiment enhances the virulence or host range of an already dangerous pathogen.",
    "The biological agent was engineered for potential dual-use as a biological weapon.",
    "No institutional biosafety oversight was obtained before initiating the high-risk research.",
    "The pathogen was released into uncontrolled environments without regulatory approval.",
    "This study creates a novel pathogen with no justification for prophylactic or protective purposes.",
    "The research involves weaponization of biological toxins or enhancement of lethality.",
]

# ─────────────────────────────────────────────────────────────────────────────
# PILLAR 2: INFORMED CONSENT & WELFARE
# Frameworks: Declaration of Helsinki, WHO AI Health Ethics
# ─────────────────────────────────────────────────────────────────────────────
CONSENT_ANCHORS = [
    # Positive compliance anchors
    "Ethical approval was obtained from the Institutional Review Board prior to subject recruitment.",
    "All participants provided written informed consent before any study procedures were initiated.",
    "The study design complies with the ethical principles of the Declaration of Helsinki.",
    "Voluntary participation was ensured and participants were informed of their right to withdraw.",
    "Participants were given a comprehensive briefing covering the study aims, risks, and benefits.",
    "Animals used in this study were cared for in accordance with the 3Rs principles: Replace, Reduce, Refine.",
    "The IACUC reviewed and approved all animal research procedures in this study.",
    "The animal study minimized suffering through implementation of humane endpoints and refinement protocols.",
    "An IRB reference number was assigned confirming independent ethics committee review.",
    "Subjects were informed of anticipated benefits, known risks, and their rights as research participants.",
    "Human subject data was collected only after signed consent forms were obtained and documented.",
    "Participant welfare was monitored throughout the study with a designated safety monitoring committee.",
    "All research involving human subjects was conducted in full compliance with international ethical standards.",

    # Negative anchors
    "Patient records were accessed without obtaining individual informed consent from subjects.",
    "The study was conducted without IRB or ethics committee review or approval.",
    "Consent was waived without documentation of why informed consent was not feasible.",
    "Participants were not fully informed about the risks and purposes of the experimental procedures.",
    "Vulnerable populations such as prisoners or minors were enrolled without appropriate safeguards.",
    "Animal subjects were subjected to severe pain or distress without effective pain management.",
]

# ─────────────────────────────────────────────────────────────────────────────
# PILLAR 3: ENVIRONMENTAL STEWARDSHIP
# Frameworks: Cartagena Protocol, BWC
# ─────────────────────────────────────────────────────────────────────────────
ENVIRONMENTAL_ANCHORS = [
    # Positive compliance anchors
    "An environmental impact assessment was completed prior to release of any modified organisms.",
    "The risk assessment followed Cartagena Protocol Article 15 standards for living modified organisms.",
    "All genetically modified organisms are contained within a certified greenhouse facility with strict controls.",
    "Measures were taken to prevent unintended transboundary movement of living modified organisms.",
    "Potential adverse effects on non-target organisms, biodiversity, and ecosystem services were assessed.",
    "Waste biological materials are disposed of according to certified biosafety discard protocols.",
    "The study includes an ecological risk assessment covering effects on native flora and fauna.",
    "Field trials were conducted only within contained enclosures with perimeter biosecurity controls.",
    "Biodiversity impact was modeled and mitigation strategies were documented before study initiation.",
    "Environmental monitoring was performed at all study sites to detect unintended ecological effects.",
    "The containment strategy includes multiple redundant barriers to prevent environmental dispersion.",
    "Regulatory approval was obtained from the national biosafety authority before environmental release.",

    # Negative anchors
    "The modified organism was released into open fields without any regulatory permit or authorization.",
    "No environmental risk assessment was conducted prior to releasing the biological material outdoors.",
    "The study poses a risk of uncontrolled dispersal of genetically modified material into natural ecosystems.",
    "Containment failures could result in contamination of native species and irreversible biodiversity loss.",
    "Uncontrolled release of the engineered organism into the environment occurred during the study.",
]

# ─────────────────────────────────────────────────────────────────────────────
# PILLAR 4: DATA PRIVACY & ETHICS
# Frameworks: WHO AI Health Ethics, Declaration of Helsinki
# ─────────────────────────────────────────────────────────────────────────────
DATA_ANCHORS = [
    # Positive compliance anchors
    "All genomic sequence data were de-identified prior to deposition in public repositories.",
    "A data governance framework was implemented to regulate access, storage, and secondary use.",
    "Participant data was anonymized using certified de-identification methods before analysis.",
    "Genomic data inherently linked to individuals is protected under a restricted-access management plan.",
    "The study complies with WHO AI Health Ethics guidance on health data privacy and governance.",
    "Data security measures including encryption, access control, and audit logging were implemented.",
    "Participants retain the right to withdraw their data from the study at any time without penalty.",
    "A data management plan was registered and approved, limiting data use to defined research purposes.",
    "Pseudonymization was applied to all personal identifiers before datasets were shared with collaborators.",
    "Role-based access controls limit data access strictly to authorized research personnel.",
    "Secondary use of clinical data is only permitted with explicit patient consent or ethical waiver.",
    "The system complies with applicable data protection regulations including GDPR provisions.",

    # Negative anchors
    "Identifiable patient data was used for model training without obtaining individual consent.",
    "Genomic data containing personal identifiers was shared publicly without restriction.",
    "No data governance or access control mechanisms were in place to protect sensitive health data.",
    "Participant data was transferred to a third party without authorization or data sharing agreement.",
    "Re-identification of anonymized participant data is possible given the variables retained in the dataset.",
]

# ─────────────────────────────────────────────────────────────────────────────
# PILLAR 5: JUSTICE & RESEARCH EQUITY
# Frameworks: Declaration of Helsinki, WHO AI Health Ethics
# ─────────────────────────────────────────────────────────────────────────────
JUSTICE_ANCHORS = [
    # Positive compliance anchors
    "A benefit-sharing agreement ensures equitable distribution of research outcomes to partner communities.",
    "The study includes community engagement with local populations in all three participating countries.",
    "Equitable access to the developed vaccine or treatment was explicitly built into the research design.",
    "Capacity building initiatives were established to strengthen research infrastructure in LMIC institutions.",
    "The research priorities respond directly to the health needs of the vulnerable populations enrolled.",
    "A Material Transfer Agreement ensures compliance with Nagoya Protocol obligations on benefit-sharing.",
    "Low- and middle-income country partners are co-investigators with full intellectual property rights.",
    "The study is responsive to local community priorities as confirmed through formal consultation processes.",
    "Research findings will be published under open-access licenses to maximize global accessibility.",
    "Knowledge transfer programs are included to ensure partner institutions develop long-term capacity.",
    "An ethics committee from the local LMIC institution reviewed and approved this research.",
    "Community advisory boards representing participant populations were consulted during study design.",

    # Negative anchors
    "Research benefits accrue exclusively to the sponsoring organization with no sharing arrangement.",
    "Results from a study on LMIC populations are restricted by proprietary agreements that block local access.",
    "The vulnerable population was used as a research subject pool without corresponding benefit to their community.",
    "No consideration was given to global equity in access to the medical intervention developed in this study.",
    "The research exploits biological samples from indigenous communities without consent or compensation.",
]

# ─────────────────────────────────────────────────────────────────────────────
# MASTER KNOWLEDGE BASE
# ─────────────────────────────────────────────────────────────────────────────
KNOWLEDGE_BASE = {
    "biosafety":     BIOSAFETY_ANCHORS,
    "consent":       CONSENT_ANCHORS,
    "environmental": ENVIRONMENTAL_ANCHORS,
    "data":          DATA_ANCHORS,
    "justice":       JUSTICE_ANCHORS,
}

# Regulatory citations per pillar (mirrors the frontend REGULATORY_CLAUSES exactly)
REGULATORY_CLAUSES = {
    "biosafety": [
        {"source": "DURC/ASPR · Section 3.1", "text": "Research that produces, aims to produce, or can be reasonably anticipated to produce one or more of the listed experimental effects must be evaluated for dual use research of concern (DURC) potential and requires Institutional Biosafety Committee (IBC) review."},
        {"source": "Cartagena Protocol · Article 26", "text": "The Parties, in reaching a decision on import under this Protocol or under its domestic measures implementing the Protocol, may take into account, consistent with their international obligations, socio-economic considerations arising from the impact of living modified organisms on the conservation and sustainable use of biological diversity."},
        {"source": "BWC · Article I", "text": "Each State Party to this Convention undertakes never in any circumstances to develop, produce, stockpile or otherwise acquire or retain: (1) Microbial or other biological agents, or toxins whatever their origin or method of production, of types and in quantities that have no justification for prophylactic, protective or other peaceful purposes."},
    ],
    "consent": [
        {"source": "Declaration of Helsinki · §25", "text": "Participation by individuals capable of giving informed consent as subjects in medical research must be voluntary. Although it may be appropriate to consult family members or community leaders, no individual capable of giving informed consent may be enrolled in a research study unless he or she freely agrees."},
        {"source": "Declaration of Helsinki · §26", "text": "In medical research involving human subjects capable of giving informed consent, each potential subject must be adequately informed of the aims, methods, sources of funding, any possible conflicts of interest, institutional affiliations of the researcher, the anticipated benefits and potential risks of the study and the discomfort it may entail."},
        {"source": "WHO AI Health Ethics · §4.3", "text": "AI technologies should not be used in ways that result in people being deceived or manipulated... Individuals should be able to exercise meaningful control over data collected about them, including the right to withdraw consent."},
    ],
    "environmental": [
        {"source": "Cartagena Protocol · Article 16", "text": "The Parties shall, taking into account Article 8 (g) of the Convention, establish and maintain appropriate mechanisms, measures and strategies to regulate, manage and control risks identified in the risk assessment provisions of this Protocol associated with the use, handling and transboundary movement of living modified organisms."},
        {"source": "Cartagena Protocol · Article 15", "text": "Risk assessments undertaken pursuant to this Protocol shall be carried out in a scientifically sound manner, in accordance with Annex III and taking into account recognized risk assessment techniques. Such risk assessments shall be based, at a minimum, on information provided in accordance with Article 8 and other available scientific evidence."},
    ],
    "data": [
        {"source": "WHO AI Health Ethics · §5.1", "text": "The privacy and confidentiality of patient data must be protected, prioritizing data de-identification and enforcing strict access controls to prevent unauthorized profiling or disclosure."},
        {"source": "Declaration of Helsinki · §24", "text": "Every precaution must be taken to protect the privacy of research subjects and the confidentiality of their personal information."},
    ],
    "justice": [
        {"source": "Declaration of Helsinki · §20", "text": "Medical research with a vulnerable group is only justified if the research is responsive to the health needs or priorities of this group and the research cannot be carried out in a non-vulnerable group. In addition, this group should stand to benefit from the knowledge, practices or interventions that result from the research."},
        {"source": "WHO AI Health Ethics · §8.2", "text": "Designers and developers of AI technologies should ensure that AI systems do not exacerbate existing health inequalities. There should be equitable access to the benefits of AI technologies, and risks should not disproportionately fall upon vulnerable populations."},
    ],
}

# Number of positive vs negative anchor sentences per pillar
# Used by scoring to understand anchor polarity
ANCHOR_POLARITY = {
    "biosafety":     {"positive": 13, "negative": 7},
    "consent":       {"positive": 13, "negative": 6},
    "environmental": {"positive": 12, "negative": 5},
    "data":          {"positive": 12, "negative": 5},
    "justice":       {"positive": 12, "negative": 5},
}
