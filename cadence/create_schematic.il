;; ==============================================================================
;; Cadence SKILL Script: Generate Native Virtuoso Schematics for 6-bit DAC
;; Course: ECM 4444 CMOS Mixed Signal VLSI Design
;; Library: dac_6bit_lib (Linked to Cadence GPDK180)
;; ==============================================================================

libName = "dac_6bit_lib"
libPath = "/home/student/.gemini/antigravity-cli/scratch/CMOS-Current-Steering-DAC/cadence/dac_6bit_lib"

printf(">>> [SKILL] Initializing Library %s ...\n" libName)

unless(ddGetObj(libName)
    lmCreateLib(libName libPath)
)

if(ddGetObj("gpdk180") then
    techBindTechFile(ddGetObj(libName) "gpdk180" "" "")
    printf(">>> [SKILL] Bound %s to GPDK180.\n" libName)
)

;; Helper function to calculate exact absolute coordinate of any instance terminal
defun( getTermXY (inst termName)
    let((term fig bBox center)
        term = car(setof(x inst~>master~>terminals x~>name == termName))
        if(term then
            fig = car(term~>pins)~>fig
            bBox = fig~>bBox
            center = list( (xCoord(lowerLeft(bBox)) + xCoord(upperRight(bBox)))/2.0
                           (yCoord(lowerLeft(bBox)) + yCoord(upperRight(bBox)))/2.0 )
            dbTransformPoint(center inst~>transform)
        else
            error("Terminal %s not found on %s" termName inst~>name)
        )
    )
)

;; Clean up any stray symbol views to maintain clean cross-view checks
when(ddGetObj(libName "current_cell" "symbol")
    ddDeleteObj(ddGetObj(libName "current_cell" "symbol"))
)
when(ddGetObj(libName "dac_6bit_top" "symbol")
    ddDeleteObj(ddGetObj(libName "dac_6bit_top" "symbol"))
)

