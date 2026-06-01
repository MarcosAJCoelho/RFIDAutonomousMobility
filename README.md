# Use of Radio Frequency Identifiers in Autonomous Mobility Systems: With a Focus on Safety 
**IEEE Latin America Transactions** | Submission ID: 10693 | Year: 2026 

## Authors 
| Author | Affiliation | Email | 
|--------|------------|-------| 
| João Mota Neto | Centro Universitário UniSATC, Criciúma, SC, Brazil | joao.neto@satc.edu.br | 
| Marcos Antônio Jeremias Coelho | Centro Universitário UniSATC, Criciúma, SC, Brazil | marcos.coelho@satc.edu.br | 
| Gabriela Rocha Roque | Centro Universitário UniSATC, Criciúma, SC, Brazil | gabriela.roque@satc.edu.br | 
| Roderval Marcelino | UFSC, Araranguá, SC, Brazil | roderval.marcelino@ufsc.br | 

## Abstract 
This work proposes and experimentally evaluates the use of UHF Radio Frequency Identification (RFID) technology as a redundant perception layer for traffic sign identification in autonomous mobility systems. Passive UHF RFID tags were integrated into traffic signs and detected using a vehicle-mounted reader system. The experimental evaluation was conducted in two stages: controlled bench tests and field tests on a real university campus environment.

Key contributions:
-Quantitative experimental characterization of RFID-based traffic sign recognition under dynamic and geometric constraints
-Safety margin analysis combining recognition distance, latency, and vehicle dynamics
-Bayesian sensor fusion framework parametrized from experimental data
-Dwell time and Slotted ALOHA protocol analysis under vehicular speeds
-Simplified Failure Mode and Effects Analysis (FMEA)

<img width="1961" height="784" alt="RFID" src="https://github.com/user-attachments/assets/81f060b6-618a-40d4-b54e-a10ea66c3e7f" />


 
## Hardware Requirements 
| Component | Model | Specifications | 
|--------|------------|-------| 
| UHF RFID Reader/Antenna | Viaonda MID 12-iETH | 902–928 MHz, 12 dBi gain, 42° beamwidth, TCP/IP
| RFID Tags | Control ID ABS IP68 | Passive UHF, metallic surface, −30 °C to 80 °C
| Processing unit | Raspberry Pi 3B+ | Linux OS, Python 3.8+, RPi.GPIO
| Test vehicle | Standard passenger car | Custom antenna mounting bracket


## Repository Structure

```
rfid-autonomous-mobility/
│
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── LICENSE                            # MIT License
│
├── data/
│   ├── bench_test_raw.csv             # 120 recognition distance measurements (bench)
│   ├── field_test_raw.csv             # 60 measurements — 12 signs × 5 passes at 10 km/h
│   ├── field_test_summary.csv         # Per-sign mean distance and lateral offset (Table II)
│   └── read_rate_by_speed.csv         # Read rate at 10, 20 and 40 km/h (Table IV)
│
├── scripts/
│   ├── rfid_reader.py                 # Main RFID acquisition loop (500 ms polling, TCP/IP)
│   ├── gui_interface.py               # Real-time graphical interface (Tkinter)
│   ├── gpio_output.py                 # Raspberry Pi GPIO activation (pins 18, 23, 24)
│   ├── statistical_analysis.py        # CI, Shapiro-Wilk, Pearson correlation (Tables I, III)
│   ├── safety_margin_analysis.py      # Stopping distance analysis (Table VI)
│   ├── aloha_dwell_analysis.py        # Dwell time and ALOHA model (Table V)
│   ├── bayesian_fusion.py             # Bayesian posterior calculations (Table VII)
│   └── fmea_table.py                  # FMEA with RPN values (Table VIII)
│
└── figures/
    ├── fig07_antenna_coverage.py      # Generates Fig. 7 — antenna coverage diagram
    └── fig11_fusion_architecture/     # Source files for Fig. 11 — fusion architecture
        ├── fusion_architecture.svg
        └── fusion_architecture.png
```

---

## File Descriptions

### `/data/bench_test_raw.csv`
Contains the 120 recognition distance measurements collected during controlled bench tests. Each row represents a single tag approach.

| Column | Description |
|--------|-------------|
| `approach_id` | Sequential identifier (1–120) |
| `distance_m` | Recognition distance in meters |
| `tag_id` | Tag EPC identifier |
| `orientation` | Tag orientation relative to antenna (frontal) |

### `/data/field_test_raw.csv`
Contains the 60 recognition distance measurements from campus field experiments (12 signs × 5 repetitions each at 10 km/h).

| Column | Description |
|--------|-------------|
| `sign_id` | Sign number (1–12, corresponding to Table II) |
| `pass_id` | Repetition number (1–5) |
| `distance_m` | Recognition distance in meters |
| `lateral_offset_m` | Sign lateral offset from vehicle trajectory in meters |
| `speed_kmh` | Vehicle speed during approach (10 km/h for all quantitative runs) |
| `segment_type` | Road segment type: `straight` or `curved` |

### `/data/field_test_summary.csv`
Per-sign summary used for Table II and Pearson correlation analysis (r = −0.87, p < 0.001).

