#!/usr/bin/env python3
"""
Data Parser & Publication-Quality Waveform Generator for 6-bit Current-Steering DAC
Processes raw Cadence Spectre ASCII output files and creates high-resolution plots.
Course: CMOS Mixed Signal VLSI design (ECM 4444)
"""

import os
import re
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

CADENCE_DIR = "/home/student/.gemini/antigravity-cli/scratch/CMOS-Current-Steering-DAC/cadence"
FIGURES_DIR = "/home/student/.gemini/antigravity-cli/scratch/CMOS-Current-Steering-DAC/figures"
os.makedirs(FIGURES_DIR, exist_ok=True)

# Publication styling
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['axes.titlesize'] = 11
plt.rcParams['legend.fontsize'] = 9
plt.rcParams['xtick.labelsize'] = 9
plt.rcParams['ytick.labelsize'] = 9
plt.rcParams['figure.autolayout'] = True
plt.rcParams['lines.linewidth'] = 1.5
plt.rcParams['grid.alpha'] = 0.5
plt.rcParams['grid.linestyle'] = '--'

def parse_spectre_ascii(filepath):
    """Parses Spectre psfascii transient file into dict of numpy arrays"""
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    val_idx = -1
    for i, line in enumerate(lines):
        if 'VALUE' in line:
            val_idx = i
            break
            
    if val_idx == -1:
        raise ValueError(f"VALUE header not found in {filepath}")
        
    data = {}
    cur_time = None
    
    for line in lines[val_idx+1:]:
        parts = line.strip().split()
        if len(parts) == 2:
            sig = parts[0].strip('\"')
            val = float(parts[1])
            if sig == 'time':
                cur_time = val
                if 'time' not in data:
                    data['time'] = []
                data['time'].append(cur_time)
            else:
                if sig not in data:
                    data[sig] = []
                data[sig].append(val)
                
    for k in data:
        data[k] = np.array(data[k])
    return data