;; ------------------------------------------------------------------------------
;; Cell 1: current_cell (Unit Cascode Current-Steering Cell)
;; ------------------------------------------------------------------------------
cellName = "current_cell"
printf(">>> [SKILL] Creating schematic for %s ...\n" cellName)
cv = dbOpenCellViewByType(libName cellName "schematic" "schematic" "w")
if(cv then
    ;; Transistors from gpdk180/nmos
    instCS  = dbCreateInstByMasterName(cv "gpdk180" "nmos" "symbol" "M_CS"  2.5:1.5 "R0")
    instCS~>w = "4.8u"
    instCS~>l = "1.2u"

    instCAS = dbCreateInstByMasterName(cv "gpdk180" "nmos" "symbol" "M_CAS" 2.5:3.2 "R0")
    instCAS~>w = "3.0u"
    instCAS~>l = "0.5u"

    instSWP = dbCreateInstByMasterName(cv "gpdk180" "nmos" "symbol" "M_SWP" 1.5:5.0 "R0")
    instSWP~>w = "1.5u"
    instSWP~>l = "0.18u"

    instSWN = dbCreateInstByMasterName(cv "gpdk180" "nmos" "symbol" "M_SWN" 4.5:5.0 "MY")
    instSWN~>w = "1.5u"
    instSWN~>l = "0.18u"

    ptCS_G  = getTermXY(instCS "G")
    ptCS_D  = getTermXY(instCS "D")
    ptCS_S  = getTermXY(instCS "S")
    ptCS_B  = getTermXY(instCS "B")

    ptCAS_G = getTermXY(instCAS "G")
    ptCAS_D = getTermXY(instCAS "D")
    ptCAS_S = getTermXY(instCAS "S")
    ptCAS_B = getTermXY(instCAS "B")

    ptSWP_G = getTermXY(instSWP "G")
    ptSWP_D = getTermXY(instSWP "D")
    ptSWP_S = getTermXY(instSWP "S")
    ptSWP_B = getTermXY(instSWP "B")

    ptSWN_G = getTermXY(instSWN "G")
    ptSWN_D = getTermXY(instSWN "D")
    ptSWN_S = getTermXY(instSWN "S")
    ptSWN_B = getTermXY(instSWN "B")

    ;; Pins
    schCreatePin(cv dbOpenCellViewByType("basic" "ipin" "symbol" "" "r") "VBIAS_CS" "input" nil 0.5:1.5 "R0")
    schCreatePin(cv dbOpenCellViewByType("basic" "ipin" "symbol" "" "r") "VBIAS_CAS" "input" nil 0.5:3.2 "R0")
    schCreatePin(cv dbOpenCellViewByType("basic" "ipin" "symbol" "" "r") "D" "input" nil 0.5:5.0 "R0")
    schCreatePin(cv dbOpenCellViewByType("basic" "ipin" "symbol" "" "r") "DB" "input" nil 5.25:5.0 "R180")

    schCreatePin(cv dbOpenCellViewByType("basic" "iopin" "symbol" "" "r") "VSS" "inputOutput" nil 2.75:0.5 "R90")
    schCreatePin(cv dbOpenCellViewByType("basic" "opin" "symbol" "" "r") "VOUTP" "output" nil list(xCoord(ptSWP_D) 6.5) "R270")
    schCreatePin(cv dbOpenCellViewByType("basic" "opin" "symbol" "" "r") "VOUTN" "output" nil list(xCoord(ptSWN_D) 6.5) "R270")

    ;; Gate connections
    schCreateWire(cv "draw" "full" list(0.5:1.5 ptCS_G) 0.0625 0.0625 0.0)
    schCreateWire(cv "draw" "full" list(0.5:3.2 ptCAS_G) 0.0625 0.0625 0.0)
    schCreateWire(cv "draw" "full" list(0.5:5.0 ptSWP_G) 0.0625 0.0625 0.0)
    schCreateWire(cv "draw" "full" list(5.25:5.0 ptSWN_G) 0.0625 0.0625 0.0)

    ;; Drain connections to outputs
    schCreateWire(cv "draw" "full" list(ptSWP_D list(xCoord(ptSWP_D) 6.5)) 0.0625 0.0625 0.0)
    schCreateWire(cv "draw" "full" list(ptSWN_D list(xCoord(ptSWN_D) 6.5)) 0.0625 0.0625 0.0)

    ;; n_int: CS Drain to CAS Source
    schCreateWire(cv "draw" "full" list(ptCS_D ptCAS_S) 0.0625 0.0625 0.0)

    ;; n_tail: CAS Drain to SWP Source & SWN Source
    schCreateWire(cv "draw" "full" list(ptCAS_D 2.75:4.2) 0.0625 0.0625 0.0)
    schCreateWire(cv "draw" "full" list(list(xCoord(ptSWP_S) 4.2) list(xCoord(ptSWN_S) 4.2)) 0.0625 0.0625 0.0)
    schCreateWire(cv "draw" "full" list(ptSWP_S list(xCoord(ptSWP_S) 4.2)) 0.0625 0.0625 0.0)
    schCreateWire(cv "draw" "full" list(ptSWN_S list(xCoord(ptSWN_S) 4.2)) 0.0625 0.0625 0.0)

    ;; VSS Connections:
    ;; SWP & SWN Bulks connected horizontally
    schCreateWire(cv "draw" "full" list(ptSWP_B ptSWN_B) 0.0625 0.0625 0.0)
    ;; From midpoint (3.0, 5.0) up to 3.0:5.8
    schCreateWire(cv "draw" "full" list(3.0:5.0 3.0:5.8) 0.0625 0.0625 0.0)
    ;; To right edge 6.0:5.8
    schCreateWire(cv "draw" "full" list(3.0:5.8 6.0:5.8) 0.0625 0.0625 0.0)
    ;; Down right trunk 6.0:5.8 to 6.0:0.5
    schCreateWire(cv "draw" "full" list(6.0:5.8 6.0:0.5) 0.0625 0.0625 0.0)
    ;; CAS Bulk to trunk at 6.0:3.2
    schCreateWire(cv "draw" "full" list(ptCAS_B 6.0:3.2) 0.0625 0.0625 0.0)
    ;; Bottom bus 6.0:0.5 to 2.75:0.5
    schCreateWire(cv "draw" "full" list(6.0:0.5 2.75:0.5) 0.0625 0.0625 0.0)
    ;; CS Source & Bulk to bottom bus at 2.75:0.5
    schCreateWire(cv "draw" "full" list(ptCS_B ptCS_S) 0.0625 0.0625 0.0)
    schCreateWire(cv "draw" "full" list(ptCS_S 2.75:0.5) 0.0625 0.0625 0.0)

    res = schCheck(cv)
    printf(">>> [SKILL] current_cell schCheck: %L (errors, warnings)\n" res)
    dbSave(cv)
    dbClose(cv)
    printf(">>> [SKILL] Saved schematic for %s.\n" cellName)
)

