# CMOS Current-Steering Digital-to-Analog Converter (DAC)

**Course**: CMOS Mixed Signal VLSI Design (Sub Code: ECM 4444)  
**Institution**: School of Electrical Engineering, Manipal Institute of Technology Bengaluru  
**Process Technology**: Cadence GPDK 180nm CMOS ($V_{DD} = 1.8\text{ V}$)  
**Toolsuite**: Cadence Design Suite (Spectre / Virtuoso IC618)

---

## Overview

This repository hosts the schematic design, analytical sizing methodology, Cadence Spectre simulation testbenches, and comprehensive performance verification for a **6-bit High-Speed Differential Current-Steering DAC**.

### Target Specifications
* **Resolution**: 6 bits (64 conversion levels)
* **Sampling / Update Rate**: $\ge 200\text{ MS/s}$
* **Full-Scale Current ($I_{FS}$)**: $1.575\text{ mA}$ ($I_{LSB} = 25\ \mu\text{A}$)
* **Differential Output Swing**: $\ge 600\text{ mV}_{p-p}$ ($R_L = 200\ \Omega$)
* **Differential Non-Linearity (DNL)**: $|\text{DNL}| < 0.5\text{ LSB}$ (Strict monotonicity)
* **Integral Non-Linearity (INL)**: $|\text{INL}| < 0.8\text{ LSB}$
* **Settling Time ($t_s$)**: $< 3.5\text{ ns}$ (to within $0.5\text{ LSB}$)
* **Spurious-Free Dynamic Range (SFDR)**: $\ge 42\text{ dB}$ at Nyquist

---

## Repository Structure

```
.
├── cadence/          # Cadence Spectre netlists, subcircuits, and testbenches
├── scripts/          # Analytical sizing formulas and waveform plotting scripts
├── figures/          # High-resolution simulation plots & architectural schematics
└── report/           # 5-8 page IEEE format project report LaTeX source & compiled PDF
```
