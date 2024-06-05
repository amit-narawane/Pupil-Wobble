# Python ZOS-API ray tracing to examine pupil wobble
# Author: Amit Narawane
# 06/05/2024
# Izatt Lab, Duke University

import numpy as np

import clr
from System import Enum, Int32, Double

from ZOS_setup import PythonStandaloneApplication
from ZMXconfig import BaseConfig

cfg = BaseConfig()

if __name__ == '__main__':
    zos = PythonStandaloneApplication()
    
    # load local variables
    ZOSAPI = zos.ZOSAPI
    TheApplication = zos.TheApplication
    TheSystem = zos.TheSystem

    TheSystem.LoadFile(cfg.zemax_file, False)
    MCE = TheSystem.MCE

    if cfg.scan_type == 'raster':
        # Generate raster scans
        bscan_pos = np.linspace(cfg.scan_range[0], cfg.scan_range[1], cfg.n_bscans)
        points = np.linspace(cfg.scan_range[0], cfg.scan_range[1], cfg.n_points)

        if hasattr(cfg, 'wobble_file'):
            wobble_data = np.squeeze(np.load(cfg.wobble_file))
            scan_points = np.zeros((cfg.n_bscans,cfg.n_points,4))
            for bscan in range(cfg.n_bscans):
                for point in range(cfg.n_points):
                    scan_points[bscan,point,0] = points[point]
                    scan_points[bscan,point,1] = bscan_pos[bscan]
                    scan_points[bscan,point,2] = -wobble_data[bscan,point,1] / cfg.fsm_slope
                    scan_points[bscan,point,3] = wobble_data[bscan,point,0] / cfg.fsm_slope

        else:
            scan_points = np.zeros((cfg.n_bscans,cfg.n_points,2))
            for bscan in range(cfg.n_bscans):
                for point in points:
                    scan_points[bscan,:,0] = points
                    scan_points[bscan,:,1] = bscan_pos[bscan]

    elif cfg.scan_type == 'radial':
        # Generate radial scans
        bscan_thetas = np.linspace(cfg.radial_range[0], cfg.radial_range[1], cfg.n_bscans, endpoint=False)
        points = np.linspace(cfg.scan_range[0], cfg.scan_range[1], cfg.n_points)

        if cfg.FSM == False:
            scan_points = np.zeros((cfg.n_bscans,cfg.n_points,2))
            for bscan in range(cfg.n_bscans):
                scan_points[bscan,:,0] = points*np.cos(bscan_thetas[bscan])
                scan_points[bscan,:,1] = points*np.sin(bscan_thetas[bscan])

        else:
            fsm_thetas = np.linspace(cfg.fsm_range[0], cfg.fsm_range[1], cfg.n_bscans, endpoint=False)
            scan_points = np.zeros((cfg.n_bscans,cfg.n_points,4))

            for bscan in range(cfg.n_bscans):
                scan_points[bscan,:,0] = points*np.cos(bscan_thetas[bscan])
                scan_points[bscan,:,1] = points*np.sin(bscan_thetas[bscan])

            if hasattr(cfg, 'wobble_file'):
                wobble_data = np.squeeze(np.load(cfg.wobble_file))
                for bscan in range(cfg.n_bscans):
                    for point in range(cfg.n_points):
                        scan_points[bscan,point,2] = -wobble_data[bscan,point,1] / cfg.fsm_slope
                        scan_points[bscan,point,3] = wobble_data[bscan,point,0] / cfg.fsm_slope
            else:
                for bscan in range(cfg.n_bscans):
                    scan_points[bscan,:,2] = cfg.entry_offset*np.cos(fsm_thetas[bscan]) / cfg.fsm_slope
                    scan_points[bscan,:,3] = cfg.entry_offset*np.sin(fsm_thetas[bscan]) / cfg.fsm_slope
    
    pupil_vals = []

    for bscan in range(cfg.n_bscans):
        print(f'---Starting bscan {bscan+1}/{cfg.n_bscans}---')

        # Set up MCE operands
        MCE.DeleteAllConfigurations()

        # Galvo Parameters
        x_galvo = MCE.GetOperandAt(1)
        x_galvo.ChangeType(ZOSAPI.Editors.MCE.MultiConfigOperandType.PRAM)
        x_galvo.Param1 = cfg.x_galvo_sur
        x_galvo.Param2 = 3
        MCE.AddOperand()
        y_galvo = MCE.GetOperandAt(2)
        y_galvo.ChangeType(ZOSAPI.Editors.MCE.MultiConfigOperandType.PRAM)
        y_galvo.Param1 = cfg.y_galvo_sur
        y_galvo.Param2 = 4
        MCE.AddOperand()

        if cfg.FSM:
        # FSM Parameters
            fsm_tilt_x = MCE.GetOperandAt(3)
            fsm_tilt_x.ChangeType(ZOSAPI.Editors.MCE.MultiConfigOperandType.PRAM)
            fsm_tilt_x.Param1 = cfg.fsm_sur
            fsm_tilt_x.Param2 = 3 # x tilt
            MCE.AddOperand()
            fsm_tilt_y = MCE.GetOperandAt(4)
            fsm_tilt_y.ChangeType(ZOSAPI.Editors.MCE.MultiConfigOperandType.PRAM)
            fsm_tilt_y.Param1 = cfg.fsm_sur
            fsm_tilt_y.Param2 = 4 # y tilt


        for point in range(cfg.n_points):
            MCE.AddConfiguration(False)
            x_galvo.GetOperandCell(point+2).DoubleValue = scan_points[bscan,point,0]
            y_galvo.GetOperandCell(point+2).DoubleValue = scan_points[bscan,point,1]
            if cfg.FSM:
                fsm_tilt_x.GetOperandCell(point+2).DoubleValue = scan_points[bscan,point,2]
                fsm_tilt_y.GetOperandCell(point+2).DoubleValue = scan_points[bscan,point,3]

        MCE.DeleteConfiguration(1)

        pupil_bscan = []

        for point in range(cfg.n_points):
            print(f'Starting point {point+1}/{cfg.n_points}')
            # Set configuration
            MCE.SetCurrentConfiguration(point+1)

            pupil_point = []
            
            # Create ray trace
            raytrace = TheSystem.Tools.OpenBatchRayTrace()

            if cfg.pupil:
                nsur = cfg.pupil_plane
            else:
                nsur = TheSystem.LDE.NumberOfSurfaces-1

            if cfg.n_ring == 1:
                p = np.zeros((1,2))
            else:
                ring_thetas = np.linspace(0, 2*np.pi, cfg.n_ring, endpoint=False)
                p = np.column_stack((np.cos(ring_thetas), np.sin(ring_thetas)))

            normUnPolData = raytrace.CreateNormUnpol(cfg.n_ring, ZOSAPI.Tools.RayTrace.RaysType.Real, nsur)
            normUnPolData.ClearData()

            for i in range(cfg.n_ring):
                normUnPolData.AddRay(Int32(cfg.waveNumber), Double(cfg.hx), Double(cfg.hy), Double(p[i,0]), Double(p[i,1]), Enum.Parse(ZOSAPI.Tools.RayTrace.OPDMode, "None"))
            
            raytrace.RunAndWaitForCompletion()

            # Read results
            normUnPolData.StartReadingResults()

            sysInt = Int32(1)
            sysDbl = Double(1.0)

            for i in range(cfg.n_ring):
                output = normUnPolData.ReadNextResult(sysInt, sysInt, sysInt, sysDbl, sysDbl, sysDbl, sysDbl, sysDbl, sysDbl, sysDbl, sysDbl, sysDbl, sysDbl, sysDbl)
                (valid, ray_idx, error_code, vignette_code, x, y, z, l, m, n, l2, m2, n2, opd, intensity) = output

                if valid == True:
                    pupil_point.append([x,y])
                else:
                    print(f'Ray trace for {ray_idx} failed')

            raytrace.Close()

            pupil_bscan.append(pupil_point)
        
        pupil_vals.append(pupil_bscan)

    if hasattr(cfg, 'pupil_file'):
        np.save(cfg.pupil_file, pupil_vals)

    del zos
    zos = None