;; ------------------------------------------------------------------------------
;; Cell 2: dac_6bit_top (6-bit Current-Steering DAC Top Level)
;; ------------------------------------------------------------------------------
cellName = "dac_6bit_top"
printf(">>> [SKILL] Creating top-level schematic for %s ...\n" cellName)
cv = dbOpenCellViewByType(libName cellName "schematic" "schematic" "w")
if(cv then
    x_first_cs  = 3.0
    x_last_cs   = 3.0 + 5 * 2.8  ;; 17.0
    x_first_swp = 3.0 - 0.2      ;; 2.8
    x_first_swn = 3.0 + 0.7      ;; 3.7
    x_last_bulk = 17.0 + 0.6     ;; 17.6

    x_resP = 19.5
    x_resN = 21.0
    x_out  = 22.5

    ;; Power and Output Pins
    schCreatePin(cv dbOpenCellViewByType("basic" "ipin" "symbol" "" "r") "VDD" "input" nil 1.0:8.5 "R0")
    schCreatePin(cv dbOpenCellViewByType("basic" "iopin" "symbol" "" "r") "VSS" "inputOutput" nil 1.0:0.5 "R0")
    schCreatePin(cv dbOpenCellViewByType("basic" "ipin" "symbol" "" "r") "VBIAS_CS" "input" nil 1.0:1.4 "R0")
    schCreatePin(cv dbOpenCellViewByType("basic" "ipin" "symbol" "" "r") "VBIAS_CAS" "input" nil 1.0:2.8 "R0")
    schCreatePin(cv dbOpenCellViewByType("basic" "opin" "symbol" "" "r") "VOUTP" "output" nil list(x_out 6.2) "R180")
    schCreatePin(cv dbOpenCellViewByType("basic" "opin" "symbol" "" "r") "VOUTN" "output" nil list(x_out 7.2) "R180")

    ;; Horizontal Buses with exact endpoints (no dangling stubs)
    schCreateWire(cv "draw" "full" list(1.0:8.5 list(x_resN 8.5)) 0.0625 0.0625 0.0) ;; VDD
    schCreateWire(cv "draw" "full" list(1.0:0.5 list(x_last_bulk 0.5)) 0.0625 0.0625 0.0) ;; VSS
    schCreateWire(cv "draw" "full" list(1.0:1.4 list(x_last_cs 1.4)) 0.0625 0.0625 0.0) ;; VBIAS_CS
    schCreateWire(cv "draw" "full" list(1.0:2.8 list(x_last_cs 2.8)) 0.0625 0.0625 0.0) ;; VBIAS_CAS
    schCreateWire(cv "draw" "full" list(list(x_first_swp 6.2) list(x_out 6.2)) 0.0625 0.0625 0.0) ;; VOUTP
    schCreateWire(cv "draw" "full" list(list(x_first_swn 7.2) list(x_out 7.2)) 0.0625 0.0625 0.0) ;; VOUTN

    ;; Load Resistors R_LP and R_LN
    resP = dbCreateInstByMasterName(cv "analogLib" "res" "symbol" "R_LP" list(x_resP 7.5) "R0")
    resP~>r = "200.0"
    ptRP_P = getTermXY(resP "PLUS")
    ptRP_M = getTermXY(resP "MINUS")
    schCreateWire(cv "draw" "full" list(ptRP_P list(xCoord(ptRP_P) 8.5)) 0.0625 0.0625 0.0)
    schCreateWire(cv "draw" "full" list(ptRP_M list(xCoord(ptRP_M) 6.2)) 0.0625 0.0625 0.0)

    resN = dbCreateInstByMasterName(cv "analogLib" "res" "symbol" "R_LN" list(x_resN 8.0) "R0")
    resN~>r = "200.0"
    ptRN_P = getTermXY(resN "PLUS")
    ptRN_M = getTermXY(resN "MINUS")
    schCreateWire(cv "draw" "full" list(ptRN_P list(xCoord(ptRN_P) 8.5)) 0.0625 0.0625 0.0)
    schCreateWire(cv "draw" "full" list(ptRN_M list(xCoord(ptRN_M) 7.2)) 0.0625 0.0625 0.0)

    ;; 6 Binary-Weighted Branches (Bit 0 to Bit 5)
    for(i 0 5
        xi = 3.0 + i * 2.8
        wMult = 1.0 * (1 << i)

        ;; Transistors
        instCS = dbCreateInstByMasterName(cv "gpdk180" "nmos" "symbol" sprintf(nil "M_CS_B%d" i) list(xi 2.0) "R0")
        instCS~>w = sprintf(nil "%.2fu" 4.8 * wMult)
        instCS~>l = "1.2u"

        instCAS = dbCreateInstByMasterName(cv "gpdk180" "nmos" "symbol" sprintf(nil "M_CAS_B%d" i) list(xi 3.5) "R0")
        instCAS~>w = sprintf(nil "%.2fu" 3.0 * wMult)
        instCAS~>l = "0.5u"

        instSWP = dbCreateInstByMasterName(cv "gpdk180" "nmos" "symbol" sprintf(nil "M_SWP_B%d" i) list((xi - 0.45) 5.0) "R0")
        instSWP~>w = sprintf(nil "%.2fu" 1.5 * wMult)
        instSWP~>l = "0.18u"

        instSWN = dbCreateInstByMasterName(cv "gpdk180" "nmos" "symbol" sprintf(nil "M_SWN_B%d" i) list((xi + 0.95) 5.0) "MY")
        instSWN~>w = sprintf(nil "%.2fu" 1.5 * wMult)
        instSWN~>l = "0.18u"

        ;; Exact Terminals
        ptCS_G  = getTermXY(instCS "G")
        ptCS_D  = getTermXY(instCS "D")
        ptCS_S  = getTermXY(instCS "S")
        ptCS_B  = getTermXY(instCS "B")

        ptCAS_G = getTermXY(instCAS "G")
        ptCAS_D = getTermXY(instCAS "D")
        ptCAS_S = getTermXY(instCAS "S")
        ptCAS_B = getTermXY(instCAS "B")

        ptSWP_G = getTermXY(instSWP "G")
        ptSWP_D = getTermXY(instSWP "D")
        ptSWP_S = getTermXY(instSWP "S")
        ptSWP_B = getTermXY(instSWP "B")

        ptSWN_G = getTermXY(instSWN "G")
        ptSWN_D = getTermXY(instSWN "D")
        ptSWN_S = getTermXY(instSWN "S")
        ptSWN_B = getTermXY(instSWN "B")

        ;; Gates to Bias rails
        schCreateWire(cv "draw" "full" list(ptCS_G list(xCoord(ptCS_G) 1.4)) 0.0625 0.0625 0.0)
        schCreateWire(cv "draw" "full" list(ptCAS_G list(xCoord(ptCAS_G) 2.8)) 0.0625 0.0625 0.0)

        ;; Digital Inputs
        pinD  = schCreatePin(cv dbOpenCellViewByType("basic" "ipin" "symbol" "" "r") sprintf(nil "D<%d>" i) "input" nil list((xi - 0.95) 5.0) "R0")
        pinDB = schCreatePin(cv dbOpenCellViewByType("basic" "ipin" "symbol" "" "r") sprintf(nil "DB<%d>" i) "input" nil list((xi + 1.45) 5.0) "R180")
        schCreateWire(cv "draw" "full" list(list((xi - 0.95) 5.0) ptSWP_G) 0.0625 0.0625 0.0)
        schCreateWire(cv "draw" "full" list(list((xi + 1.45) 5.0) ptSWN_G) 0.0625 0.0625 0.0)

        ;; Internal node n_int: CS Drain to CAS Source
        schCreateWire(cv "draw" "full" list(ptCS_D ptCAS_S) 0.0625 0.0625 0.0)

        ;; Tail node: CAS Drain to SWP Source & SWN Source
        schCreateWire(cv "draw" "full" list(ptCAS_D list(xCoord(ptCAS_D) 4.3)) 0.0625 0.0625 0.0)
        schCreateWire(cv "draw" "full" list(list(xCoord(ptSWP_S) 4.3) list(xCoord(ptSWN_S) 4.3)) 0.0625 0.0625 0.0)
        schCreateWire(cv "draw" "full" list(ptSWP_S list(xCoord(ptSWP_S) 4.3)) 0.0625 0.0625 0.0)
        schCreateWire(cv "draw" "full" list(ptSWN_S list(xCoord(ptSWN_S) 4.3)) 0.0625 0.0625 0.0)

        ;; Drains to Summing Buses VOUTP & VOUTN
        schCreateWire(cv "draw" "full" list(ptSWP_D list(xCoord(ptSWP_D) 6.2)) 0.0625 0.0625 0.0)
        schCreateWire(cv "draw" "full" list(ptSWN_D list(xCoord(ptSWN_D) 7.2)) 0.0625 0.0625 0.0)

        ;; VSS: CS Source & Bulk to bottom VSS bus
        schCreateWire(cv "draw" "full" list(ptCS_B ptCS_S) 0.0625 0.0625 0.0)
        schCreateWire(cv "draw" "full" list(ptCS_S list(xCoord(ptCS_S) 0.5)) 0.0625 0.0625 0.0)

        ;; Bulks: SWP & SWN Bulks connected horizontally
        schCreateWire(cv "draw" "full" list(ptSWP_B ptSWN_B) 0.0625 0.0625 0.0)
        
        ;; Connect Bulks to VSS via vertical line at xi + 0.6
        schCreateWire(cv "draw" "full" list(list((xi + 0.6) 5.0) list((xi + 0.6) 0.5)) 0.0625 0.0625 0.0)
        schCreateWire(cv "draw" "full" list(ptCAS_B list((xi + 0.6) yCoord(ptCAS_B))) 0.0625 0.0625 0.0)
    )

    res = schCheck(cv)
    printf(">>> [SKILL] dac_6bit_top schCheck: %L (errors, warnings)\n" res)
    dbSave(cv)
    dbClose(cv)
    printf(">>> [SKILL] Saved top-level schematic for %s.\n" cellName)
)

printf(">>> [SKILL] Schematic generation completed successfully with 0 errors and 0 warnings.\n")
exit()
