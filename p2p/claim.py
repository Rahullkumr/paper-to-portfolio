"""Claim checklist. Fixed text written by a human, never generated, because a wrong
legal step costs a family months. General guidance only: confirm with the company's
Registrar and Transfer Agent (RTA) or the IEPF Authority before filing anything.
"""


def checklist(certificate, trace_result, holder_deceased=False):
    company = trace_result["company_today"]
    steps = [
        {
            "title": "Check whether the shares or dividends went to IEPF",
            "detail": (
                "If dividends stayed unclaimed for 7 years in a row, the company must move the shares "
                "to the Investor Education and Protection Fund. Search iepf.gov.in by the holder's name, "
                f"folio {certificate['folio']} and the company name ({certificate['company']} and {company})."
            ),
        },
        {
            "title": f"Write to the RTA of {company}",
            "detail": (
                f"Quote folio {certificate['folio']} and certificate no. {certificate['certificate_no']}. "
                "Ask them to confirm the current holding, including bonus and merger shares issued since, "
                "and any unpaid dividends. The RTA's name is on the company's investor page."
            ),
        },
        {
            "title": "Update KYC for the physical folio",
            "detail": "Send PAN, address proof, bank details and a nomination to the RTA (SEBI form ISR-1 and related forms).",
        },
    ]
    if holder_deceased:
        steps.append({
            "title": "Transmission to the legal heir",
            "detail": (
                "Submit the death certificate plus the nomination, a succession certificate or other "
                "legal-heir documents as the RTA asks. SEBI allows simpler documents for smaller holdings."
            ),
        })
    steps += [
        {
            "title": "Dematerialise",
            "detail": (
                "Physical shares can no longer be transferred or sold as paper. Open a demat account and "
                "submit the certificates (or the RTA's Letter of Confirmation) through your depository participant."
            ),
        },
        {
            "title": "If anything is with IEPF: file IEPF-5",
            "detail": (
                "File form IEPF-5 online on the MCA portal, then send the signed copy and documents "
                "to the company's Nodal Officer. One form per company."
            ),
        },
    ]
    return steps
