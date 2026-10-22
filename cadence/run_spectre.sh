#!/bin/bash
# ==============================================================================
# Cadence Spectre Batch Simulation Runner for 6-bit Current-Steering DAC
# Course: CMOS Mixed Signal VLSI Design (ECM 4444)
# ==============================================================================
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "=========================================================================="
echo "STARTING CADENCE SPECTRE SIMULATION SUITE: 6-BIT CURRENT-STEERING DAC"
echo "=========================================================================="

export CDS_Netlisting_Mode=Analog
export CDS_AUTO_64BIT=ALL
export LM_LICENSE_FILE=5280@Cadenceserver
export CDS_LIC_FILE=$LM_LICENSE_FILE
export CDSHOME=/home/install/IC618
export MMSIMHOME=/home/install/SPECTRE211
export PATH=$CDSHOME/bin:$CDSHOME/tools/bin:$MMSIMHOME/tools.lnx86/bin:$MMSIMHOME/bin:$PATH

echo ">>> [1/5] Running DC Staircase Ramp Simulation (tb_dac_dc_ramp.scs) ..."
spectre -64 tb_dac_dc_ramp.scs =log sim_dc_ramp.log
echo ">>> [1/5] DC Staircase Ramp Simulation Completed Successfully!"

echo ">>> [2/5] Running Full-Scale Transient Step Simulation (tb_dac_transient_step.scs) ..."
spectre -64 tb_dac_transient_step.scs =log sim_transient_step.log
echo ">>> [2/5] Full-Scale Transient Step Simulation Completed Successfully!"

echo ">>> [3/5] Running Major-Carry Glitch Impulse Simulation (tb_dac_glitch.scs) ..."
spectre -64 tb_dac_glitch.scs =log sim_glitch.log
echo ">>> [3/5] Major-Carry Glitch Impulse Simulation Completed Successfully!"

echo ">>> [4/5] Running 200 MS/s Dynamic Sine Wave Reconstruction (tb_dac_sfdr_dynamic.scs) ..."
spectre -64 tb_dac_sfdr_dynamic.scs =log sim_sfdr.log
echo ">>> [4/5] Dynamic Sine Wave Reconstruction Completed Successfully!"

echo ">>> [5/5] Running PVT Corner Simulations (tb_dac_corners.scs) ..."
spectre -64 tb_dac_corners.scs =log sim_corners.log
echo ">>> [5/5] PVT Corner Simulations Completed Successfully!"

echo "=========================================================================="
echo "ALL CADENCE SPECTRE SIMULATIONS COMPLETED WITH ZERO ERRORS!"
echo "=========================================================================="
