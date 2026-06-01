"""
aloha_dwell_analysis.py
========================
Reproduces Table V from:
  "Use of Radio Frequency Identifiers in Autonomous Mobility Systems:
   With a Focus on Safety"
  IEEE Latin America Transactions, 2026
 
Table reproduced:
  - Table V: Dwell Time and Detection Probability Analysis (Q=2)
 
Model:
  t_dwell    = d_recognition / v
  t_cycle    = 2^Q × t_slot                (EPCglobal C1G2 Slotted ALOHA)
  n_cycles   = floor(t_dwell / t_cycle)
  P_det      = [1 − (1 − 1/2^Q)^n_cycles] × min(t_dwell / T_poll, 1)
 
Usage:
  python aloha_dwell_analysis.py [--Q N] [--t-slot-ms MS] [--poll-ms MS]
"""
 
import argparse
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os
 
# ── System parameters ────────────────────────────────────────────────────────
Q_DEFAULT      = 2        # EPCglobal C1G2 Q-factor (slots = 2^Q)
T_SLOT_MS      = 3.0      # ms — slot duration (C1G2 specification)
T_POLL_MS      = 500.0    # ms — software polling interval
 
D_MEAN_M       = 8.17     # m — mean field recognition distance
D_MIN_M        = 3.0      # m — minimum observed (sign 6, curved)
 
SPEEDS_KMH     = [10, 20, 30, 40, 60]
 
# ── Core model ───────────────────────────────────────────────────────────────
def t_cycle_ms(Q: int, t_slot_ms: float = T_SLOT_MS) -> float:
    """Duration of one Slotted ALOHA inventory cycle [ms]."""
    return (2 ** Q) * t_slot_ms
 
 
def t_dwell_ms(d_m: float, v_kmh: float) -> float:
    """Time a tag remains within detection envelope [ms]."""
    v_ms = v_kmh / 3.6
    return (d_m / v_ms) * 1000.0
 
 
def n_cycles(d_m: float, v_kmh: float, Q: int,
             t_slot_ms: float = T_SLOT_MS) -> int:
    """Number of complete ALOHA inventory cycles during dwell window."""
    td = t_dwell_ms(d_m, v_kmh)
    tc = t_cycle_ms(Q, t_slot_ms)
    return int(td / tc)
 
 
def p_per_cycle(Q: int) -> float:
    """Probability of successful read in one inventory cycle (1 tag)."""
    return 1.0 / (2 ** Q)
 
 
def p_detection(d_m: float, v_kmh: float, Q: int,
                t_slot_ms: float = T_SLOT_MS,
                t_poll_ms: float = T_POLL_MS) -> float:
    """
    Compound detection probability accounting for:
      (1) ALOHA success across n_cycles
      (2) Polling window alignment probability
    """
    td  = t_dwell_ms(d_m, v_kmh)
    nc  = n_cycles(d_m, v_kmh, Q, t_slot_ms)
    ppc = p_per_cycle(Q)
 
    # ALOHA probability: at least one successful read in nc cycles
    if nc <= 0:
        p_aloha = ppc  # one partial cycle
    else:
        p_aloha = 1.0 - (1.0 - ppc) ** nc
 
    # Polling window: probability that polling trigger fires within dwell
    p_poll = min(td / t_poll_ms, 1.0)
 
    return p_aloha * p_poll
 
 
def format_prob(p: float) -> str:
    """Format probability as percentage with threshold labels."""
    if p >= 0.999:
        return ">99.9%"
    if p <= 0.005:
        return "<0.5%"
    return f"{p*100:.1f}%"
 
 
def dwell_ok(d_m: float, v_kmh: float, t_poll_ms: float = T_POLL_MS) -> bool:
    return t_dwell_ms(d_m, v_kmh) >= t_poll_ms
 
 
# ── Print helpers ────────────────────────────────────────────────────────────
SEP  = "─" * 108
SEP2 = "═" * 108
 
 
def section(title: str) -> None:
    print(f"\n{SEP2}")
    print(f"  {title}")
    print(SEP2)
 
 
def divider() -> None:
    print(f"  {SEP}")
 
 