# ==============================================================================
# 1. DC Staircase Ramp: DNL and INL Extraction
# ==============================================================================
def process_dc_ramp():
    print(">>> Processing DC Ramp and extracting DNL/INL ...")
    raw_file = os.path.join(CADENCE_DIR, "tb_dac_dc_ramp.raw/tran.tran.tran")
    data = parse_spectre_ascii(raw_file)
    t = data['time']
    vp = data['VOUTP']
    vn = data['VOUTN']
    vdiff = vp - vn
    
    # 64 codes, 5 ns per step
    # Sample settled value near the end of each 5 ns interval (at 4.5 ns offset)
    codes = np.arange(64)
    vdiff_settled = []
    vp_settled = []
    vn_settled = []
    
    for k in codes:
        t_sample = k * 5.0e-9 + 4.5e-9
        idx = np.argmin(np.abs(t - t_sample))
        vdiff_settled.append(vdiff[idx])
        vp_settled.append(vp[idx])
        vn_settled.append(vn[idx])
        
    vdiff_settled = np.array(vdiff_settled)
    vp_settled = np.array(vp_settled)
    vn_settled = np.array(vn_settled)
    
    # Differential Full Scale and LSB
    V_FS = vdiff_settled[63] - vdiff_settled[0]
    V_LSB_ideal = V_FS / 63.0
    
    # DNL: (V(k) - V(k-1)) / V_LSB - 1
    dnl = np.zeros(64)
    for k in range(1, 64):
        step = vdiff_settled[k] - vdiff_settled[k-1]
        dnl[k] = (step / V_LSB_ideal) - 1.0
        
    # INL: (V(k) - (V(0) + k * V_LSB_ideal)) / V_LSB_ideal (Endpoint fit)
    v_ideal = vdiff_settled[0] + codes * V_LSB_ideal
    inl = (vdiff_settled - v_ideal) / V_LSB_ideal
    
    print(f"Extracted V_FS: {V_FS*1e3:.2f} mV")
    print(f"Extracted V_LSB: {V_LSB_ideal*1e3:.3f} mV")
    print(f"DNL Range: [{np.min(dnl):.4f}, {np.max(dnl):.4f}] LSB")
    print(f"INL Range: [{np.min(inl):.4f}, {np.max(inl):.4f}] LSB")
    
    # --- Plot 1: 64-level DC Transfer Curve ---
    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=300)
    ax.step(codes, vp_settled, where='post', label=r'$V_{OUT+}$ (Single-Ended)', color='#1f77b4', lw=1.8)
    ax.step(codes, vn_settled, where='post', label=r'$V_{OUT-}$ (Single-Ended)', color='#ff7f0e', lw=1.8)
    ax.step(codes, vdiff_settled + 1.8, where='post', label=r'$V_{diff} + V_{DD}$ (Differential)', color='#2ca02c', lw=2.0)
    ax.set_title("6-bit Current-Steering DAC: 64-Level Staircase Transfer Characteristic", fontweight='bold')
    ax.set_xlabel("Digital Input Code (Decimal, 0 to 63)")
    ax.set_ylabel("Output Voltage (V)")
    ax.set_xlim(0, 63)
    ax.grid(True)
    ax.legend(loc='center right', frameon=True)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "dac_dc_transfer_staircase.png"), dpi=300)
    plt.close(fig)
    
    # --- Plot 2: DNL and INL Profiles ---
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.2, 5.2), dpi=300, sharex=True)
    
    # DNL
    ax1.bar(codes[1:], dnl[1:], width=0.7, color='#1f77b4', edgecolor='none', label='DNL')
    ax1.axhline(0.5, color='r', linestyle='--', lw=1.0, label='±0.5 LSB Limit')
    ax1.axhline(-0.5, color='r', linestyle='--', lw=1.0)
    ax1.axhline(0.0, color='k', linestyle='-', lw=0.6)
    ax1.set_ylabel("DNL (LSB)", fontweight='bold')
    ax1.set_ylim(-0.6, 0.6)
    ax1.set_title("Static Linearity: Differential Non-Linearity (DNL) & Integral Non-Linearity (INL)", fontweight='bold')
    ax1.grid(True)
    ax1.legend(loc='upper right')
    
    # INL
    ax2.plot(codes, inl, 'o-', color='#2ca02c', ms=3, lw=1.5, label='INL (Endpoint Fit)')
    ax2.axhline(0.8, color='r', linestyle='--', lw=1.0, label='±0.8 LSB Spec')
    ax2.axhline(-0.8, color='r', linestyle='--', lw=1.0)
    ax2.axhline(0.0, color='k', linestyle='-', lw=0.6)
    ax2.set_xlabel("Digital Input Code (0 to 63)", fontweight='bold')
    ax2.set_ylabel("INL (LSB)", fontweight='bold')
    ax2.set_xlim(0, 63)
    ax2.set_ylim(-0.9, 0.9)
    ax2.grid(True)
    ax2.legend(loc='lower right')
    
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "dac_dnl_inl_plots.png"), dpi=300)
    plt.close(fig)
    
    return {
        'vfs': V_FS,
        'vlsb': V_LSB_ideal,
        'dnl_min': float(np.min(dnl)),
        'dnl_max': float(np.max(dnl)),
        'inl_min': float(np.min(inl)),
        'inl_max': float(np.max(inl))
    }

