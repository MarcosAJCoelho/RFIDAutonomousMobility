"""
bayesian_fusion.py
===================
Reproduces Table VII from:
  "Use of Radio Frequency Identifiers in Autonomous Mobility Systems:
   With a Focus on Safety"
  IEEE Latin America Transactions, 2026
 
Table reproduced:
  - Table VII: Bayesian Posterior by Sensor State
 
Model:
  H   = traffic sign of type T is present at current location
  R   = RFID detection event  ∈ {0, 1}
  V   = Vision detection event ∈ {0, 1}
 
  P(H|R,V) = P(R|H) · P(V|H) · P(H) / P(R,V)    [conditional independence]
 
Parameters derived from experimental data:
  P(R=1|H)  = 1.00  — 100% detection rate within antenna envelope (n=60 approaches)
  P(R=1|¬H) = 0.00  — zero false positives observed across all field sessions
  P(V=1|H)  = 0.85  — literature estimate (favorable conditions)
  P(V=1|¬H) = 0.05  — literature estimate (typical classifier FPR)
  P(H)      = 0.70  — map-level prior (sign zone)
 
Usage:
  python bayesian_fusion.py [--p-rfid-det F] [--p-rfid-fp F]
                             [--p-vis-det F]  [--p-vis-fp F]
                             [--prior F]
"""
 
import argparse
 
# ── Default parameters (paper values) ────────────────────────────────────────
P_RFID_DET_DEFAULT  = 1.00   # P(R=1 | H)  — RFID detection rate
P_RFID_FP_DEFAULT   = 0.00   # P(R=1 | ¬H) — RFID false positive rate
P_VIS_DET_DEFAULT   = 0.85   # P(V=1 | H)  — Vision detection rate
P_VIS_FP_DEFAULT    = 0.05   # P(V=1 | ¬H) — Vision false positive rate
P_PRIOR_DEFAULT     = 0.70   # P(H)         — Map-level prior
 
# ── Bayesian model ────────────────────────────────────────────────────────────
def posterior(
    rfid: int, vis: int,
    p_rfid_det: float, p_rfid_fp: float,
    p_vis_det:  float, p_vis_fp:  float,
    prior:      float,
) -> float | None:
    """
    Compute P(H | R=rfid, V=vis) using Bayes' theorem.
    Returns None for the type-conflict state (not computable by this model).
    """
    p_h  = prior
    p_nh = 1.0 - prior
 
    # P(R | H) and P(R | ¬H)
    p_r_h  = p_rfid_det if rfid else (1.0 - p_rfid_det)
    p_r_nh = p_rfid_fp  if rfid else (1.0 - p_rfid_fp)
 
    # P(V | H) and P(V | ¬H)
    p_v_h  = p_vis_det if vis else (1.0 - p_vis_det)
    p_v_nh = p_vis_fp  if vis else (1.0 - p_vis_fp)
 
    # Joint likelihoods (conditional independence)
    p_e_h  = p_r_h  * p_v_h
    p_e_nh = p_r_nh * p_v_nh
 
    # Marginal evidence
    p_e = p_e_h * p_h + p_e_nh * p_nh
 
    if p_e < 1e-12:
        return None
 
    return (p_e_h * p_h) / p_e
 
 
def confidence_label(p: float | None) -> str:
    if p is None:
        return "Conflict"
    if p >= 0.90:
        return "High"
    if p >= 0.65:
        return "Medium-high" if p >= 0.78 else "Medium"
    return "Low"
 
 
def action_label(p: float | None, state: str) -> str:
    if state == "type_conflict":
        return "Most restrictive rule"
    if p >= 0.90:
        return "Proceed normally"
    if p >= 0.65:
        return "Comply + alert"
    if p >= 0.40:
        return "Reduce speed + alert"
    return "Check map prior"
 
 
# ── Print helpers ─────────────────────────────────────────────────────────────
SEP  = "─" * 80
SEP2 = "═" * 80
 
 
def section(title: str) -> None:
    print(f"\n{SEP2}")
    print(f"  {title}")
    print(SEP2)
 
 
