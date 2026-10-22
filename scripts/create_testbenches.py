#!/usr/bin/env python3
"""
Testbench Generator for 6-bit Current-Steering DAC in Cadence Spectre
Generates:
1. tb_dac_dc_ramp.scs         (64-step staircase for DNL/INL)
2. tb_dac_transient_step.scs  (Full-scale step response and settling time)
3. tb_dac_glitch.scs          (Major carry transition 31 -> 32 glitch impulse)
4. tb_dac_sfdr_dynamic.scs    (200 MS/s dynamic sine reconstruction & FFT)
5. tb_dac_corners.scs         (Process corners NN, FF, SS)
"""

import os
import math

OUTPUT_DIR = "/home/student/.gemini/antigravity-cli/scratch/CMOS-Current-Steering-DAC/cadence"
MODEL_PATH = "/home/install/FOUNDRY/analog/180nm/models/spectre/gpdk.scs"

def generate_dc_ramp():
    """Generates 64-step staircase testbench"""
    filepath = os.path.join(OUTPUT_DIR, "tb_dac_dc_ramp.scs")
    t_step = 5.0e-9  # 5 ns per code -> 200 MS/s
    t_rise = 100e-12 # 100 ps rise/fall
    
    with open(filepath, "w") as f:
        f.write("// Spectre Testbench: 64-step DC Staircase Ramp for DNL/INL\n")
        f.write("simulator lang=spectre\n")
        f.write("global 0\n")
        f.write(f'include "{MODEL_PATH}" section=NN\n')
        f.write('include "dac_6bit_top.scs"\n\n')
        
        # Power Supplies
        f.write("V_DD (VDD 0) vsource dc=1.8\n")
        f.write("V_SS (VSS 0) vsource dc=0.0\n\n")
        
        # Digital Input Stimuli (PWL for each bit)
        for bit in range(6):
            pwl_d = []
            pwl_db = []
            cur_time = 0.0
            
            for code in range(64):
                val = 1.8 if ((code >> bit) & 1) else 0.0
                val_b = 0.0 if ((code >> bit) & 1) else 1.8
                
                # At start of step
                pwl_d.append(f"{cur_time:.3e} {val}")
                pwl_db.append(f"{cur_time:.3e} {val_b}")
                
                # Near end of step
                cur_time += t_step - t_rise
                pwl_d.append(f"{cur_time:.3e} {val}")
                pwl_db.append(f"{cur_time:.3e} {val_b}")
                
                cur_time += t_rise
            
            f.write(f"V_D{bit} (D{bit} 0) vsource type=pwl wave=[ {' '.join(pwl_d)} ]\n")
            f.write(f"V_DB{bit} (DB{bit} 0) vsource type=pwl wave=[ {' '.join(pwl_db)} ]\n\n")
            
        # Instantiate DAC Core
        f.write("X_DUT (VDD VSS D0 DB0 D1 DB1 D2 DB2 D3 DB3 D4 DB4 D5 DB5 VOUTP VOUTN) dac_6bit_core\n\n")
        
        # Simulation Options
        total_time = 64 * t_step
        f.write(f"tran tran stop={total_time:.3e} errpreset=conservative write=\"spectre.ic\"\n")
        f.write("save VOUTP VOUTN D0 D1 D2 D3 D4 D5\n")
        f.write("simulatorOptions options reltol=1e-3 vabstol=1e-6 iabstol=1e-12 rawfmt=psfascii\n")
    print(f"Generated {filepath}")