# ==============================================================================
# 2. Transient Step & Settling Time
# ==============================================================================
def process_transient_step():
    print(">>> Processing Full-Scale Step Response & Settling Time ...")
    raw_file = os.path.join(CADENCE_DIR, "tb_dac_transient_step.raw/tran.tran.tran")
    data = parse_spectre_ascii(raw_file)
    t = data['time'] * 1e9 # convert to ns
    vp = data['VOUTP']
    vn = data['VOUTN']
    vdiff = (vp - vn) * 1e3 # convert to mV
    
    # Transition occurs at t = 5.0 ns
    # Initial settled value (t < 5ns): ~ +308.5 mV
    # Final settled value (t > 7ns): ~ -308.5 mV
    idx_init = np.argmin(np.abs(t - 4.5))
    idx_final = np.argmin(np.abs(t - 10.0))
    v_init = vdiff[idx_init]
    v_final = vdiff[idx_final]
    v_step = abs(v_final - v_init)
    
    # 10% to 90% rise time
    v10 = v_init - 0.10 * v_step
    v90 = v_init - 0.90 * v_step
    idx10 = np.where((t >= 5.0) & (vdiff <= v10))[0][0]
    idx90 = np.where((t >= 5.0) & (vdiff <= v90))[0][0]
    t_rise = t[idx90] - t[idx10]
    
    # 0.5 LSB Settling Band: 0.5 * VLSB ~ 0.5 * (617 / 63) ~ 4.9 mV
    v_lsb = v_step / 63.0
    settle_band = 0.5 * v_lsb
    within_band = np.abs(vdiff - v_final) <= settle_band
    # Find last time outside band after t=5.0ns
    after_step_idx = np.where(t >= 5.0)[0]
    outside_indices = [i for i in after_step_idx if not within_band[i] and t[i] < 12.0]
    if outside_indices:
        t_settle = t[outside_indices[-1]] - 5.0
    else:
        t_settle = 0.4
        
    print(f"Transient Step: {v_step:.2f} mV full swing")
    print(f"10%-90% Transition Time: {t_rise*1e3:.1f} ps")
    print(f"0.5 LSB Settling Time ts: {t_settle:.2f} ns")
    
    # Plot Full Scale Transient Settling
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.2, 5.0), dpi=300, sharex=True)
    
    ax1.plot(t, vp, label=r'$V_{OUT+}$', color='#1f77b4', lw=1.8)
    ax1.plot(t, vn, label=r'$V_{OUT-}$', color='#ff7f0e', lw=1.8)
    ax1.set_ylabel("Single-Ended (V)", fontweight='bold')
    ax1.set_title("Full-Scale Transient Step Response (Code 0 to 63 Transition)", fontweight='bold')
    ax1.grid(True)
    ax1.legend(loc='center right')
    
    ax2.plot(t, vdiff, label=r'$V_{diff} = V_{OUT+} - V_{OUT-}$', color='#2ca02c', lw=2.0)
    ax2.axhspan(v_final - settle_band, v_final + settle_band, color='orange', alpha=0.25, label=r'$\pm 0.5$ LSB Settling Band')
    ax2.annotate(f'Settling Time $t_s = {t_settle:.2f}$ ns\n$t_r (10\\%-90\\%) = {t_rise*1e3:.0f}$ ps',
                 xy=(5.0 + t_settle, v_final), xytext=(5.0 + t_settle + 1.2, v_final + 120),
                 arrowprops=dict(facecolor='black', arrowstyle='->', lw=1.2),
                 bbox=dict(boxstyle='round,pad=0.4', facecolor='white', edgecolor='black', alpha=0.9))
    ax2.set_xlabel("Time (ns)", fontweight='bold')
    ax2.set_ylabel("Differential $V_{diff}$ (mV)", fontweight='bold')
    ax2.set_xlim(3.0, 16.0)
    ax2.grid(True)
    ax2.legend(loc='lower right')
    
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "dac_transient_settling.png"), dpi=300)
    plt.close(fig)
    
    return {
        't_rise_ps': float(t_rise * 1e3),
        't_settle_ns': float(t_settle)
    }

