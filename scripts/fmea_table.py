"""
fmea_table.py
==============
Reproduces Table VIII from:
  "Use of Radio Frequency Identifiers in Autonomous Mobility Systems:
   With a Focus on Safety"
  IEEE Latin America Transactions, 2026
 
Table reproduced:
  - Table VIII: Simplified FMEA for RFID Perception Layer
 
FMEA scales (1–10):
  S  Severity    — 1 = negligible impact,    10 = catastrophic
  O  Occurrence  — 1 = extremely unlikely,   10 = near-certain
  D  Detectability — 1 = easily detected,    10 = undetectable
  RPN = S × O × D   (Risk Priority Number)
 
RPN thresholds:
  ≥ 100  Critical    — immediate action required
  40–99  Significant — action recommended
  < 40   Acceptable  — monitor, standard mitigation
 
Usage:
  python fmea_table.py [--export-csv PATH]
"""
 
import argparse
import csv
import sys
from dataclasses import dataclass, field
from typing import List
 
# ── FMEA dataclass ────────────────────────────────────────────────────────────
@dataclass
class FailureMode:
    id:          int
    name:        str
    cause:       str
    effect:      str
    S:           int      # Severity        (1–10)
    O:           int      # Occurrence      (1–10)
    D:           int      # Detectability   (1–10)
    mitigation:  str
    experimental_note: str = ""
 
    @property
    def RPN(self) -> int:
        return self.S * self.O * self.D
 
    @property
    def risk_level(self) -> str:
        if self.RPN >= 100:
            return "CRITICAL"
        if self.RPN >= 40:
            return "SIGNIFICANT"
        return "Acceptable"
 
 
# ── FMEA data (Table VIII) ────────────────────────────────────────────────────
FMEA_DATA: List[FailureMode] = [
    FailureMode(
        id=1,
        name="RFID missed detection",
        cause="Tag outside antenna beam; vehicle speed too high; "
              "multipath null zone; polling-window miss at high speed",
        effect="Sign not identified via RFID layer; "
               "vehicle falls back to vision-only perception path",
        S=4, O=3, D=2,
        mitigation="Fall back to vision layer; RFID absence is "
                   "detectable — trigger cautious mode. "
                   "Map-based expectation raises alertness in known sign zones. "
                   "Reduce polling interval to 50–100 ms.",
        experimental_note="Read rate: 100% for signs within geometric "
                           "envelope at all tested speeds (Table IV).",
    ),
    FailureMode(
        id=2,
        name="RFID false positive",
        cause="Adjacent-lane tag read; reflected signal from metallic "
              "surface (parked vehicles, guard rails); "
              "EPC mapping error",
        effect="Incorrect sign type output; potential unwarranted "
               "vehicle response",
        S=7, O=1, D=3,
        mitigation="Cross-validate with vision output and HD map. "
                   "42° beamwidth limits lateral contamination. "
                   "Priority-based arbitration: most restrictive sign applies.",
        experimental_note="Zero false positives observed across all 60 field "
                           "approaches and all qualitative high-speed runs.",
    ),
    FailureMode(
        id=3,
        name="Vision system failure",
        cause="Occlusion by vegetation; poor lighting; "
              "weathered or vandalized sign; adverse weather; "
              "adversarial perturbation",
        effect="Sign not detected visually; vehicle relies on "
               "RFID layer only",
        S=4, O=4, D=2,
        mitigation="RFID layer activates as primary source. "
                   "This is the primary use case of the proposed architecture: "
                   "RFID provides reliable symbolic output independent of "
                   "visual conditions.",
        experimental_note="Vision-only degradation scenarios motivate the "
                           "RFID redundancy layer (Introduction, Section I).",
    ),
    FailureMode(
        id=4,
        name="RFID–Vision type conflict",
        cause="Tampered or misassigned tag; vision misclassification; "
              "temporary sign obscuring RFID-tagged sign",
        effect="Ambiguous sign identity; potential incorrect "
               "vehicle action",
        S=8, O=1, D=2,
        mitigation="Arbitration rule: apply most restrictive interpretation "
                   "(STOP > PED. CROSSING > SPEED LIMIT). "
                   "Alert driver. Cross-check with HD-map expected sign type.",
        experimental_note="Priority ordering validated in simultaneous "
                           "multi-tag bench tests (Section III-A, Fig. 8–9).",
    ),
    FailureMode(
        id=5,
        name="Latency exceeds safety threshold",
        cause="Fixed 500 ms polling interval; TCP/IP overhead; "
              "Python processing time; "
              "tag traverses detection zone during latency window",
        effect="Sign identified too late for emergency braking at "
               "speeds above 20 km/h; "
               "insufficient stopping distance",
        S=9, O=4, D=4,
        mitigation="Position system as ANTICIPATORY layer, not reactive trigger. "
                   "Reduce polling to 50–100 ms (software only). "
                   "Use map-based pre-alerting: decelerate before sign zone. "
                   "Direct braking actuation: limit to v ≤ 20 km/h "
                   "(P_safe = 92.7%).",
        experimental_note="P(safe|40 km/h) < 2% (Table VI). "
                           "Dwell-window miss at v ≥ 30 km/h for d = 3.0 m "
                           "(Table V). This is the sole critical failure mode.",
    ),
    FailureMode(
        id=6,
        name="Dual-source failure",
        cause="System power loss; Raspberry Pi crash; "
              "TCP/IP network failure; "
              "camera and RFID reader both offline simultaneously",
        effect="Complete loss of RFID-based sign perception; "
               "vehicle relies on driver or other automation layers",
        S=9, O=1, D=2,
        mitigation="Watchdog timer detects subsystem silence. "
                   "Trigger minimal-risk condition (MRC): "
                   "reduce to safe speed, activate hazard lights, "
                   "controlled stop or driver handover request.",
        experimental_note="No system failures observed during experimental "
                           "sessions (bench or field).",
    ),
]
 