### `/data/read_rate_by_speed.csv`
Read rate observations at 10, 20 and 40 km/h from Table IV. Qualitative runs at 20 and 40 km/h are marked accordingly.

### `/scripts/rfid_reader.py`
Main acquisition script. Connects to the Viaonda reader via TCP/IP, implements the 500 ms polling interval, decodes EPC codes, maps them to sign categories, and triggers the corresponding GPIO digital outputs.

**Run on Raspberry Pi with reader connected to local network:**
```bash
python scripts/rfid_reader.py --ip 192.168.1.100 --port 5000
```

### `/scripts/gui_interface.py`
Real-time graphical user interface. Displays the sign image, priority level (1–3), sign type name, and EPC code for each active detection. Built with Python Tkinter.

```bash
python scripts/gui_interface.py
```

### `/scripts/gpio_output.py`
Configures Raspberry Pi GPIO outputs:
- GPIO Pin 18 → STOP SIGN
- GPIO Pin 23 → PEDESTRIAN CROSSING
- GPIO Pin 24 → 20 km/h SPEED LIMIT

### `/scripts/statistical_analysis.py`
Reproduces all statistical results in Tables I and III:
- Mean, standard deviation, 95% confidence interval (Student's t-distribution)
- Shapiro-Wilk normality test (W = 0.94, p = 0.07)
- Pearson correlation between recognition distance and lateral offset (r = −0.87, p < 0.001)

```bash
python scripts/statistical_analysis.py
```

### `/scripts/safety_margin_analysis.py`
Reproduces Table VI. Computes:
- Distance traveled during 500 ms latency at each speed
- Kinematic braking distance for a = 6 m/s² and a = 8 m/s²
- Total required stopping distance
- Probabilistic safety guarantee P(safe|v) from normal distribution

```bash
python scripts/safety_margin_analysis.py
```

### `/scripts/aloha_dwell_analysis.py`
Reproduces Table V. Implements the dwell time model and compound detection probability:
- `t_dwell = d_recognition / v`
- `n_cycles = floor(t_dwell / t_cycle)` with `t_cycle = 12 ms` (Q=2)
- `P(detection) = [1 − (1 − 1/2^Q)^n_cycles] × min(t_dwell / T_poll, 1)`

```bash
python scripts/aloha_dwell_analysis.py
```

### `/scripts/bayesian_fusion.py`
Reproduces Table VII. Computes Bayesian posterior P(H|R,V) for all four sensor state combinations using parameters derived from experimental data:
- `P(R=1|H) = 1.0`, `P(R=1|¬H) = 0.0` (from field test false positive rate)
- `P(V=1|H) = 0.85`, `P(V=1|¬H) = 0.05` (from literature)
- `P(H) = 0.70` (map prior)

```bash
python scripts/bayesian_fusion.py
```

### `/scripts/fmea_table.py`
Reproduces Table VIII. Computes Risk Priority Number (RPN = S × O × D) for the six identified failure modes and generates a formatted summary.

```bash
python scripts/fmea_table.py
```

---

## Installation

```bash
git clone https://github.com/[USERNAME]/rfid-autonomous-mobility
cd rfid-autonomous-mobility
pip install -r requirements.txt
```

### `requirements.txt`
```
numpy>=1.21.0
scipy>=1.7.0
pandas>=1.3.0
matplotlib>=3.4.0
RPi.GPIO>=0.7.0    # Raspberry Pi only — omit on other platforms
tkinter            # Usually included with Python
```

---

## Reproducing All Paper Results

```bash
# Tables I and III — statistical analysis
python scripts/statistical_analysis.py

# Table V — dwell time and ALOHA protocol analysis
python scripts/aloha_dwell_analysis.py

# Table VI — safety margin analysis
python scripts/safety_margin_analysis.py

# Table VII — Bayesian fusion framework
python scripts/bayesian_fusion.py

# Table VIII — FMEA
python scripts/fmea_table.py

# Fig. 7 — antenna coverage diagram
python figures/fig07_antenna_coverage.py
```

---

## Experimental Setup Summary

- **Bench tests:** 120 controlled tag approaches, frontal alignment, laboratory environment
- **Field tests:** 12 tagged signs, UniSATC campus route (~800 m), 5 repetitions per sign at 10 km/h
- **Dynamic runs:** qualitative passes at 20 km/h and 40 km/h (read rate documented, distance not measured)
- **Key results:** Mean recognition distance 8.17 m (field), 10.35 m (bench); zero false positives across all sessions

---

## Acknowledgments

This study was financed in part by the **Fundação de Amparo à Pesquisa e Inovação do Estado de Santa Catarina (FAPESC)** — FAPESC 21/2024.

---

## Citation
```bibtex 
@article{mota2026rfid, 
  author  = {Mota Neto, João and Coelho, Marcos Antônio Jeremias and 
             Roque, Gabriela Rocha and Marcelino, Roderval}, 
  title   = {Use of Radio Frequency Identifiers in Autonomous Mobility 
             Systems: With a Focus on Safety}, 
  journal = {IEEE Latin America Transactions}, 
  year    = {2026}, 
  doi     = {[DOI when assigned]} 
} 

``` 