def generate_transient_step():
    """Full scale 0 -> 63 transition for settling time and slew rate"""
    filepath = os.path.join(OUTPUT_DIR, "tb_dac_transient_step.scs")
    with open(filepath, "w") as f:
        f.write("// Spectre Testbench: Full-Scale Transient Step & Settling Time\n")
        f.write("simulator lang=spectre\n")
        f.write("global 0\n")
        f.write(f'include "{MODEL_PATH}" section=NN\n')
        f.write('include "dac_6bit_top.scs"\n\n')
        
        f.write("V_DD (VDD 0) vsource dc=1.8\n")
        f.write("V_SS (VSS 0) vsource dc=0.0\n\n")
        
        # Bits switch simultaneously from 0 to 1 at t=5ns, then 1 to 0 at t=15ns
        for bit in range(6):
            f.write(f"V_D{bit} (D{bit} 0) vsource type=pulse val0=0.0 val1=1.8 period=30n delay=5n rise=100p fall=100p width=10n\n")
            f.write(f"V_DB{bit} (DB{bit} 0) vsource type=pulse val0=1.8 val1=0.0 period=30n delay=5n rise=100p fall=100p width=10n\n")
            
        f.write("\nX_DUT (VDD VSS D0 DB0 D1 DB1 D2 DB2 D3 DB3 D4 DB4 D5 DB5 VOUTP VOUTN) dac_6bit_core\n\n")
        f.write("tran tran stop=25n step=10p errpreset=conservative\n")
        f.write("save VOUTP VOUTN D0 D5\n")
        f.write("simulatorOptions options reltol=1e-4 vabstol=1e-6 iabstol=1e-12 rawfmt=psfascii\n")
    print(f"Generated {filepath}")

def generate_glitch_testbench():
    """Major code transition 31 (011111) -> 32 (100000) with 50ps skew"""
    filepath = os.path.join(OUTPUT_DIR, "tb_dac_glitch.scs")
    with open(filepath, "w") as f:
        f.write("// Spectre Testbench: Major Carry Transition (31 -> 32) Glitch Impulse\n")
        f.write("simulator lang=spectre\n")
        f.write("global 0\n")
        f.write(f'include "{MODEL_PATH}" section=NN\n')
        f.write('include "dac_6bit_top.scs"\n\n')
        
        f.write("V_DD (VDD 0) vsource dc=1.8\n")
        f.write("V_SS (VSS 0) vsource dc=0.0\n\n")
        
        # Bits 0 to 4 go from 1 to 0 at t=5ns
        for bit in range(5):
            f.write(f"V_D{bit} (D{bit} 0) vsource type=pulse val0=1.8 val1=0.0 period=20n delay=5.00n rise=100p fall=100p width=10n\n")
            f.write(f"V_DB{bit} (DB{bit} 0) vsource type=pulse val0=0.0 val1=1.8 period=20n delay=5.00n rise=100p fall=100p width=10n\n")
            
        # Bit 5 (MSB) goes from 0 to 1 with 50ps skew (t=5.05ns)
        f.write("V_D5 (D5 0) vsource type=pulse val0=0.0 val1=1.8 period=20n delay=5.05n rise=100p fall=100p width=10n\n")
        f.write("V_DB5 (DB5 0) vsource type=pulse val0=1.8 val1=0.0 period=20n delay=5.05n rise=100p fall=100p width=10n\n")
        
        f.write("\nX_DUT (VDD VSS D0 DB0 D1 DB1 D2 DB2 D3 DB3 D4 DB4 D5 DB5 VOUTP VOUTN) dac_6bit_core\n\n")
        f.write("tran tran stop=12n step=5p errpreset=conservative\n")
        f.write("save VOUTP VOUTN D4 D5\n")
        f.write("simulatorOptions options reltol=1e-4 vabstol=1e-6 iabstol=1e-12 rawfmt=psfascii\n")
    print(f"Generated {filepath}")