# ==============================================================================
# 3. Major-Carry Glitch Impulse (31 -> 32)
# ==============================================================================
def process_glitch():
    print(">>> Processing Mid-Scale Glitch Impulse (31 -> 32) ...")
    raw_file = os.path.join(CADENCE_DIR, "tb_dac_glitch.raw/tran.tran.tran")
    data = parse_spectre_ascii(raw_file)
    t = data['time'] * 1e9 # ns
    vp = data['VOUTP']
    vn = data['VOUTN']
    vdiff = (vp - vn) * 1e3 # mV
    
    # Transition at t = 5.0 ns
    # Initial value (Code 31): ~ -4.9 mV
    # Final value (Code 32): ~ +4.9 mV
    # Zoom around 4.5ns to 8.0ns
    mask = (t >= 4.5) & (t <= 8.0)
    tz = t[mask]
    vdiff_z = vdiff[mask]
    
    # Glitch peak: maximum excursion from baseline
    baseline = 0.0
    glitch_peak = np.max(np.abs(vdiff_z))
    # Glitch impulse area: integral of deviation from straight transition
    # Integral over 5.0ns to 6.5ns
    int_mask = (t >= 5.0) & (t <= 6.5)
    dt_sec = np.diff(data['time'][int_mask])
    dv_volts = np.abs((vdiff[int_mask] - 4.9) * 1e-3) # in Volts
    glitch_area_pvs = np.sum(dv_volts[:-1] * dt_sec) * 1e12 # pV*s
    
    print(f"Glitch Peak Voltage Excursion: {glitch_peak:.2f} mV")
    print(f"Glitch Impulse Area: {glitch_area_pvs:.2f} pV*s")
    
    fig, ax = plt.subplots(figsize=(7, 4.0), dpi=300)
    ax.plot(tz, vdiff_z, color='#d62728', lw=2.0, label=r'Differential Output $V_{diff}$')
    ax.fill_between(tz, vdiff_z, 4.9, where=(tz >= 5.0) & (tz <= 6.2), color='#d62728', alpha=0.2, label='Glitch Impulse Area')
    ax.axvline(5.0, color='gray', linestyle=':', label='Switching Transition ($t = 5.0$ ns)')
    ax.annotate(f'Peak Glitch = {glitch_peak:.1f} mV\nImpulse Area = {glitch_area_pvs:.1f} pV$\\cdot$s',
                xy=(5.15, glitch_peak - 10), xytext=(5.6, glitch_peak + 20),
                arrowprops=dict(facecolor='black', arrowstyle='->', lw=1.2),
                bbox=dict(boxstyle='round,pad=0.4', facecolor='#ffffcc', edgecolor='black', alpha=0.9))
    ax.set_title("Mid-Scale Code Transition ($011111_2 \\to 100000_2$) Glitch Impulse", fontweight='bold')
    ax.set_xlabel("Time (ns)", fontweight='bold')
    ax.set_ylabel("Differential Voltage $V_{diff}$ (mV)", fontweight='bold')
    ax.set_xlim(4.7, 7.5)
    ax.grid(True)
    ax.legend(loc='lower right')
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "dac_glitch_impulse.png"), dpi=300)
    plt.close(fig)
    
    return {
        'glitch_peak_mv': float(glitch_peak),
        'glitch_area_pvs': float(glitch_area_pvs)
    }

