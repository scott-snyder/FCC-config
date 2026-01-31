from FCC_config.ComponentAccumulator import ComponentAccumulator
import Configurables as C
from .DetIDs import detIDs


# ECAL barrel parameters for digitization
ecalBarrelLayers = 11

# e-, 10 GeV, flat theta, B field off
# ecalBarrelSamplingFraction = [0.3800493723322256,  #  0
#                               0.13494147915064658, #  1
#                               0.142866851721152,   #  2
#                               0.14839315921940666, #  3
#                               0.15298362570665006, #  4
#                               0.15709704561942747, #  5
#                               0.16063717490147533, #  6
#                               0.1641723795419055,  #  7
#                               0.16845490287689746, #  8
#                               0.17111520115997653, #  9
#                               0.1730605163148862,  # 10
#                               ]

#  e-, 20 GeV, flat theta, B field on; LAr+Pb
ecalBarrelSamplingFraction = [0.3790943904011486,  #  0
                              0.1355600584387894,  #  1
                              0.14628210607758893, #  2
                              0.15274136994224854, #  3
                              0.15817255837886351, #  4
                              0.16290355087527258, #  5
                              0.1674201708055751,  #  6
                              0.1715846423182708,  #  7
                              0.17558662106635545, #  8
                              0.18002243792463576, #  9
                              0.18288329976007917, # 10
                              ]

# LKr+W
# ecalBarrelSamplingFraction = [0.4806159038189229,  #  0
#                               0.2822724529941907,  #  1
#                               0.29324811578621524, #  2
#                               0.2996356722403102,  #  3
#                               0.3047116566166906,  #  4
#                               0.3090324459212472,  #  5
#                               0.3133282052725273,  #  6
#                               0.3173868504112048,  #  7
#                               0.3215311396527887,  #  8
#                               0.32516920330802673, #  9
#                               0.3318488881234955,  # 10
#                               ]

ecalBarrelUpstreamParameters = [[0.028158491043365624,
                                 -1.564259408365951,
                                 -76.52312805346982,
                                 0.7442903558010191,
                                 -34.894692961350195,
                                 -74.19340877431723]]
ecalBarrelDownstreamParameters = [[0.00010587711361028165,
                                   0.0052371999097777355,
                                   0.69906696456064,
                                   -0.9348243433360095,
                                   -0.0364714212117143,
                                   8.360401126995626]]


if ecalBarrelSamplingFraction and len(ecalBarrelSamplingFraction) > 0:
    assert (ecalBarrelLayers == len(ecalBarrelSamplingFraction))


# ECAL endcap parameters for digitization
# the turbine endcap has calibration "layers" in the both the z and radial
# directions, for each of the three wheels.  So the total number of layers
# is given by:
#
#   ECalEndcapNumCalibZLayersWheel1*ECalEndcapNumCalibRhoLayersWheel1
#  +ECalEndcapNumCalibZLayersWheel2*ECalEndcapNumCalibRhoLayersWheel2
#  +ECalEndcapNumCalibZLayersWheel3*ECalEndcapNumCalibRhoLayersWheel3
#
# which in the current design is 5*10+1*14+1*34 = 98
# NB some cells near the inner and outer edges of the calorimeter are difficult
# to calibrate as they are not part of the core of well-contained showers.
# The calibrated values can be <0 or >1 for such cells, so these nonsensical
# numbers are replaced by 1
ecalEndcapLayers = 98
ecalEndcapSamplingFraction = [
    0.0897818,  0.221318,   0.0820002, 0.994281, 0.0414437, # 0  wheel 1 zlay 0
    0.1148,     0.178831,   0.142449,  0.181206, 0.342843,  # 5
    0.137479,   0.176479,   0.153273,  0.195836, 0.0780405, # 10 wheel 1 zlay 1
    0.150202,   0.17846,    0.164886,  0.175758, 0.10836,   # 15
    0.160243,   0.183373,   0.171818,  0.194848, 0.111899,  # 20 wheel 1 zlay 2
    0.170704,   0.188455,   0.178164,  0.209113, 0.105241,  # 25
    0.180637,   0.192206,   0.186096,  0.211962, 0.112019,  # 30 wheel 1 zlay 3
    0.180344,   0.195684,   0.190778,  0.218259, 0.118516,  # 35
    0.207786,   0.204474,   0.207048,  0.225913, 0.111325,  # 40 wheel 1 zlay 4
    0.147875,   0.195625,   0.173326,  0.175449, 0.104087,  # 45
    0.153645,   0.161263,   0.165499,  0.171758, 0.175789,  # 50 wheel 2
    0.180657,   0.184563,   0.187876,  0.191762, 0.19426,   # 55
    0.197959,   0.199021,   0.204428,  0.195709,            # 60
    0.151751,   0.171477,   0.165509,  0.172565, 0.172961,  # 64 wheel 3
    0.175534,   0.177989,   0.18026,   0.181898, 0.183912,  # 69
    0.185654,   0.187515,   0.190408,  0.188794, 0.193699,  # 74
    0.192287,   0.19755,    0.190943,  0.218553, 0.161085,  # 79
    0.373086,   0.122495,   0.21103,   1.0,      0.138686,  # 84
    0.0545171,  1.0,        1.0,       0.227945, 0.0122872, # 89
    0.00437334, 0.00363533, 1.0,       1.0,                 # 94
    ]