RPN_CRITICAL    = 100
RPN_SIGNIFICANT = 40
 
# ── Print helpers ─────────────────────────────────────────────────────────────
SEP  = "─" * 92
SEP2 = "═" * 92
 
 
def section(title: str) -> None:
    print(f"\n{SEP2}")
    print(f"  {title}")
    print(SEP2)
 
 
def divider() -> None:
    print(f"  {SEP}")
 
 
def risk_badge(rpn: int) -> str:
    if rpn >= RPN_CRITICAL:
        return f"[!!! CRITICAL  RPN={rpn:>3}]"
    if rpn >= RPN_SIGNIFICANT:
        return f"[!  SIGNIFICANT RPN={rpn:>3}]"
    return f"[   acceptable  RPN={rpn:>3}]"
 
 
# ── Table VIII ────────────────────────────────────────────────────────────────
def print_table_viii() -> None:
    section("TABLE VIII — Simplified FMEA for RFID Perception Layer")
 
    print(
        f"  {'#':>2}  {'Failure mode':<28}  "
        f"{'Effect (summary)':<35}  "
        f"{'S':>2}  {'O':>2}  {'D':>2}  {'RPN':>5}  {'Risk':>12}"
    )
    divider()
 
    for fm in FMEA_DATA:
        # Truncate long strings for the compact table view
        name_s   = (fm.name[:26] + "..") if len(fm.name) > 28 else fm.name
        effect_s = (fm.effect[:33] + "..") if len(fm.effect) > 35 else fm.effect
        print(
            f"  {fm.id:>2}  {name_s:<28}  "
            f"{effect_s:<35}  "
            f"{fm.S:>2}  {fm.O:>2}  {fm.D:>2}  "
            f"{fm.RPN:>5}  {fm.risk_level:>12}"
        )
 
    divider()
    critical = [fm for fm in FMEA_DATA if fm.RPN >= RPN_CRITICAL]
    signif   = [fm for fm in FMEA_DATA if RPN_SIGNIFICANT <= fm.RPN < RPN_CRITICAL]
    accept   = [fm for fm in FMEA_DATA if fm.RPN < RPN_SIGNIFICANT]
    print(f"\n  S = Severity · O = Occurrence · D = Detectability  (1–10 scale)")
    print(f"  D: 1 = easily detected, 10 = undetectable")
    print(f"  RPN = S × O × D")
    print(f"\n  RPN thresholds:  "
          f"≥ {RPN_CRITICAL} CRITICAL ({len(critical)} modes)  |  "
          f"{RPN_SIGNIFICANT}–{RPN_CRITICAL-1} SIGNIFICANT ({len(signif)} modes)  |  "
          f"< {RPN_SIGNIFICANT} Acceptable ({len(accept)} modes)")
 
 