# ── Table V ──────────────────────────────────────────────────────────────────
def print_table_v(Q: int, t_slot: float, t_poll: float) -> None:
    tc = t_cycle_ms(Q, t_slot)
    n_slots = 2 ** Q
    section(
        f"TABLE V — Dwell Time and Detection Probability Analysis  "
        f"[Q={Q} | {n_slots} slots | t_cycle={tc:.0f} ms | T_poll={t_poll:.0f} ms]"
    )
    print(
        f"  {'Speed':>8}  "
        f"{'t_dwell':>14}  "
        f"{'t_dwell':>14}  "
        f"{'Dwell>poll?':>11}  "
        f"{'Cycles':>7}  "
        f"{'Cycles':>7}  "
        f"{'P_det':>10}  "
        f"{'P_det':>10}"
    )
    print(
        f"  {'':>8}  "
        f"{'(d=8.17 m)':>14}  "
        f"{'(d=3.0 m)':>14}  "
        f"{'':>11}  "
        f"{'(d=8 m)':>7}  "
        f"{'(d=3 m)':>7}  "
        f"{'(d=8 m)':>10}  "
        f"{'(d=3 m)':>10}"
    )
    divider()
 
    for v in SPEEDS_KMH:
        td_mean   = t_dwell_ms(D_MEAN_M, v)
        td_min    = t_dwell_ms(D_MIN_M,  v)
        ok_mean   = td_mean >= t_poll
        ok_min    = td_min  >= t_poll
 
        if ok_mean and ok_min:
            poll_label = "Both ✓"
        elif ok_mean:
            poll_label = "d=8 m only"
        else:
            poll_label = "Neither ✗"
 
        nc_mean = n_cycles(D_MEAN_M, v, Q, t_slot)
        nc_min  = n_cycles(D_MIN_M,  v, Q, t_slot)
 
        pd_mean = p_detection(D_MEAN_M, v, Q, t_slot, t_poll)
        pd_min  = p_detection(D_MIN_M,  v, Q, t_slot, t_poll)
 
        pd_min_note = format_prob(pd_min)
        if not ok_min:
            pd_min_note += "*"
 
        print(
            f"  {v:>5} km/h  "
            f"  {td_mean:>9.0f} ms  "
            f"  {td_min:>9.0f} ms  "
            f"  {poll_label:>11}  "
            f"  {nc_mean:>5}  "
            f"  {nc_min:>5}  "
            f"  {format_prob(pd_mean):>10}  "
            f"  {pd_min_note:>10}"
        )
 
    divider()
    print(f"  * Includes polling window risk — t_dwell < T_poll = {t_poll:.0f} ms")
    print(f"    Tag may traverse detection zone between consecutive polling triggers.")
    print(f"\n  Equations:")
    print(f"    t_dwell = d / v")
    print(f"    t_cycle = 2^Q × t_slot = {n_slots} × {t_slot:.0f} ms = {tc:.0f} ms")
    print(f"    n_cycles = ⌊t_dwell / t_cycle⌋")
    print(f"    P_det = [1 − (1 − 1/2^Q)^n_cycles] × min(t_dwell / T_poll, 1)")
 
 
# ── Protocol detail ──────────────────────────────────────────────────────────
def print_protocol_detail(Q: int, t_slot: float, t_poll: float) -> None:
    section("EPCglobal C1G2 Slotted ALOHA — Protocol Parameters")
    tc = t_cycle_ms(Q, t_slot)
    ppc = p_per_cycle(Q)
 
    rows = [
        ("Q-factor",                            f"{Q}"),
        ("Number of slots per cycle (2^Q)",      f"{2**Q}"),
        ("Slot duration",                        f"{t_slot:.1f} ms"),
        ("Inventory cycle duration (t_cycle)",   f"{tc:.1f} ms"),
        ("Per-cycle detection probability",      f"{ppc:.3f}  ({ppc*100:.1f}%)"),
        ("Software polling interval (T_poll)",   f"{t_poll:.0f} ms"),
        ("Max cycles per poll interval",         f"{int(t_poll / tc)}"),
    ]
    for lbl, val in rows:
        print(f"  {lbl:<42} {val}")
 
    divider()
    print("  Two failure mechanisms are distinguished:")
    print("    (1) ALOHA packet loss — tag in range but ALOHA cycle fails")
    print("        → Probability of miss per cycle = (1 − 1/2^Q) = "
          f"{(1 - ppc):.3f}")
    print("    (2) Polling-window miss — tag traverses detection zone")
    print("        between two consecutive polling triggers (t_dwell < T_poll)")
    print("        → Occurs for d=3.0 m at v ≥ 30 km/h")
 
 