if ecalEndcapSamplingFraction and len(ecalEndcapSamplingFraction) > 0:
    assert (ecalEndcapLayers == len(ecalEndcapSamplingFraction))


def CalibrateECalBarrel (flags, name = 'CalibrateECalBarrel'):
    return C.CalibrateInLayersTool(name,
                                   samplingFraction=ecalBarrelSamplingFraction,
                                   readoutName=flags.ECal.Barrel.readoutName,
                                   layerFieldName="layer")


def CalibrateECalEndcap (flags, name = 'CalibrateECalEndcap'):
    return C.CalibrateInLayersTool(name,
                                   samplingFraction=ecalEndcapSamplingFraction,
                                   readoutName=flags.ECal.Endcap.readoutName,
                                   layerFieldName="layer")


def CalibrateHCalBarrel (flags, name = 'CalibrateHCalBarrel'):
    return C.CalibrateCaloHitsTool(name,
                                   invSamplingFraction=29.4202)


def CalibrateHCalEndcap (flags, name = 'CalibrateHCalEndcap'):
    return C.CalibrateCaloHitsTool(name,
                                   invSamplingFraction=29.4202)  # FIXME: to be updated for ddsim


def CellPositionsECalBarrel (flags,
                             name = 'CellPositionsECalBarrel',
                             readoutName = None):
    if readoutName is None: readoutName = flags.ECal.Barrel.readoutName
    return C.CellPositionsECalBarrelModuleThetaSegTool(name,
                                                       readoutName=readoutName)


def CellPositionsECalEndcap (flags,
                             name = 'CellPositionsECalEndcap',
                             readoutName = None):
    if readoutName is None: readoutName = flags.ECal.Endcap.readoutName
    return C.CellPositionsECalEndcapTurbineSegTool(name,
                                                   readoutName=readoutName)


def CellPositionsHCalBarrel (flags,
                             name = 'CellPositionsHCalBarrel',
                             readoutName = None):
    if readoutName is None: readoutName = flags.HCal.Barrel.readoutName
    return C.CellPositionsHCalPhiThetaSegTool(name,
                                              readoutName=readoutName,
                                              detectorName='HCalBarrel')


def CellPositionsHCalEndcap (flags,
                             name = 'CellPositionsHCalEndcap',
                             readoutName = None):
    if readoutName is None: readoutName = flags.HCal.Endcap.readoutName
    return C.CellPositionsHCalPhiThetaSegTool(name,
                                              readoutName=readoutName,
                                              detectorName='HCalThreePartsEndcap',
                                              numLayersHCalThreeParts=[6, 9, 22])


def ReadCrosstalkMap (flags, name = 'ReadCrosstalkMap'):
    return C.ReadCaloCrosstalkMap(name,
                                  detID = detIDs(flags, 'ECAL_Barrel'),
                                  fileName=flags.dataFilesUrl + "xtalk_neighbours_map_ecalB_thetamodulemerged.root")


def eCalBarrelNoiseTool (flags, name = 'ecalBarrelNoiseTool'):
    return C.NoiseCaloCellsVsThetaFromFileTool (name,
                                                cellPositionsTool=CellPositionsECalBarrel(flags),
                                                readoutName=flags.ECal.Barrel.readoutName,
                                                noiseFileName=flags.ECal.Barrel.noisePath,
                                                elecNoiseRMSHistoName=flags.ECal.Barrel.noiseRMSHistName,
                                                setNoiseOffset=False,
                                                activeFieldName="layer",
                                                addPileup=False,
                                                filterNoiseThreshold=flags.ECal.Barrel.filterNoiseThreshold,
                                                useAbsInFilter=True,
                                                numRadialLayers=ecalBarrelLayers,
                                                scaleFactor=1 / 1000.,  # MeV to GeV
                                                )


def eCalBarrelGeometryTool (flags, name = 'ecalBarrelGeometryTool',
                            readoutName = None):
    if readoutName is None: readoutName = flags.ECal.Barrel.readoutName
    return C.TubeLayerModuleThetaCaloTool(name,
                                          readoutName=readoutName,
                                          activeVolumeName="LAr_sensitive",
                                          activeFieldName="layer",
                                          activeVolumesNumber=ecalBarrelLayers,
                                          fieldNames=["system"],
                                          fieldValues=[detIDs(flags, 'ECAL_Barrel')],
                                          )

