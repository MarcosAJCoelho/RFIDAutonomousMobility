"""
safety_margin_analysis.py
==========================
Reproduces Table VI from:
  "Use of Radio Frequency Identifiers in Autonomous Mobility Systems:
   With a Focus on Safety"
  IEEE Latin America Transactions, 2026
 
Table reproduced:
  - Table VI: Safety Margin Analysis
    (stopping distance vs mean field recognition distance across speeds)
 
Additional outputs:
  - Probabilistic safety guarantees P(safe | v) from the normal distribution
    of field recognition distances
  - Worst-case analysis: P01 and P05 recognition distance percentiles
  - Maximum safe operating speed for direct braking actuation
 
Usage:
  python safety_margin_analysis.py [--poll-ms MS] [--decel-a1 A] [--decel-a2 A]
"""
 
import argparse
import sys
from scipy import stats
import numpy as np
 
# ── System parameters ────────────────────────────────────────────────────────
MU_FIELD   = 8.167   # m  — mean field recognition distance
SIGMA_FIELD = 2.906  # m  — SD  field recognition distances
T_POLL_S   = 0.500   # s  — polling interval (deterministic latency bound)
 
# Deceleration levels
A_STD  = 6.0   # m/s² — standard emergency braking
A_ABS  = 8.0   # m/s² — ABS-assisted braking (dry asphalt)
 
# Test speeds
SPEEDS_KMH = [10, 20, 30, 40, 60]
 
# ── Helpers ──────────────────────────────────────────────────────────────────
SEP  = "─" * 90
SEP2 = "═" * 90
 
def kmh_to_ms(v_kmh: float) -> float:
    return v_kmh / 3.6
 
def d_lat(v_kmh: float, t_poll: float = T_POLL_S) -> float:
    """Distance traveled during detection latency."""
    return kmh_to_ms(v_kmh) * t_poll
 
def d_brake(v_kmh: float, a: float) -> float:
    """Kinematic braking distance."""
    v = kmh_to_ms(v_kmh)
    return (v ** 2) / (2 * a)
 
def d_total(v_kmh: float, a: float, t_poll: float = T_POLL_S) -> float:
    """Total minimum stopping distance."""
    return d_lat(v_kmh, t_poll) + d_brake(v_kmh, a)
 
def p_safe(v_kmh: float, a: float, mu: float = MU_FIELD,
           sigma: float = SIGMA_FIELD, t_poll: float = T_POLL_S) -> float:
    """
    Probability that a random recognition distance provides sufficient
    stopping margin:  P(d_rec > d_lat + d_brake)
    """
    d_req = d_total(v_kmh, a, t_poll)
    z = (d_req - mu) / sigma
    return 1.0 - stats.norm.cdf(z)
 
def adequacy_label(v_kmh: float, mu: float = MU_FIELD,
                   a1: float = A_STD, a2: float = A_ABS) -> str:
    """Text label based on worst-case (standard braking)."""
    d = d_total(v_kmh, a1)
    if d <= mu * 0.65:
        return "Yes"
    elif d <= mu:
        return "Marginal"
    else:
        return "No"
 
def section(title: str) -> None:
    print(f"\n{SEP2}")
    print(f"  {title}")
    print(SEP2)
 
def divider() -> None:
    print(f"  {SEP}")
 
# ── Print Table VI ────────────────────────────────────────────────────────────
def print_table_vi(t_poll: float, a1: float, a2: float) -> None:
    section(
        f"TABLE VI — Safety Margin Analysis  "
        f"[T_poll={t_poll*1000:.0f} ms | a₁={a1} m/s² | a₂={a2} m/s²]"
    )
    hdr = (f"  {'Speed':>8}  {'d_lat':>8}  {'d_brake a₁':>11}  "
           f"{'d_brake a₂':>11}  {'d_total a₁':>11}  "
           f"{'d_total a₂':>11}  {'d_recog μ':>10}  {'Adequate?':>10}")
    print(hdr)
    divider()
 
    for v in SPEEDS_KMH:
        dl   = d_lat(v, t_poll)
        db1  = d_brake(v, a1)
        db2  = d_brake(v, a2)
        dt1  = dl + db1
        dt2  = dl + db2
        label = adequacy_label(v, MU_FIELD, a1, a2)
        print(
            f"  {v:>5} km/h"
            f"  {dl:>7.2f} m"
            f"  {db1:>10.2f} m"
            f"  {db2:>10.2f} m"
            f"  {dt1:>10.2f} m"
            f"  {dt2:>10.2f} m"
            f"  {MU_FIELD:>9.2f} m"
            f"  {label:>10}"
        )
    divider()
    print(f"  μ_field = {MU_FIELD} m  |  "
          f"d_lat = v × T_poll  |  d_brake = v²/(2a)  |  d_total = d_lat + d_brake")
 
 