# ── Detailed card per failure mode ────────────────────────────────────────────
def print_detail() -> None:
    section("Failure Mode Details — Causes, Mitigations, Experimental Evidence")
    for fm in FMEA_DATA:
        badge = risk_badge(fm.RPN)
        print(f"\n  {badge}  FM-{fm.id}: {fm.name}")
        print(f"  {SEP[:60]}")
        _wrap_print("Cause",       fm.cause)
        _wrap_print("Effect",      fm.effect)
        _wrap_print("Mitigation",  fm.mitigation)
        if fm.experimental_note:
            _wrap_print("Evidence",    fm.experimental_note)
        print(f"  S={fm.S}  O={fm.O}  D={fm.D}  RPN={fm.RPN}")
 
 
def _wrap_print(label: str, text: str, width: int = 70) -> None:
    """Print a labelled multi-line field with wrapping."""
    words = text.split()
    line  = f"  {label:<13}"
    for word in words:
        if len(line) + len(word) + 1 > width + len(label) + 4:
            print(line)
            line = " " * (len(label) + 4) + word
        else:
            line += (" " if len(line) > len(label) + 4 else "") + word
    print(line)
 
 
# ── RPN ranking ───────────────────────────────────────────────────────────────
def print_ranking() -> None:
    section("RPN Ranking — All Failure Modes")
    ranked = sorted(FMEA_DATA, key=lambda fm: fm.RPN, reverse=True)
    print(f"  {'Rank':>4}  {'FM-#':>4}  {'Failure mode':<30}  "
          f"{'S':>2}  {'O':>2}  {'D':>2}  {'RPN':>5}  {'Risk':>12}")
    divider()
    for rank, fm in enumerate(ranked, 1):
        print(
            f"  {rank:>4}  FM-{fm.id:>1}  {fm.name:<30}  "
            f"{fm.S:>2}  {fm.O:>2}  {fm.D:>2}  "
            f"{fm.RPN:>5}  {fm.risk_level:>12}"
        )
    divider()
    total_rpn = sum(fm.RPN for fm in FMEA_DATA)
    max_fm    = ranked[0]
    print(f"\n  Total RPN:     {total_rpn}")
    print(f"  Max RPN:       {max_fm.RPN}  (FM-{max_fm.id}: {max_fm.name})")
    print(f"  Critical mode: FM-{max_fm.id} is the ONLY failure mode")
    print(f"                 above the critical threshold (RPN ≥ {RPN_CRITICAL}).")
    print(f"\n  Conclusion: the system's safety case rests on managing FM-{max_fm.id}")
    print(f"  (latency) through operational design (anticipatory layer,")
    print(f"  polling reduction, map-based pre-alerting). All other failure")
    print(f"  modes are mitigable at the perception and arbitration layers.")
 
 
# ── CSV export ────────────────────────────────────────────────────────────────
def export_csv(path: str) -> None:
    fieldnames = [
        "id", "name", "cause", "effect",
        "S", "O", "D", "RPN", "risk_level",
        "mitigation", "experimental_note"
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for fm in FMEA_DATA:
            writer.writerow({
                "id": fm.id, "name": fm.name, "cause": fm.cause,
                "effect": fm.effect, "S": fm.S, "O": fm.O, "D": fm.D,
                "RPN": fm.RPN, "risk_level": fm.risk_level,
                "mitigation": fm.mitigation,
                "experimental_note": fm.experimental_note,
            })
    print(f"  CSV exported: {path}")
 
 
# ── Main ─────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reproduce Table VIII — FMEA for RFID Perception Layer"
    )
    parser.add_argument("--detail",     action="store_true",
                        help="Print detailed cause/mitigation/evidence per mode")
    parser.add_argument("--export-csv", metavar="PATH", default=None,
                        help="Export FMEA data to CSV file")
    args = parser.parse_args()
 
    print(f"\n{'═'*92}")
    print("  RFID Traffic Sign Recognition — Failure Mode and Effects Analysis (FMEA)")
    print("  IEEE Latin America Transactions, 2026")
    print(f"{'═'*92}")
 
    print_table_viii()
    print_ranking()
 
    if args.detail:
        print_detail()
 
    if args.export_csv:
        export_csv(args.export_csv)
 
    print(f"\n{'═'*92}\n")
 
 
if __name__ == "__main__":
    main()