def divider() -> None:
    print(f"  {SEP}")
 
 
# ── Table VII ─────────────────────────────────────────────────────────────────
def print_table_vii(params: dict) -> None:
    section("TABLE VII — Bayesian Posterior P(H|R,V) by Sensor State")
 
    states = [
        ("Full consensus",  1, 1,   "agreement"),
        ("RFID only",       1, 0,   "rfid_only"),
        ("Vision only",     0, 1,   "vis_only"),
        ("Neither detects", 0, 0,   "neither"),
        ("Type conflict",   "A","B","type_conflict"),
    ]
 
    print(
        f"  {'State':<20}  {'R':>4}  {'V':>4}  "
        f"{'P(H|R,V)':>10}  {'Confidence':>13}  "
        f"{'Vehicle action':<25}"
    )
    divider()
 
    results = {}
    for name, r, v, key in states:
        if key == "type_conflict":
            p = None
            p_str = "—"
            r_str, v_str = str(r), str(v)
        else:
            p = posterior(r, v, **params)
            p_str = f"{p:.2f}" if p is not None else "—"
            r_str = "✓" if r == 1 else "✗"
            v_str = "✓" if v == 1 else "✗"
 
        conf   = confidence_label(p)
        action = action_label(p, key)
        results[key] = p
 
        print(
            f"  {name:<20}  {r_str:>4}  {v_str:>4}  "
            f"  {p_str:>8}  {conf:>13}  "
            f"{action:<25}"
        )
 
    divider()
    print(f"\n  Parameters used:")
    print(f"    P(R=1|H)  = {params['p_rfid_det']:.2f}  "
          f"← Experimentally verified (100% detection, n=60 field approaches)")
    print(f"    P(R=1|¬H) = {params['p_rfid_fp']:.2f}  "
          f"← Zero false positives observed in all field sessions")
    print(f"    P(V=1|H)  = {params['p_vis_det']:.2f}  "
          f"← Literature: 0.85–0.96 under favorable conditions [1][5][6][16]")
    print(f"    P(V=1|¬H) = {params['p_vis_fp']:.2f}  "
          f"← Literature: 0.02–0.08 typical FPR")
    print(f"    P(H)      = {params['prior']:.2f}  "
          f"← Map-level prior (sign zone approach)")
 
    return results
 
 
# ── Sensitivity analysis ──────────────────────────────────────────────────────
def print_sensitivity(base_params: dict) -> None:
    section("Sensitivity Analysis — Effect of Parameter Variation on P(H|R,V)")
 
    print(f"  State: RFID only (R=1, V=0) — most critical case for safety\n")
    print(f"  {'P_vis_det':>10}  {'P_vis_fp':>9}  {'Prior P(H)':>11}  "
          f"{'P(H|R=1,V=0)':>14}  {'Confidence':>13}")
    divider()
 
    for pv_det in [0.75, 0.85, 0.95]:
        for pv_fp in [0.02, 0.05, 0.10]:
            for prior in [0.50, 0.70, 0.90]:
                p = posterior(
                    1, 0,
                    base_params["p_rfid_det"],
                    base_params["p_rfid_fp"],
                    pv_det, pv_fp, prior
                )
                print(
                    f"  {pv_det:>10.2f}  {pv_fp:>9.2f}  {prior:>11.2f}  "
                    f"  {p:>12.3f}  {confidence_label(p):>13}"
                )
    divider()
    print("  RFID false positive rate = 0.00 in all rows (experimentally verified).")
    print("  Posterior at R=1 is robust to vision parameter uncertainty.")
 
 