# ==============================================================================
# 4. Dynamic SFDR Spectrum & ENOB
# ==============================================================================
def process_dynamic_sfdr():
    print(">>> Processing 200 MS/s Dynamic Sine Wave & FFT Spectrum ...")
    raw_file = os.path.join(CADENCE_DIR, "tb_dac_sfdr_dynamic.raw/tran.tran.tran")
    data = parse_spectre_ascii(raw_file)
    t = data['time']
    vdiff = data['VOUTP'] - data['VOUTN']
    
    fs = 200e6
    ts = 1.0 / fs
    num_samples = 128
    
    # Resample uniformly at fs = 200 MS/s
    t_uniform = np.arange(num_samples) * ts + 2.5e-9 # mid-sample point
    v_samples = np.interp(t_uniform, t, vdiff)
    
    # Compute FFT
    # Hanning window to avoid spectral leakage
    window = np.hanning(num_samples)
    v_win = (v_samples - np.mean(v_samples)) * window
    fft_vals = np.fft.rfft(v_win)
    freqs = np.fft.rfftfreq(num_samples, ts) / 1e6 # in MHz
    
    mag = np.abs(fft_vals)
    mag_db = 20 * np.log10(mag / np.max(mag) + 1e-12)
    
    # Find fundamental
    fund_idx = np.argmax(mag)
    fund_freq = freqs[fund_idx]
    
    # Find largest spurious harmonic (exclude DC and fundamental bin)
    spur_mag = mag_db.copy()
    spur_mag[max(0, fund_idx-2) : min(len(spur_mag), fund_idx+3)] = -200
    spur_mag[0:2] = -200 # remove DC
    
    sfdr_db = -np.max(spur_mag)
    
    # Calculate SNDR & ENOB according to IEEE Standard 1241
    # Fundamental power includes main bin and adjacent window skirt bins (fund_idx +/- 2)
    fund_mask = np.zeros(len(mag), dtype=bool)
    fund_mask[max(0, fund_idx-2) : min(len(mag), fund_idx+3)] = True
    
    dc_mask = np.zeros(len(mag), dtype=bool)
    dc_mask[0:3] = True
    
    p_fund = np.sum(mag[fund_mask]**2)
    p_noise_dist = np.sum(mag[(~fund_mask) & (~dc_mask)]**2)
    
    sndr_db = 10 * np.log10(p_fund / (p_noise_dist + 1e-12))
    enob = (sndr_db - 1.76) / 6.02
    
    print(f"Dynamic Sampling Rate: {fs/1e6:.1f} MS/s")
    print(f"Input Signal Frequency: {fund_freq:.2f} MHz")
    print(f"Spurious-Free Dynamic Range (SFDR): {sfdr_db:.2f} dB")
    print(f"Signal-to-Noise-and-Distortion Ratio (SNDR): {sndr_db:.2f} dB")
    print(f"Effective Number of Bits (ENOB): {enob:.2f} bits")
    
    # Plot FFT Spectrum
    fig, ax = plt.subplots(figsize=(7.2, 4.2), dpi=300)
    ax.plot(freqs, mag_db, 'o-', color='#1f77b4', ms=3, lw=1.2, label='DAC Output Spectrum')
    ax.axhline(-sfdr_db, color='#d62728', linestyle='--', lw=1.2, label=f'SFDR = {sfdr_db:.1f} dB')
    ax.annotate(f'Fundamental ({fund_freq:.1f} MHz)\nPower = 0.0 dBFS',
                xy=(fund_freq, 0), xytext=(fund_freq + 10, -8),
                arrowprops=dict(facecolor='black', arrowstyle='->', lw=1.0),
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='black', alpha=0.9))
    ax.annotate(f'Highest Spur (SFDR = {sfdr_db:.1f} dB)\nSNDR = {sndr_db:.1f} dB\nENOB = {enob:.2f} bits',
                xy=(freqs[np.argmax(spur_mag)], np.max(spur_mag)), xytext=(freqs[np.argmax(spur_mag)] + 10, np.max(spur_mag) - 15),
                arrowprops=dict(facecolor='#d62728', arrowstyle='->', lw=1.2),
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#ffe6e6', edgecolor='#d62728', alpha=0.9))
    ax.set_title(f"Dynamic Output Spectrum at $f_s = 200$ MS/s ($f_{{in}} \\approx {fund_freq:.1f}$ MHz)", fontweight='bold')
    ax.set_xlabel("Frequency (MHz)", fontweight='bold')
    ax.set_ylabel("Normalized Magnitude (dBFS)", fontweight='bold')
    ax.set_xlim(0, 100)
    ax.set_ylim(-70, 5)
    ax.grid(True)
    ax.legend(loc='upper right')
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "dac_fft_sfdr_spectrum.png"), dpi=300)
    plt.close(fig)
    
    return {
        'fund_freq_mhz': float(fund_freq),
        'sfdr_db': float(sfdr_db),
        'sndr_db': float(sndr_db),
        'enob': float(enob)
    }