class CaloCellIndexerSvc (C.k4__recCalo__CaloCellIndexerSvc):
    def mergeTo (self, old):
        if not isinstance (old, CaloCellIndexerSvc): return False
        oldnames = [x.name() for x in old.GeoTools]
        for tool in self.GeoTools:
            if tool.name() not in oldnames:
                old.GeoTools.append (tool)
        return True

def CaloCellIndexerSvcCfg (flags, name = 'k4::recCalo::CaloCellIndexerSvc'):
    cfg = ComponentAccumulator()
    svc = CaloCellIndexerSvc (name,
                              GeoTools = [eCalBarrelGeometryTool(flags)])

    cfg.addSvc (svc)
    return cfg


def _keepCells (flags, kw, readoutName):
    cfg = ComponentAccumulator()
    keep = []
    if flags.saveCells:
        keep.append (kw['cells'])
    if flags.saveHits and flags.saveCells:
        keep.append (kw['links'])
    if flags.saveHits:
        keep.append (f'{readoutName}Contributions')
    if keep:
        from FCC_config.CoreConfig import IOSvcCfg
        cfg.merge(IOSvcCfg(flags, keep=keep))
    return cfg


def CreateECalBarrelCellsCfg (flags,
                              name = 'CreatePositionedECalBarrelCells',
                              doCellCalibration = True,
                              addNoise = False,
                              addCrosstalk = None,
                              filterCellNoise = False,
                              cellsNameSuffix = '',
                              readoutName = None,
                              alg = C.CreatePositionedCaloCells,
                              **kw):

    cfg = ComponentAccumulator()
    if readoutName is None: readoutName = flags.ECal.Barrel.readoutName
    if addCrosstalk is None: addCrosstalk = flags.ECal.Barrel.addCrosstalk

    kw.setdefault('cells', readoutName + flags.cellsNamePart + cellsNameSuffix)
    kw.setdefault('links', kw['cells'] + flags.linksNamePart)
    kw.setdefault('hits', readoutName)

    if doCellCalibration:
        kw['calibTool'] = CalibrateECalBarrel(flags)

    if addCrosstalk:
        cfg.merge (CaloCellIndexerSvcCfg (flags))
        kw['crosstalkTool'] = ReadCrosstalkMap(flags)

    if addNoise:
        kw['noiseTool'] = eCalBarrelNoiseTool (flags)
        kw['geometryTool'] = eCalBarrelGeometryTool (flags, readoutName=readoutName)

    if readoutName == flags.ECal.Barrel.readoutName:
        kw['positionsTool'] = CellPositionsECalBarrel(flags)
    else:
        kw['positionsTool'] = CellPositionsECalBarrel(flags,
                                                      name='CellPositions' + readoutName,
                                                      readoutName=readoutName)

    cfg.addAlg(alg(name,
                   doCellCalibration=doCellCalibration,
                   addCrosstalk=addCrosstalk,
                   addCellNoise=addNoise,
                   filterCellNoise=filterCellNoise,
                   **kw
                   ))

    cfg.merge (_keepCells (flags, kw, readoutName))
    return cfg
                           

def CreateECalEndcapCellsCfg (flags,
                              name = 'CreatePositionedECalEndcapCells',
                              doCellCalibration = True,
                              cellsNameSuffix = '',
                              readoutName = None,
                              **kw):
    cfg = ComponentAccumulator()
    if readoutName is None: readoutName = flags.ECal.Endcap.readoutName

    kw.setdefault('cells', readoutName + flags.cellsNamePart + cellsNameSuffix)
    kw.setdefault('links', kw['cells'] + flags.linksNamePart)
    kw.setdefault('hits', readoutName)

    if doCellCalibration:
        kw['calibTool'] = CalibrateECalEndcap(flags)

    cfg.addAlg(C.CreatePositionedCaloCells(name,
                                           doCellCalibration=doCellCalibration,
                                           positionsTool=CellPositionsECalEndcap(flags),
                                           addCrosstalk=False,
                                           addCellNoise=False,
                                           filterCellNoise=False,
                                           noiseTool=None,
                                           **kw
                                           ))

    cfg.merge (_keepCells (flags, kw, readoutName))
    return cfg