# ── Asymmetry explanation ─────────────────────────────────────────────────────
def print_asymmetry(results: dict) -> None:
    section("Key Result: Sensor Asymmetry")
    p_rfid = results.get("rfid_only")
    p_vis  = results.get("vis_only")
    if p_rfid is not None and p_vis is not None:
        diff = p_rfid - p_vis
        print(f"\n  P(H | RFID only) = {p_rfid:.3f}")
        print(f"  P(H | Vision only) = {p_vis:.3f}")
        print(f"  Difference = {diff:+.3f}  (RFID evidence is stronger)")
        print(f"\n  Interpretation:")
        print(f"  When RFID detects a sign that the camera misses (e.g. weathered,")
        print(f"  occluded, or poorly lit), the posterior ({p_rfid:.2f}) still exceeds")
        print(f"  0.75, providing sufficient confidence for regulatory compliance.")
        print(f"  This asymmetry follows directly from P(R=1|¬H) ≈ 0:")
        print(f"  an RFID detection is effectively a false-positive-free event.")
        print(f"\n  When vision detects but RFID misses ({p_vis:.2f}), the lower")
        print(f"  confidence reflects the non-zero vision FPR under degraded")
        print(f"  conditions. This quantitatively justifies treating RFID")
        print(f"  detections as higher-quality evidence than vision-only detections.")
 
 
# ── Five-state decision table ─────────────────────────────────────────────────
def print_decision_table(results: dict) -> None:
    section("Five-State Decision Framework and Vehicle Action Mapping")
 
    thresholds = [
        ("P ≥ 0.90", "Normal sign compliance — proceed at speed"),
        ("0.65 ≤ P < 0.90", "Cautious compliance — alert driver, moderate deceleration"),
        ("0.40 ≤ P < 0.65", "Precautionary — reduce speed, prepare to stop"),
        ("P < 0.40", "Minimal-risk condition — decelerate, await confirmation"),
        ("Type conflict", "Apply most restrictive sign type (STOP priority 1)"),
    ]
 
    for thresh, action in thresholds:
        print(f"  {thresh:<22}  →  {action}")
 
    divider()
    print("  Priority ordering (from system implementation):")
    print("    1 = STOP SIGN  >  2 = PEDESTRIAN CROSSING  >  3 = SPEED LIMIT")
    print("  This ordering extends from multi-tag arbitration (bench tests)")
    print("  to inter-sensor type-conflict resolution.")
 
 
# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reproduce Table VII — Bayesian Sensor Fusion Framework"
    )
    parser.add_argument("--p-rfid-det", type=float, default=P_RFID_DET_DEFAULT,
                        help=f"P(R=1|H)  RFID detection rate  (default: {P_RFID_DET_DEFAULT})")
    parser.add_argument("--p-rfid-fp",  type=float, default=P_RFID_FP_DEFAULT,
                        help=f"P(R=1|¬H) RFID false positive  (default: {P_RFID_FP_DEFAULT})")
    parser.add_argument("--p-vis-det",  type=float, default=P_VIS_DET_DEFAULT,
                        help=f"P(V=1|H)  Vision detection rate (default: {P_VIS_DET_DEFAULT})")
    parser.add_argument("--p-vis-fp",   type=float, default=P_VIS_FP_DEFAULT,
                        help=f"P(V=1|¬H) Vision false positive (default: {P_VIS_FP_DEFAULT})")
    parser.add_argument("--prior",      type=float, default=P_PRIOR_DEFAULT,
                        help=f"P(H) map-level prior            (default: {P_PRIOR_DEFAULT})")
    parser.add_argument("--sensitivity", action="store_true",
                        help="Print sensitivity analysis table")
    args = parser.parse_args()
 
    params = dict(
        p_rfid_det = args.p_rfid_det,
        p_rfid_fp  = args.p_rfid_fp,
        p_vis_det  = args.p_vis_det,
        p_vis_fp   = args.p_vis_fp,
        prior      = args.prior,
    )
 
    print(f"\n{'═'*80}")
    print("  RFID Traffic Sign Recognition — Bayesian Sensor Fusion Framework")
    print("  IEEE Latin America Transactions, 2026")
    print(f"{'═'*80}")
 
    results = print_table_vii(params)
    print_asymmetry(results)
    print_decision_table(results)
 
    if args.sensitivity:
        print_sensitivity(params)
 
    print(f"\n{'═'*80}\n")
 
 
if __name__ == "__main__":
    main()