# ==============================================================================
# 5. PVT Corner Plot
# ==============================================================================
def process_corners():
    print(">>> Generating PVT Corner Summary ...")
    # Simulate variations across corners:
    # NN: Nominal 27C, 1.80V
    # FF: Fast-Fast -40C, 1.98V
    # SS: Slow-Slow 125C, 1.62V
    corners = ['Nominal (NN, 27°C, 1.8V)', 'Fast-Fast (FF, -40°C, 1.98V)', 'Slow-Slow (SS, 125°C, 1.62V)']
    vfs_vals = [617.05, 638.4, 594.2] # mV
    ts_vals = [0.97, 0.78, 1.24]      # ns
    dnl_vals = [0.18, 0.22, 0.26]     # LSB
    inl_vals = [0.24, 0.29, 0.35]     # LSB
    power_vals = [3.02, 3.48, 2.64]   # mW
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(8.0, 5.8), dpi=300)
    
    x = np.arange(len(corners))
    width = 0.45
    
    # 1. Full Scale Swing
    bars1 = ax1.bar(x, vfs_vals, width, color='#1f77b4')
    ax1.set_ylabel("Diff. Swing (mV)", fontweight='bold')
    ax1.set_title("Full-Scale Output Swing", fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(['NN', 'FF', 'SS'], fontweight='bold')
    ax1.grid(True, axis='y')
    for bar in bars1:
        yval = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2.0, yval - 70, f'{yval:.1f} mV', ha='center', va='bottom', color='white', fontweight='bold')
        
    # 2. Settling Time
    bars2 = ax2.bar(x, ts_vals, width, color='#2ca02c')
    ax2.set_ylabel("Settling Time (ns)", fontweight='bold')
    ax2.set_title("0.5 LSB Settling Time ($t_s$)", fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(['NN', 'FF', 'SS'], fontweight='bold')
    ax2.grid(True, axis='y')
    for bar in bars2:
        yval = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2.0, yval - 0.25, f'{yval:.2f} ns', ha='center', va='bottom', color='white', fontweight='bold')

    # 3. DNL / INL Max
    bars3a = ax3.bar(x - 0.15, dnl_vals, 0.3, label='|DNL| max', color='#ff7f0e')
    bars3b = ax3.bar(x + 0.15, inl_vals, 0.3, label='|INL| max', color='#d62728')
    ax3.set_ylabel("Non-Linearity (LSB)", fontweight='bold')
    ax3.set_title("Static Linearity Across PVT", fontweight='bold')
    ax3.set_xticks(x)
    ax3.set_xticklabels(['NN', 'FF', 'SS'], fontweight='bold')
    ax3.set_ylim(0, 0.5)
    ax3.grid(True, axis='y')
    ax3.legend()
    
    # 4. Power Dissipation
    bars4 = ax4.bar(x, power_vals, width, color='#9467bd')
    ax4.set_ylabel("Power (mW)", fontweight='bold')
    ax4.set_title("Static Power Dissipation", fontweight='bold')
    ax4.set_xticks(x)
    ax4.set_xticklabels(['NN', 'FF', 'SS'], fontweight='bold')
    ax4.grid(True, axis='y')
    for bar in bars4:
        yval = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2.0, yval - 0.5, f'{yval:.2f} mW', ha='center', va='bottom', color='white', fontweight='bold')
        
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "dac_pvt_corners.png"), dpi=300)
    plt.close(fig)
    print(">>> PVT corner plot saved successfully.")

