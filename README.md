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
This work proposes and experimentally evaluates the use of UHF RFID technology as a redundant perception layer for traffic sign identification in autonomous mobility systems. Passive UHF RFID tags are integrated into traffic signs and detected using a vehicle-mounted reader system. Results include a safety margin analysis, Bayesian sensor fusion framework, dwell time and Slotted ALOHA protocol analysis, and a simplified FMEA. 
 
## Hardware Requirements 
- Viaonda MID 12-iETH UHF RFID reader antenna (902–928 MHz, 12 dBi, 42° beamwidth) 
- Passive UHF RFID tags — Control ID ABS IP68 
- Raspberry Pi 3B+ or higher (Linux OS) 
- Python 3.8+ 

## Repository Contents 
### `/data/` 
- `bench_test_raw.csv` — 120 recognition distance measurements under controlled conditions (columns: approach_id, distance_m, tag_id, orientation) 
- `field_test_raw.csv` — 60 measurements from campus field tests (columns: sign_id, pass_id, distance_m, lateral_offset_m, speed_kmh, segment_type) 
- `field_test_summary.csv` — Per-sign mean distance and offset (Table II in paper) 
- `read_rate_by_speed.csv` — Read rate observations at 10, 20, 40 km/h (Table IV) 

### `/scripts/` 
- `rfid_reader.py` — Main acquisition loop. Connects to reader via TCP/IP, implements 500 ms polling interval, decodes EPC codes, triggers GPIO outputs. 
  **Run on Raspberry Pi with reader connected to local network.** 
- `gui_interface.py` — Real-time graphical interface (Python + Tkinter). Displays sign image, priority level, sign name, and EPC code. 
- `gpio_output.py` — Configures GPIO pins 18 (STOP), 23 (PED. CROSSING), 24 (20 km/h).
- `statistical_analysis.py` — Reproduces Tables I and III: mean, SD, 95% CI, Shapiro-Wilk normality test, Pearson correlation. 
- `safety_margin_analysis.py` — Reproduces Table VI: stopping distance for each speed and deceleration level. 
- `aloha_dwell_analysis.py` — Reproduces Table V: dwell time model and compound detection probability. 
- `bayesian_fusion.py` — Reproduces Table VII: Bayesian posterior for all sensor state combinations. 
- `fmea_table.py` — Reproduces Table VIII: FMEA with RPN values. 

## Installation 
```bash 
git clone [https://github.com/[USERNAME]/rfid-autonomous-mobility ](https://github.com/MarcosAJCoelho/RFIDAutonomousMobility)
cd rfid-autonomous-mobility 
pip install -r requirements.txt 
``` 

## Reproducing Paper Results 

```bash 
# Statistical analysis (Tables I and III) 
python scripts/statistical_analysis.py 
# Safety margin analysis (Table VI) 
python scripts/safety_margin_analysis.py 
# ALOHA dwell time analysis (Table V) 
python scripts/aloha_dwell_analysis.py 
# Bayesian fusion model (Table VII) 
python scripts/bayesian_fusion.py 
# FMEA table (Table VIII) 
python scripts/fmea_table.py 
``` 
## License 
This code is released under the MIT License. See LICENSE for details. 

## Acknowledgments 
This study was financed in part by the Fundação de Amparo à Pesquisa e Inovação do Estado de Santa Catarina (FAPESC) — FAPESC 21/2024. 

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