# ── Mitigation analysis ───────────────────────────────────────────────────────
def print_mitigation(Q: int, t_slot: float) -> None:
    section("Mitigation: Effect of Reducing Polling Interval")
    print(f"  Current:   T_poll = {T_POLL_MS:.0f} ms")
    print(f"  Proposed:  T_poll = 50–100 ms (software change, no hardware required)\n")
 
    for t_poll_new in [500.0, 200.0, 100.0, 50.0]:
        print(f"  T_poll = {t_poll_new:>5.0f} ms:")
        for v in [40, 60]:
            for d, d_label in [(D_MEAN_M, "d=8.17 m"), (D_MIN_M, "d=3.0 m")]:
                td = t_dwell_ms(d, v)
                pd = p_detection(d, v, Q, t_slot, t_poll_new)
                ok = "✓" if td >= t_poll_new else "✗"
                print(
                    f"    v={v:>2} km/h  {d_label}  "
                    f"t_dwell={td:.0f} ms  dwell>poll:{ok}  "
                    f"P_det={format_prob(pd)}"
                )
        print()
    print("  Conclusion: T_poll = 100 ms resolves vulnerability for all")
    print("  observed recognition distances at speeds ≤ 60 km/h.")
 
 
# ── Plot ──────────────────────────────────────────────────────────────────────
def save_plot(Q: int, t_slot: float, t_poll: float, out_dir: str) -> None:
    speeds = np.linspace(1, 80, 300)
    pd_mean = [p_detection(D_MEAN_M, v, Q, t_slot, t_poll) * 100 for v in speeds]
    pd_min  = [p_detection(D_MIN_M,  v, Q, t_slot, t_poll) * 100 for v in speeds]
 
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(speeds, pd_mean, color="#1D9E75", lw=2, label=f"d = {D_MEAN_M} m (mean)")
    ax.plot(speeds, pd_min,  color="#E24B4A", lw=2, label=f"d = {D_MIN_M} m (min)")
    ax.axhline(99, color="#888780", lw=1, ls="--", label="99% threshold")
    ax.axvline(40, color="#EF9F27", lw=1, ls=":", label="40 km/h (max tested)")
    ax.fill_between(speeds, 0, pd_mean, alpha=0.08, color="#1D9E75")
    ax.fill_between(speeds, 0, pd_min,  alpha=0.08, color="#E24B4A")
    ax.set_xlabel("Vehicle speed (km/h)", fontsize=11)
    ax.set_ylabel("P(detection) (%)", fontsize=11)
    ax.set_title(f"ALOHA Detection Probability vs Speed  [Q={Q}, T_poll={t_poll:.0f} ms]",
                 fontsize=11)
    ax.legend(fontsize=9)
    ax.set_xlim(0, 80)
    ax.set_ylim(0, 105)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    path = os.path.join(out_dir, "fig_aloha_detection_probability.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Plot saved: {path}")
 
 
# ── Main ─────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reproduce Table V — Dwell Time and ALOHA Analysis"
    )
    parser.add_argument("--Q",          type=int,   default=Q_DEFAULT,
                        help=f"ALOHA Q-factor (default: {Q_DEFAULT})")
    parser.add_argument("--t-slot-ms",  type=float, default=T_SLOT_MS,
                        help=f"Slot duration in ms (default: {T_SLOT_MS})")
    parser.add_argument("--poll-ms",    type=float, default=T_POLL_MS,
                        help=f"Polling interval in ms (default: {T_POLL_MS})")
    parser.add_argument("--plot",       action="store_true",
                        help="Save detection probability plot as PNG")
    parser.add_argument("--out-dir",    default=".",
                        help="Output directory for plot (default: .)")
    args = parser.parse_args()
 
    print(f"\n{'═'*108}")
    print("  RFID Traffic Sign Recognition — Dwell Time and ALOHA Analysis")
    print("  IEEE Latin America Transactions, 2026")
    print(f"{'═'*108}")
 
    print_protocol_detail(args.Q, args.t_slot_ms, args.poll_ms)
    print_table_v(args.Q, args.t_slot_ms, args.poll_ms)
    print_mitigation(args.Q, args.t_slot_ms)
 
    if args.plot:
        save_plot(args.Q, args.t_slot_ms, args.poll_ms, args.out_dir)
 
    print(f"\n{'═'*108}\n")
 
 
if __name__ == "__main__":
    main()