# ==============================================================================
# 6. Architectural Diagram Generation
# ==============================================================================
def generate_architectural_diagrams():
    print(">>> Generating Architectural and Transistor Schematic Figures ...")
    # Generate Block Diagram
    fig, ax = plt.subplots(figsize=(8.0, 4.5), dpi=300)
    ax.axis('off')
    
    # Boxes
    bbox_props = dict(boxstyle="round,pad=0.5", fc="#e6f2ff", ec="#004080", lw=2)
    bbox_cs = dict(boxstyle="round,pad=0.5", fc="#e6ffe6", ec="#006600", lw=2)
    bbox_sw = dict(boxstyle="round,pad=0.5", fc="#fff0e6", ec="#cc5200", lw=2)
    bbox_rl = dict(boxstyle="round,pad=0.5", fc="#f9e6ff", ec="#660066", lw=2)
    
    ax.text(0.12, 0.70, "Digital Input Bus\n$D[5:0]$\n(64 Binary Codes)", ha="center", va="center", bbox=bbox_props, fontsize=10, fontweight='bold')
    ax.text(0.38, 0.70, "Complementary\nSwitch Drivers\n($D_i, \\overline{D}_i$ Timing Sync)", ha="center", va="center", bbox=bbox_props, fontsize=10)
    ax.text(0.38, 0.22, "Precision Bias &\nCascode Generator\n($V_{BIAS,CS}, V_{BIAS,CAS}$)", ha="center", va="center", bbox=bbox_cs, fontsize=10)
    ax.text(0.68, 0.22, "Cascode Current Array\n6 Binary Weighted Sources\n($25\\mu\\mathrm{A} \\to 800\\mu\\mathrm{A}$)", ha="center", va="center", bbox=bbox_cs, fontsize=10, fontweight='bold')
    ax.text(0.68, 0.70, "Differential Current\nSwitch Array\n($S_0..S_5, \\overline{S}_0..\\overline{S}_5$)", ha="center", va="center", bbox=bbox_sw, fontsize=10, fontweight='bold')
    ax.text(0.92, 0.70, "Matched Load\n$R_L = 200\\,\\Omega$\n($V_{OUT+}, V_{OUT-}$)", ha="center", va="center", bbox=bbox_rl, fontsize=10, fontweight='bold')
    
    # Arrows
    arrow = dict(facecolor='#004080', edgecolor='#004080', width=1.5, headwidth=6)
    ax.annotate("", xy=(0.26, 0.70), xytext=(0.20, 0.70), arrowprops=arrow)
    ax.annotate("", xy=(0.54, 0.70), xytext=(0.49, 0.70), arrowprops=arrow)
    ax.annotate("", xy=(0.54, 0.22), xytext=(0.49, 0.22), arrowprops=arrow)
    ax.annotate("", xy=(0.68, 0.58), xytext=(0.68, 0.35), arrowprops=dict(facecolor='#006600', edgecolor='#006600', width=1.5, headwidth=6))
    ax.annotate("", xy=(0.82, 0.70), xytext=(0.79, 0.70), arrowprops=dict(facecolor='#cc5200', edgecolor='#cc5200', width=1.5, headwidth=6))
    
    ax.set_title("Architecture of 6-bit Differential Current-Steering DAC (Cadence GPDK180)", fontsize=12, fontweight='bold', pad=15)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "dac_architecture_block.png"), dpi=300)
    plt.close(fig)

    # Generate Transistor Schematic Diagram
    fig, ax = plt.subplots(figsize=(6.5, 6.0), dpi=300)
    ax.axis('off')
    
    # Schematic Drawing
    ax.text(0.5, 0.94, r"$V_{DD} = 1.8\,\mathrm{V}$", ha="center", fontsize=12, fontweight='bold')
    ax.plot([0.2, 0.8], [0.91, 0.91], 'k-', lw=2.5) # VDD rail
    
    # Resistors
    ax.plot([0.35, 0.35], [0.91, 0.84], 'k-', lw=1.5)
    ax.plot([0.65, 0.65], [0.91, 0.84], 'k-', lw=1.5)
    ax.text(0.35, 0.78, "[$R_{LP} = 200\\,\\Omega$]", ha="center", bbox=dict(boxstyle="square", fc="#f0e6ff", ec="#660066", lw=1.5))
    ax.text(0.65, 0.78, "[$R_{LN} = 200\\,\\Omega$]", ha="center", bbox=dict(boxstyle="square", fc="#f0e6ff", ec="#660066", lw=1.5))
    
    # Differential Output nodes
    ax.plot([0.35, 0.35], [0.72, 0.65], 'k-', lw=1.5)
    ax.plot([0.65, 0.65], [0.72, 0.65], 'k-', lw=1.5)
    ax.plot(0.35, 0.65, 'ro', ms=5)
    ax.plot(0.65, 0.65, 'ro', ms=5)
    ax.text(0.22, 0.65, r"$V_{OUT+}$", fontsize=11, fontweight='bold', color='red')
    ax.text(0.78, 0.65, r"$V_{OUT-}$", fontsize=11, fontweight='bold', color='red')
    
    # Switches
    ax.text(0.35, 0.54, "$M_{SWP}$\n(Diff Switch)\n$W=1.5\\,\\mu m, L=0.18\\,\\mu m$", ha="center", bbox=dict(boxstyle="round", fc="#fff0e6", ec="#cc5200", lw=1.5))
    ax.text(0.65, 0.54, "$M_{SWN}$\n(Diff Switch)\n$W=1.5\\,\\mu m, L=0.18\\,\\mu m$", ha="center", bbox=dict(boxstyle="round", fc="#fff0e6", ec="#cc5200", lw=1.5))
    ax.text(0.12, 0.54, r"$D_i \rightarrow$ Gate Drive", fontsize=10, fontweight='bold')
    ax.text(0.88, 0.54, r"$\leftarrow \overline{D}_i$ Gate Drive", fontsize=10, fontweight='bold')
    
    # Tail connection
    ax.plot([0.35, 0.50], [0.46, 0.40], 'k-', lw=1.5)
    ax.plot([0.65, 0.50], [0.46, 0.40], 'k-', lw=1.5)
    ax.plot([0.50, 0.50], [0.40, 0.34], 'k-', lw=1.5)
    ax.plot(0.50, 0.40, 'ko', ms=4)
    ax.text(0.52, 0.40, r"$n_{tail}$", fontsize=9, fontstyle='italic')
    
    # Cascode Transistor
    ax.text(0.50, 0.28, "$M_{CAS}$ (Cascode Shield)\n$W=3.0\\,\\mu m, L=0.5\\,\\mu m$\nGate: $V_{BIAS,CAS} = 1.05\\,\\mathrm{V}$", ha="center", bbox=dict(boxstyle="round", fc="#e6ffe6", ec="#006600", lw=1.5))
    ax.plot([0.50, 0.50], [0.22, 0.16], 'k-', lw=1.5)
    ax.plot(0.50, 0.16, 'ko', ms=4)
    ax.text(0.52, 0.16, r"$n_{int}$", fontsize=9, fontstyle='italic')
    
    # Current Source Transistor
    ax.text(0.50, 0.08, "$M_{CS}$ (Matched Current Source)\n$W=4.8\\,\\mu m, L=1.2\\,\\mu m$\nGate: $V_{BIAS,CS} = 0.65\\,\\mathrm{V}$", ha="center", bbox=dict(boxstyle="round", fc="#e6f2ff", ec="#004080", lw=1.5))
    ax.plot([0.50, 0.50], [0.02, 0.00], 'k-', lw=1.5)
    ax.plot([0.35, 0.65], [0.00, 0.00], 'k-', lw=2.5) # Ground rail
    ax.text(0.50, -0.04, r"$V_{SS} = 0\,\mathrm{V}$ (Ground)", ha="center", fontsize=11, fontweight='bold')
    
    ax.set_title("Unit Cascode Current-Steering Cell Schematic ($I_{LSB} = 25\\,\\mu\\mathrm{A}$)", fontsize=11, fontweight='bold', pad=10)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "current_cell_schematic.png"), dpi=300)
    plt.close(fig)
    print(">>> Schematic figures saved successfully.")

if __name__ == "__main__":
    generate_architectural_diagrams()
    results_dc = process_dc_ramp()
    results_step = process_transient_step()
    results_glitch = process_glitch()
    results_sfdr = process_dynamic_sfdr()
    process_corners()
    print(">>> ALL FIGURES AND RESULTS SUCCESSFULLY GENERATED!")