# ── Probabilistic safety guarantees ─────────────────────────────────────────
def print_probabilistic(t_poll: float, a1: float, a2: float) -> None:
    section("Probabilistic Safety Guarantees  P(safe | v) — Equation (4)")
    print(f"  P(safe|v) = P(d_rec > d_lat + d_brake) = 1 − Φ((d_total(v) − μ) / σ)")
    print(f"  μ = {MU_FIELD} m  |  σ = {SIGMA_FIELD} m  |  T_poll = {t_poll*1000:.0f} ms\n")
    print(f"  {'Speed':>8}  {'d_total a₁':>11}  {'P_safe a₁':>11}  "
          f"{'d_total a₂':>11}  {'P_safe a₂':>11}  {'Assessment':>22}")
    divider()
 
    for v in SPEEDS_KMH:
        dt1 = d_total(v, a1, t_poll)
        dt2 = d_total(v, a2, t_poll)
        ps1 = p_safe(v, a1, t_poll=t_poll)
        ps2 = p_safe(v, a2, t_poll=t_poll)
 
        if ps2 >= 0.95:
            assess = "Adequate for direct actuation"
        elif ps1 >= 0.90:
            assess = "Marginal — limited conditions only"
        elif ps1 >= 0.50:
            assess = "Insufficient — use as pre-alert only"
        else:
            assess = "Cannot support direct braking"
 
        print(
            f"  {v:>5} km/h"
            f"  {dt1:>10.2f} m"
            f"  {ps1:>10.1%}"
            f"  {dt2:>10.2f} m"
            f"  {ps2:>10.1%}"
            f"  {assess:>22}"
        )
 
    divider()
    print(f"\n  Published values (paper, a=6 m/s²):")
    print(f"    P(safe|10 km/h) = 98.3%   P(safe|20 km/h) = 92.7%")
    print(f"    P(safe|30 km/h) = 27.1%   P(safe|40 km/h) < 2%")
 
 
# ── Worst-case bounds ────────────────────────────────────────────────────────
def print_worst_case() -> None:
    section("Worst-Case Recognition Distance Bounds")
    print(f"  d_rec(p) = μ + σ · Φ⁻¹(p)   [μ={MU_FIELD} m, σ={SIGMA_FIELD} m]\n")
    percentiles = [0.01, 0.05, 0.10, 0.25, 0.50]
    print(f"  {'Percentile':>12}  {'d_rec (m)':>12}  {'Notes'}")
    divider()
    for p in percentiles:
        d = MU_FIELD + SIGMA_FIELD * stats.norm.ppf(p)
        note = ""
        if p == 0.01:
            note = "← P01 lower bound (99% confidence)"
        elif p == 0.05:
            note = f"← P05; min observed = 3.0 m (consistent)"
        elif p == 0.50:
            note = "← median ≈ mean (symmetric distribution)"
        print(f"  {p:>11.0%}  {max(d, 0):>11.2f} m  {note}")
    divider()
    print(f"  Minimum observed (field):  3.0 m  (sign 6, curved, offset 1.5 m)")
    print(f"  Maximum observed (field): 12.0 m  (sign 1, offset 1.0 m)")
 
 
# ── Maximum safe speed ────────────────────────────────────────────────────────
def print_max_safe_speed(t_poll: float, a1: float, a2: float) -> None:
    section("Maximum Safe Operating Speed for Direct Braking Actuation")
    threshold = 0.90
    print(f"  Criterion: P(safe | v, a) ≥ {threshold:.0%}\n")
    for a, label in [(a1, f"Standard braking (a={a1} m/s²)"),
                     (a2, f"ABS braking      (a={a2} m/s²)")]:
        v_max = None
        for v in range(1, 101):
            if p_safe(v, a, t_poll=t_poll) < threshold:
                v_max = v - 1
                break
        print(f"  {label}:  v_max ≈ {v_max} km/h")
    divider()
    print(f"  Conclusion: above these speeds, RFID must operate as an")
    print(f"  anticipatory layer (pre-alert), not a direct braking trigger.")
 
 
# ── Main ─────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reproduce Table VI — Safety Margin Analysis"
    )
    parser.add_argument("--poll-ms",  type=float, default=500.0,
                        help="Polling interval in milliseconds (default: 500)")
    parser.add_argument("--decel-a1", type=float, default=A_STD,
                        help=f"Deceleration a1 in m/s² (default: {A_STD})")
    parser.add_argument("--decel-a2", type=float, default=A_ABS,
                        help=f"Deceleration a2 in m/s² (default: {A_ABS})")
    args = parser.parse_args()
 
    t_poll = args.poll_ms / 1000.0
 
    print(f"\n{'═'*90}")
    print("  RFID Traffic Sign Recognition — Safety Margin Analysis")
    print("  IEEE Latin America Transactions, 2026")
    print(f"{'═'*90}")
 
    print_table_vi(t_poll, args.decel_a1, args.decel_a2)
    print_probabilistic(t_poll, args.decel_a1, args.decel_a2)
    print_worst_case()
    print_max_safe_speed(t_poll, args.decel_a1, args.decel_a2)
 
    print(f"\n{'═'*90}\n")
 
 
if __name__ == "__main__":
    main()
