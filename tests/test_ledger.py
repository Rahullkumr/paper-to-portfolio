import unittest
from pathlib import Path

from p2p import claim, ledger

SAMPLE_TEXT = (Path(__file__).parent.parent / "samples" / "sample_actions.txt").read_text()

CERT = {
    "company": "SAHYADRI SPINNING MILLS LIMITED",
    "holder": "RAMESH KASHINATH JOSHI",
    "folio": "S-01923",
    "certificate_no": "004417",
    "shares": 100,
    "face_value": 10,
    "issue_date": "1989-03-14",
}

# What a well-behaved model returns for samples/sample_actions.txt
ACTIONS = [
    {"date": "12-08-1994", "type": "bonus", "give": 1, "per": 1, "from_fv": 0, "to_fv": 0, "into": "",
     "evidence": "a bonus issue of equity shares in the ratio of 1:1, i.e. one new equity share for every one existing equity share held."},
    {"date": "20-02-2001", "type": "bonus", "give": 1, "per": 2, "from_fv": 0, "to_fv": 0, "into": "",
     "evidence": "Bonus in the ratio 1:2, i.e. one bonus share for every two equity shares held."},
    {"date": "15-09-2006", "type": "split", "give": 0, "per": 0, "from_fv": 10, "to_fv": 2, "into": "",
     "evidence": "Sub-division of equity shares from face value Rs. 10 each to face value Rs. 2 each."},
    {"date": "01-04-2011", "type": "merger", "give": 3, "per": 4, "from_fv": 0, "to_fv": 0, "into": "Deccan Textiles Ltd",
     "evidence": "Shareholders shall receive 3 equity shares of Rs. 2 each of Deccan Textiles Ltd for every 4 equity shares"},
    {"date": "10-07-2018", "type": "rename", "give": 0, "per": 0, "from_fv": 0, "to_fv": 0, "into": "Deccan Fabtech Ltd",
     "evidence": "Deccan Textiles Ltd has changed its name to Deccan Fabtech Ltd"},
]


class TraceTest(unittest.TestCase):
    def test_sample_lineage(self):
        accepted, rejected = ledger.verify(ACTIONS, SAMPLE_TEXT)
        self.assertEqual(rejected, [])
        result = ledger.trace(CERT, accepted)
        # 100 -> bonus 1:1 = 200 -> bonus 1:2 = 300 -> split 10->2 = 1500 -> merger 3:4 = 1125
        self.assertEqual([s["shares"] for s in result["timeline"]], [100, 200, 300, 1500, 1125, 1125])
        self.assertEqual(result["company_today"], "Deccan Fabtech Ltd")
        self.assertEqual(result["face_value_today"], 2.0)
        self.assertEqual(result["growth"], "11.25x")
        self.assertEqual(ledger.value(result["shares_today"], 412.5), 464062.5)

    def test_fraction_is_floored_and_recorded(self):
        cert = {**CERT, "shares": 7}
        merger = {**ACTIONS[3], "date": "2011-04-01"}
        result = ledger.trace(cert, [merger])
        self.assertEqual(result["shares_today"], 5)  # 7 * 3/4 = 5.25
        self.assertAlmostEqual(result["timeline"][-1]["fraction_paid_in_cash"], 0.25)

    def test_actions_before_issue_are_skipped(self):
        early = {**ACTIONS[0], "date": "1980-01-01"}
        result = ledger.trace(CERT, [early])
        self.assertEqual(result["shares_today"], 100)
        self.assertEqual(len(result["skipped"]), 1)

    def test_consolidation_reduces_shares(self):
        cons = {"date": "2000-01-01", "type": "consolidation", "from_fv": 1, "to_fv": 10, "evidence": ""}
        self.assertEqual(ledger.trace(CERT, [cons])["shares_today"], 10)


class VerifyTest(unittest.TestCase):
    def test_invented_evidence_is_rejected(self):
        fake = {**ACTIONS[0], "evidence": "Bonus issue in the ratio 5:1 approved by the board."}
        accepted, rejected = ledger.verify([fake], SAMPLE_TEXT)
        self.assertEqual(accepted, [])
        self.assertIn("evidence", rejected[0]["reason"])

    def test_missing_ratio_is_rejected(self):
        incomplete = {**ACTIONS[1], "give": 0}
        accepted, rejected = ledger.verify([incomplete], SAMPLE_TEXT)
        self.assertEqual(accepted, [])
        self.assertIn("missing give", rejected[0]["reason"])

    def test_whitespace_and_case_are_forgiven(self):
        loose = {**ACTIONS[2], "evidence": "SUB-DIVISION of equity shares   from face value\nRs. 10 each"}
        accepted, _ = ledger.verify([loose], SAMPLE_TEXT)
        self.assertEqual(len(accepted), 1)
        self.assertEqual(accepted[0]["date"], "2006-09-15")


class ClaimTest(unittest.TestCase):
    def test_transmission_step_only_when_deceased(self):
        result = ledger.trace(CERT, [])
        titles = [s["title"] for s in claim.checklist(CERT, result)]
        self.assertFalse(any("Transmission" in t for t in titles))
        titles = [s["title"] for s in claim.checklist(CERT, result, holder_deceased=True)]
        self.assertTrue(any("Transmission" in t for t in titles))


if __name__ == "__main__":
    unittest.main()
