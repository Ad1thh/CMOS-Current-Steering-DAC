#!/usr/bin/env python3
import subprocess
import time
import os
from Xlib import X, display
from PIL import Image

disp_num = 99
os.environ["DISPLAY"] = f":{disp_num}"

# Clean up any leftover processes
subprocess.run(["pkill", "-9", "-f", f"Xvfb :{disp_num}"], stderr=subprocess.DEVNULL)
subprocess.run(["pkill", "-9", "-f", "virtuoso"], stderr=subprocess.DEVNULL)
time.sleep(1)

print("Starting Xvfb...")
xvfb = subprocess.Popen(["Xvfb", f":{disp_num}", "-screen", "0", "1920x1080x24"])
time.sleep(2)

try:
    fig_dir = "/home/student/.gemini/antigravity-cli/scratch/CMOS-Current-Steering-DAC/figures"
    os.makedirs(fig_dir, exist_ok=True)

    # 1. Capture current_cell
    skill_script = "/tmp/render_cell.il"
    with open(skill_script, "w") as f:
        f.write('''
deOpenCellView("dac_6bit_lib" "current_cell" "schematic" "schematic" nil "r")
schHiFit()
''')

    print("Opening current_cell in Virtuoso GUI...")
    cadence_cmd = f"source /home/install/cshrc && cd /home/student/.gemini/antigravity-cli/scratch/CMOS-Current-Steering-DAC/cadence && virtuoso -replay {skill_script}"
    v_proc = subprocess.Popen(["csh", "-c", cadence_cmd])
    time.sleep(10)

    d = display.Display(f":{disp_num}")
    root = d.screen().root
    geom = root.get_geometry()
    raw = root.get_image(0, 0, geom.width, geom.height, X.ZPixmap, 0xFFFFFFFF)
    img_full = Image.frombytes("RGB", (geom.width, geom.height), raw.data, "raw", "BGRX")
    
    cell_full_path = os.path.join(fig_dir, "virtuoso_current_cell_schematic.png")
    img_full.save(cell_full_path)
    print(f"Saved {cell_full_path}")

    # Crop canvas closeup: schematic window is typically centered
    # Let's inspect the bounding box of non-black/non-gray or standard schematic canvas area
    # Canvas area in Virtuoso standard 1920x1080 layout:
    # Top menu bar ~ 0 to 110 px
    # Left tool palette ~ 0 to 80 px
    # Right assistant ~ 1600 to 1920 px
    # Canvas roughly (85, 115, 1550, 950)
    img_crop = img_full.crop((80, 110, 1550, 950))
    cell_crop_path = os.path.join(fig_dir, "virtuoso_schematic_closeup.png")
    img_crop.save(cell_crop_path)
    print(f"Saved {cell_crop_path}")

    # 2. Capture dac_6bit_top
    skill_script_top = "/tmp/render_top.il"
    with open(skill_script_top, "w") as f:
        f.write('''
deOpenCellView("dac_6bit_lib" "dac_6bit_top" "schematic" "schematic" nil "r")
schHiFit()
''')
    subprocess.run(["pkill", "-9", "-f", "virtuoso"])
    time.sleep(2)

    print("Opening dac_6bit_top in Virtuoso GUI...")
    cadence_cmd_top = f"source /home/install/cshrc && cd /home/student/.gemini/antigravity-cli/scratch/CMOS-Current-Steering-DAC/cadence && virtuoso -replay {skill_script_top}"
    v_proc_top = subprocess.Popen(["csh", "-c", cadence_cmd_top])
    time.sleep(10)

    raw_top = root.get_image(0, 0, geom.width, geom.height, X.ZPixmap, 0xFFFFFFFF)
    img_top_full = Image.frombytes("RGB", (geom.width, geom.height), raw_top.data, "raw", "BGRX")
    
    top_full_path = os.path.join(fig_dir, "virtuoso_dac_top_schematic.png")
    img_top_full.save(top_full_path)
    print(f"Saved {top_full_path}")

    img_top_crop = img_top_full.crop((80, 110, 1550, 950))
    top_crop_path = os.path.join(fig_dir, "virtuoso_dac_top_closeup.png")
    img_top_crop.save(top_crop_path)
    print(f"Saved {top_crop_path}")

finally:
    subprocess.run(["pkill", "-9", "-f", "virtuoso"])
    xvfb.terminate()
    print("Capture complete.")