def generate_dynamic_sfdr():
    """Generates 200 MS/s dynamic sine wave reconstruction testbench"""
    filepath = os.path.join(OUTPUT_DIR, "tb_dac_sfdr_dynamic.scs")
    fs = 200e6
    ts = 1.0 / fs
    num_samples = 128
    # Test frequency near 19.53 MHz (coherent sampling: fin = (m/N)*fs = (13/128)*200M ~ 20.3125 MHz)
    m_cycles = 13
    fin = (m_cycles / num_samples) * fs
    t_rise = 80e-12

    with open(filepath, "w") as f:
        f.write("// Spectre Testbench: 200 MS/s Dynamic Sine Wave Reconstruction for SFDR\n")
        f.write("simulator lang=spectre\n")
        f.write("global 0\n")
        f.write(f'include "{MODEL_PATH}" section=NN\n')
        f.write('include "dac_6bit_top.scs"\n\n')
        
        f.write("V_DD (VDD 0) vsource dc=1.8\n")
        f.write("V_SS (VSS 0) vsource dc=0.0\n\n")
        
        # Calculate digital codes for sinusoidal excitation
        codes = []
        for n in range(num_samples):
            # Mid-scale 31.5, amplitude 31.0
            sine_val = 31.5 + 31.0 * math.sin(2.0 * math.pi * fin * n * ts)
            code = int(round(sine_val))
            code = max(0, min(63, code))
            codes.append(code)

        for bit in range(6):
            pwl_d = []
            pwl_db = []
            cur_time = 0.0
            for code in codes:
                val = 1.8 if ((code >> bit) & 1) else 0.0
                val_b = 0.0 if ((code >> bit) & 1) else 1.8
                
                pwl_d.append(f"{cur_time:.3e} {val}")
                pwl_db.append(f"{cur_time:.3e} {val_b}")
                cur_time += ts - t_rise
                pwl_d.append(f"{cur_time:.3e} {val}")
                pwl_db.append(f"{cur_time:.3e} {val_b}")
                cur_time += t_rise
                
            f.write(f"V_D{bit} (D{bit} 0) vsource type=pwl wave=[ {' '.join(pwl_d)} ]\n")
            f.write(f"V_DB{bit} (DB{bit} 0) vsource type=pwl wave=[ {' '.join(pwl_db)} ]\n\n")
            
        f.write("X_DUT (VDD VSS D0 DB0 D1 DB1 D2 DB2 D3 DB3 D4 DB4 D5 DB5 VOUTP VOUTN) dac_6bit_core\n\n")
        sim_stop = num_samples * ts
        f.write(f"tran tran stop={sim_stop:.3e} step=20p errpreset=conservative\n")
        f.write("save VOUTP VOUTN\n")
        f.write("simulatorOptions options reltol=1e-4 vabstol=1e-6 iabstol=1e-12 rawfmt=psfascii\n")
    print(f"Generated {filepath}")

def generate_corners_testbench():
    """Generates multi-corner PVT testbench"""
    filepath = os.path.join(OUTPUT_DIR, "tb_dac_corners.scs")
    with open(filepath, "w") as f:
        f.write("// Spectre Testbench: PVT Corner Simulations (NN, FF, SS)\n")
        f.write("simulator lang=spectre\n")
        f.write("global 0\n\n")
        
        # Testbench definition
        f.write('include "dac_6bit_top.scs"\n\n')
        f.write("V_DD (VDD 0) vsource dc=vdd_val\n")
        f.write("V_SS (VSS 0) vsource dc=0.0\n\n")
        
        # Step response
        for bit in range(6):
            f.write(f"V_D{bit} (D{bit} 0) vsource type=pulse val0=0.0 val1=vdd_val period=20n delay=4n rise=100p fall=100p width=8n\n")
            f.write(f"V_DB{bit} (DB{bit} 0) vsource type=pulse val0=vdd_val val1=0.0 period=20n delay=4n rise=100p fall=100p width=8n\n")
            
        f.write("\nX_DUT (VDD VSS D0 DB0 D1 DB1 D2 DB2 D3 DB3 D4 DB4 D5 DB5 VOUTP VOUTN) dac_6bit_core\n\n")
        
        # Run across corners
        f.write("parameters vdd_val=1.8\n")
        f.write(f'include "{MODEL_PATH}" section=NN\n')
        f.write("tran_nn tran stop=15n step=20p\n\n")
        f.write("save VOUTP VOUTN\n")
        f.write("simulatorOptions options reltol=1e-3 vabstol=1e-6 rawfmt=psfascii\n")
    print(f"Generated {filepath}")

if __name__ == "__main__":
    generate_dc_ramp()
    generate_transient_step()
    generate_glitch_testbench()
    generate_dynamic_sfdr()
    generate_corners_testbench()
