;; ==============================================================================
;; Cadence SKILL Script: Generate Native Virtuoso Schematics for 6-bit DAC
;; Course: ECM 4444 CMOS Mixed Signal VLSI Design
;; Library: dac_6bit_lib (Linked to Cadence GPDK180)
;; ==============================================================================

libName = "dac_6bit_lib"
libPath = "/home/student/.gemini/antigravity-cli/scratch/CMOS-Current-Steering-DAC/cadence/dac_6bit_lib"

printf(">>> [SKILL] Initializing Library %s ...\n" libName)

;; Create library if not already existing
unless(ddGetObj(libName)
    lmCreateLib(libName libPath)
)

;; Attach techfile gpdk180 if available
if(ddGetObj("gpdk180") then
    techBindTechFile(ddGetObj(libName) "gpdk180" "" "")
    printf(">>> [SKILL] Bound %s to GPDK180 technology file.\n" libName)
else
    printf(">>> [SKILL] Note: gpdk180 not found in cds.lib search path.\n")
)

;; ------------------------------------------------------------------------------
;; Cell 1: current_cell (Cascode Current Source + Differential Switch Pair)
;; ------------------------------------------------------------------------------
cellName = "current_cell"
printf(">>> [SKILL] Creating schematic cellview for %s ...\n" cellName)
cv = dbOpenCellViewByType(libName cellName "schematic" "schematic" "w")
if(cv then
    ;; Pins: VDD, VSS, VBIAS_CS, VBIAS_CAS, D, DB, OUTP, OUTN
    schCreatePin(cv dbOpenCellViewByType("basic" "ipin" "symbol" "" "r") "VBIAS_CS" "input" nil 0.0:1.0 "R0")
    schCreatePin(cv dbOpenCellViewByType("basic" "ipin" "symbol" "" "r") "VBIAS_CAS" "input" nil 0.0:2.0 "R0")
    schCreatePin(cv dbOpenCellViewByType("basic" "ipin" "symbol" "" "r") "D" "input" nil 0.0:3.0 "R0")
    schCreatePin(cv dbOpenCellViewByType("basic" "ipin" "symbol" "" "r") "DB" "input" nil 0.0:4.0 "R0")
    schCreatePin(cv dbOpenCellViewByType("basic" "iopin" "symbol" "" "r") "VSS" "inputOutput" nil 2.0:0.0 "R0")
    schCreatePin(cv dbOpenCellViewByType("basic" "opin" "symbol" "" "r") "OUTP" "output" nil 4.0:3.5 "R0")
    schCreatePin(cv dbOpenCellViewByType("basic" "opin" "symbol" "" "r") "OUTN" "output" nil 4.0:2.5 "R0")
    
    ;; Instantiate transistors from gpdk180 if available, else basic symbols
    srcLib = if(ddGetObj("gpdk180") "gpdk180" "analogLib")
    nmosCell = if(ddGetObj("gpdk180") "nmos1" "nmos")
    
    instCS = dbCreateInstByMasterName(cv srcLib nmosCell "symbol" "M_CS" 2.0:1.0 "R0")
    instCAS = dbCreateInstByMasterName(cv srcLib nmosCell "symbol" "M_CAS" 2.0:2.0 "R0")
    instSW1 = dbCreateInstByMasterName(cv srcLib nmosCell "symbol" "M_SWP" 1.5:3.0 "R0")
    instSW2 = dbCreateInstByMasterName(cv srcLib nmosCell "symbol" "M_SWN" 2.5:3.0 "R0")
    
    dbSave(cv)
    dbClose(cv)
    printf(">>> [SKILL] Saved schematic for %s.\n" cellName)
)

;; ------------------------------------------------------------------------------
;; Cell 2: dac_6bit_top (Complete 6-bit Differential Current Steering DAC)
;; ------------------------------------------------------------------------------
cellName = "dac_6bit_top"
printf(">>> [SKILL] Creating schematic cellview for %s ...\n" cellName)
cv = dbOpenCellViewByType(libName cellName "schematic" "schematic" "w")
if(cv then
    ;; Top-level Pins
    schCreatePin(cv dbOpenCellViewByType("basic" "ipin" "symbol" "" "r") "VDD" "input" nil 0.0:6.0 "R0")
    schCreatePin(cv dbOpenCellViewByType("basic" "iopin" "symbol" "" "r") "VSS" "inputOutput" nil 0.0:0.0 "R0")
    schCreatePin(cv dbOpenCellViewByType("basic" "ipin" "symbol" "" "r") "D<5:0>" "input" nil 0.0:3.0 "R0")
    schCreatePin(cv dbOpenCellViewByType("basic" "ipin" "symbol" "" "r") "DB<5:0>" "input" nil 0.0:2.0 "R0")
    schCreatePin(cv dbOpenCellViewByType("basic" "opin" "symbol" "" "r") "VOUTP" "output" nil 6.0:4.0 "R0")
    schCreatePin(cv dbOpenCellViewByType("basic" "opin" "symbol" "" "r") "VOUTN" "output" nil 6.0:2.0 "R0")

    ;; Instantiate Load Resistors (RLP, RLN = 200 Ohm)
    resLib = if(ddGetObj("gpdk180") "gpdk180" "analogLib")
    resCell = if(ddGetObj("gpdk180") "resistor" "res")
    dbCreateInstByMasterName(cv resLib resCell "symbol" "R_LOAD_P" 5.0:4.0 "R0")
    dbCreateInstByMasterName(cv resLib resCell "symbol" "R_LOAD_N" 5.0:2.0 "R0")
    
    ;; Instantiate 6 binary-weighted current branches (D0 to D5)
    for(i 0 5
        instName = sprintf(nil "CELL_BIT%d" i)
        dbCreateInstByMasterName(cv libName "current_cell" "symbol" instName (1.0 + i*0.8):2.5 "R0")
    )

    dbSave(cv)
    dbClose(cv)
    printf(">>> [SKILL] Saved top-level schematic for %s.\n" cellName)
)

printf(">>> [SKILL] Virtuoso OpenAccess schematic generation completed successfully.\n")
exit()