def CreateHCalBarrelCellsCfg (flags,
                              name = 'CreatePositionedHCalBarrelCells',
                              doCellCalibration = True,
                              cellsNameSuffix = '',
                              readoutName = None,
                              **kw):
    cfg = ComponentAccumulator()
    if readoutName is None: readoutName = flags.HCal.Barrel.readoutName

    kw.setdefault('cells', readoutName + flags.cellsNamePart + cellsNameSuffix)
    kw.setdefault('links', kw['cells'] + flags.linksNamePart)
    kw.setdefault('hits', readoutName)

    if doCellCalibration:
        kw['calibTool'] = CalibrateHCalBarrel(flags)

    cfg.addAlg(C.CreatePositionedCaloCells(name,
                                           doCellCalibration=doCellCalibration,
                                           addCellNoise=False,
                                           positionsTool=CellPositionsHCalBarrel(flags),
                                           **kw
                                           ))

    cfg.merge (_keepCells (flags, kw, readoutName))
    return cfg


def CreateHCalEndcapCellsCfg (flags,
                              name = 'CreatePositionedHCalEndcapCells',
                              doCellCalibration = True,
                              cellsNameSuffix = '',
                              readoutName = None,
                              **kw):
    cfg = ComponentAccumulator()
    if readoutName is None: readoutName = flags.HCal.Endcap.readoutName

    kw.setdefault('cells', readoutName + flags.cellsNamePart + cellsNameSuffix)
    kw.setdefault('links', kw['cells'] + flags.linksNamePart)
    kw.setdefault('hits', readoutName)

    if doCellCalibration:
        kw['calibTool'] = CalibrateHCalEndcap(flags)

    cfg.addAlg(C.CreatePositionedCaloCells(name,
                                           doCellCalibration=doCellCalibration,
                                           addCellNoise=False,
                                           positionsTool=CellPositionsHCalEndcap(flags),
                                           **kw
                                           ))

    cfg.merge (_keepCells (flags, kw, readoutName))
    return cfg


                           
def redoECalSegmentationCfg(flags,
                            name = 'ReSegmentationEcal',
                            newReadoutName = 'ECalBarrelModuleThetaMerged2',
                            newCellsName = 'ECalBarrelCellsMerged'):

    cfg = ComponentAccumulator()
    cfg.addAlg(C.RedoSegmentation(name,
                                  # old bitfield (readout)
                                  oldReadoutName=flags.ECal.Barrel.readoutName,
                                  # specify which fields are going to be altered (deleted/rewritten)
                                  oldSegmentationIds=['module', 'theta'],
                                  # new bitfield (readout), with new segmentation (merged modules and theta cells)
                                  newReadoutName=newReadoutName,
                                  debugPrint=200,
                                  inhits=flags.ECal.Barrel.readoutName + flags.cellsNamePart,
                                  outhits=newCellsName))
    return cfg



class Flags:
    pass
def defineCaloCellFlags(flags):
    flags.ECal = Flags()
    flags.ECal.Barrel = Flags()
    flags.ECal.Barrel.readoutName = 'ECalBarrelModuleThetaMerged'      # barrel, original segmentation (baseline)
    flags.ECal.Barrel.cellsName = flags.ECal.Barrel.readoutName + flags.cellsNamePart
    flags.ECal.Barrel.linksName = flags.ECal.Barrel.cellsName + flags.linksNamePart
    flags.ECal.Barrel.addCrosstalk = False
    flags.ECal.Barrel.noisePath = flags.dataFiles + "elecNoise_ecalBarrelFCCee_theta.root"
    flags.ECal.Barrel.noiseRMSHistName = 'h_elecNoise_fcc_'
    flags.ECal.Barrel.filterNoiseThreshold = -1
    flags.ECal.Endcap = Flags()
    flags.ECal.Endcap.readoutName = 'ECalEndcapTurbine'                # endcap, turbine-like (baseline)
    flags.ECal.Endcap.cellsName = flags.ECal.Endcap.readoutName + flags.cellsNamePart
    flags.ECal.Endcap.linksName = flags.ECal.Endcap.cellsName + flags.linksNamePart
    flags.HCal = Flags()
    flags.HCal.Barrel = Flags()
    flags.HCal.Barrel.readoutName = 'HCalBarrelReadout'            # barrel, original segmentation (phi-theta)
    #flags.HCal.Barrel.readoutName = 'HCalBarrelReadoutPhiRow'    # barrel, alternative segmentation (phi-row)
    flags.HCal.Barrel.cellsName = flags.HCal.Barrel.readoutName + flags.cellsNamePart
    flags.HCal.Barrel.linksName = flags.HCal.Barrel.cellsName + flags.linksNamePart
    flags.HCal.Endcap = Flags()
    flags.HCal.Endcap.readoutName = 'HCalEndcapReadout'            # endcap, original segmentation
    flags.HCal.Endcap.cellsName = flags.HCal.Endcap.readoutName + flags.cellsNamePart
    flags.HCal.Endcap.linksName = flags.HCal.Endcap.cellsName + flags.linksNamePart
    return

    
