# run_digi_reco.py
# steering file for the ALLEGRO digitization/reconstruction

#
# COMMON IMPORTS
#

import os

# Logger
from Gaudi.Configuration import INFO, DEBUG, VERBOSE, ERROR
# units and physical constants
from GaudiKernel.PhysicalConstants import pi

#
# SETTINGS
#

# - default settings, that can be overridden via CLI
inputfile = "ALLEGRO_sim.root"             # input file produced with ddsim - can be overridden with IOSvc.Input
outputfile = "ALLEGRO_sim_digi_reco.root"  # output file produced by this steering file - can be overridden with IOSvc.Output
Nevts = -1                                 # -1 means all events in input file (can be overridden with -n or --num-events option of k4run

# - general settings not set via CLI
filterNoiseThreshold = -1                  # if addNoise is true, and filterNoiseThreshold is >0, will filter away cells with abs(energy) below filterNoiseThreshold * expected sigma(noise)
# dataFolder = "data/"                     # directory containing the calibration files
dataFolder = "./"                          # directory containing the calibration files

# - general settings set via CLI
from k4FWCore.parseArgs import parser
def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected.")

parser.add_argument("--includeHCal", type=str2bool, nargs="?", help="Also digitize HCal hits and create ECAL+HCAL clusters", const=True, default=False)
parser.add_argument("--includeMuon", type=str2bool, nargs="?", help="Also digitize muon hits", const=True, default=False)
parser.add_argument("--saveHits", type=str2bool, nargs="?", help="Save G4 hits", const=True, default=False)
parser.add_argument("--saveCells", type=str2bool, nargs="?", help="Save cell collection", const=True, default=False)
parser.add_argument("--addNoise", type=str2bool, nargs="?", help="Add noise to cells (ECAL barrel only)", const=True, default=False)
parser.add_argument("--addCrosstalk", type=str2bool, nargs="?", help="Add cross-talk to cells (ECAL barrel only)", const=True, default=False)
parser.add_argument("--addTracks", type=str2bool, nargs="?", help="Add reco-level tracks (smeared truth tracks)", const=True, default=False)
parser.add_argument("--doSWClustering", type=str2bool, nargs="?", help="Enable or disable sliding window clustering", const=True, default=True)
parser.add_argument("--createClusterCellCollections", type=str2bool, nargs="?", help="Create new cluster cell collections or just link clusters to cells in standard cell collections", const=True, default=True)
parser.add_argument("--doTopoClustering", type=str2bool, nargs="?", help="Enable or disable topo clustering", const=True, default=True)
parser.add_argument("--calibrateClusters", type=str2bool, nargs="?", help="Apply MVA calibration to clusters", const=True, default=False)
parser.add_argument("--reconstructPi0s", type=str2bool, nargs="?", help="Search for cluster pairs consistent with the pi0 hypothesis", const=True, default=True)
parser.add_argument("--runPhotonID", type=str2bool, nargs="?", help="Apply photon ID tool to clusters", const=True, default=False)
parser.add_argument("--runTrkHitDigitization", type=str2bool, nargs="?", help="Digitize tracker hits", const=True, default=False)
parser.add_argument("--useLegacyVTXDigitizer", type=str2bool, nargs="?", help="Perform VTXdigitizer-based digitization of tracker hits", const=True, default=False)

opts = parser.parse_known_args()[0]
runHCal = opts.includeHCal                          # if false, it will produce only ECAL clusters. if true, it will also produce ECAL+HCAL clusters
runMuon = opts.includeMuon                          # if false, it will not digitize muon hits
addNoise = opts.addNoise                            # add noise or not to the cell energy
addCrosstalk = opts.addCrosstalk                    # switch on/off the crosstalk
addTracks = opts.addTracks                          # add tracks or not
digitizeTrackerHits = opts.runTrkHitDigitization    # digitize tracker hits (DDPlanarDigi as default)
digitizeVTXdigitizer = opts.useLegacyVTXDigitizer   # digitize tracker hits (VTXdigitizer, smear truth)

# - what to save in output file
#
# always drop uncalibrated cells, except for tests and debugging
dropUncalibratedCells = True
# dropUncalibratedCells = False

# for big productions, save significant space removing hits and cells
# however, hits and cluster cells might be wanted for small productions for detailed event displays
# cluster cells are not needed for the training of the MVA energy regression nor the photon ID since needed quantities are stored in cluster shapeParameters
saveHits = opts.saveHits
saveCells = opts.saveCells
saveClusterCells = True

dropLumiCalHits = True

# for tracker hits there is a single hit/readout cell so not much gain by dropping them, especially if the corresponding digitized cells (smeared hits) have not been added to output
# dropVertexHits = True
# dropDCHHits = True
# dropSiWrHits = True
# dropMuonHits = True
dropVertexHits = False
dropDCHHits = False
dropSiWrHits = False
dropMuonHits = False

class Flags:
    pass
flags = Flags()
flags.IO = Flags()
flags.IO.inputFile = [inputfile]
flags.IO.outputFile = outputfile
flags.compactFile = 'ALLEGRO_o1_v03.xml'
flags.pathToDetector = os.environ.get('K4GEO','') + '/FCCee/ALLEGRO/compact/' + os.path.splitext(flags.compactFile)[0]
flags.dataFiles = dataFolder
flags.dataFilesUrl = 'https://fccsw.web.cern.ch/fccsw/filesForSimDigiReco/ALLEGRO/ALLEGRO_o1_v03/'
flags.cellsNamePart = 'Positioned'
flags.linksNamePart = 'SimCaloHitLinks'
flags.saveHits = saveHits   # should be elsewhere?
flags.saveCells = saveCells
from FCC_config.ALLEGRO.CreateCaloCells import defineCaloCellFlags
defineCaloCellFlags(flags)
flags.ECal.Barrel.addCrosstalk = addCrosstalk
from FCC_config.ALLEGRO.CreateCaloClusters import defineCaloClusterFlags
defineCaloClusterFlags(flags, opts)



resegmentECalBarrel = False

# - parameters for clustering (could also be made configurable via CLI)
doSWClustering = opts.doSWClustering
doTopoClustering = opts.doTopoClustering
outputSaveClusters = []  # list of clusters for which we want to create the truth links

#
# ALGORITHMS AND SERVICES SETUP
#
TopAlg = []  # alg sequence
ExtSvc = []  # list of external services
from FCC_config.ComponentAccumulator import ComponentAccumulator

# Event counter
from Configurables import EventCounter
eventCounter = EventCounter("EventCounter",
                            OutputLevel=INFO,
                            Frequency=10)
TopAlg += [eventCounter]
# add a message sink service if you want a summary table at the end (not needed..)
# ExtSvc += ["Gaudi::Monitoring::MessageSvcSink"]

# CPU information
from Configurables import AuditorSvc, ChronoAuditor
chra = ChronoAuditor()
audsvc = AuditorSvc()
audsvc.Auditors = [chra]
ExtSvc += [audsvc]


# Detector geometry
# prefix all xmls with path_to_detector
# if K4GEO is empty, this should use relative path to working directory
from Configurables import GeoSvc
geoservice = GeoSvc("GeoSvc",
                    OutputLevel=INFO
                    # OutputLevel=DEBUG  # set to DEBUG to print dd4hep::DEBUG messages in k4geo C++ drivers
                    )

path_to_detector = os.environ.get("K4GEO", "") + "/FCCee/ALLEGRO/compact/ALLEGRO_o1_v03/"
detectors_to_use = [
    'ALLEGRO_o1_v03.xml'
]
geoservice.detectors = [
    os.path.join(path_to_detector, _det) for _det in detectors_to_use
]
ExtSvc += [geoservice]

from FCC_config.ALLEGRO.DetIDs import detIDs

# Input/Output handling
from k4FWCore import IOSvc
from Configurables import EventDataSvc
io_svc = IOSvc("IOSvc")
io_svc.Input = inputfile
io_svc.Output = outputfile
io_svc.outputCommands = ['drop *',
                         'keep EventHeader',
                         'keep MCParticles']
ExtSvc += [io_svc]
ExtSvc += [EventDataSvc("EventDataSvc")]

if addTracks or digitizeTrackerHits or addNoise:
    ExtSvc += ["RndmGenSvc"]


# Tracking
# Create tracks from gen particles
if addTracks:
    from Configurables import TracksFromGenParticles
    tracksFromGenParticles = TracksFromGenParticles("CreateTracksFromGenParticles",
                                                    InputGenParticles=["MCParticles"],
                                                    InputSimTrackerHits=["VertexBarrelCollection",
                                                                         "VertexEndcapCollection",
                                                                         "DCHCollection",
                                                                         "SiWrBCollection",
                                                                         "SiWrDCollection"],
                                                    OutputTracks=["TracksFromGenParticles"],
                                                    OutputMCRecoTrackParticleAssociation=["TracksFromGenParticlesAssociation"],
                                                    ExtrapolateToECal=True,
                                                    KeepOnlyBestExtrapolation=False,
                                                    TrackerIDs=detIDs(flags,
                                                                      ["VXD_Barrel",
                                                                       "VXD_Disks",
                                                                       "DCH",
                                                                       "SiWr_Barrel",
                                                                       "SiWr_Disks"]),
                                                    OutputLevel=INFO)
    TopAlg += [tracksFromGenParticles]

    # Calculate dNdx from tracks
    from Configurables import TrackdNdxDelphesBased
    dNdxFromTracks = TrackdNdxDelphesBased("dNdxFromTracks",
                                           InputLinkCollection=tracksFromGenParticles.OutputMCRecoTrackParticleAssociation,
                                           OutputCollection=["DCHdNdxCollection"],
                                           ZmaxParameterName="DCH_gas_Lhalf",
                                           ZminParameterName="DCH_gas_Lhalf",
                                           RminParameterName="DCH_gas_inner_cyl_R",
                                           RmaxParameterName="DCH_gas_outer_cyl_R",
                                           FillFactor=1.0,
                                           OutputLevel=ERROR)
    TopAlg += [dNdxFromTracks]

io_svc.outputCommands += ['keep SiWrBDigis',
                          'keep SiWrBSimDigiLinks',
                          'keep SiWrDDigis',
                          'keep SiWrDSimDigiLinks',
                          'keep VTXBDigis',
                          'keep VTXBSimDigiLinks',
                          'keep VTXDDigis',
                          'keep VTXDSimDigiLinks',
                          'keep DCH_DigiCollection',
                          'keep DCH_DigiSimAssociationCollection',
                          'keep DCHdNdxCollection']
if not dropDCHHits:
    io_svc.outputCommands += ['keep DCHCollection']
if not dropSiWrHits:
    io_svc.outputCommands += ['keep SiWrBCollection',
                              'keep SiWrDCollection']
if not dropMuonHits:
    io_svc.outputCommands += ['keep VertexBarrelCollection',
                              'keep VertexEndcapCollection']


# Tracker digitization
if digitizeTrackerHits:
    from Configurables import VTXdigitizer
    import math
    # different sensors for inner/outer barrel layers
    # see https://indico.cern.ch/event/1244371/contributions/5350233
    innerVertexResolution_x = 0.003  # [mm], assume 3 µm resolution for ARCADIA sensor
    innerVertexResolution_y = 0.003  # [mm], assume 3 µm resolution for ARCADIA sensor
    innerVertexResolution_t = 1000  # [ns]
    outerVertexResolution_x = 0.050 / math.sqrt(12)  # [mm], assume ATLASPix3 sensor with 50 µm pitch
    outerVertexResolution_y = 0.150 / math.sqrt(12)  # [mm], assume ATLASPix3 sensor with 150 µm pitch
    outerVertexResolution_t = 1000  # [ns]

    if digitizeVTXdigitizer:
        vtxb_digitizer = VTXdigitizer("VTXBdigitizer",
                                      inputSimHits="VertexBarrelCollection",
                                      outputDigiHits="VTXBDigis",
                                      outputSimDigiAssociation="VTXBSimDigiLinks",
                                      detectorName="Vertex",
                                      readoutName="VertexBarrelCollection",
                                      xResolution=[innerVertexResolution_x, innerVertexResolution_x, innerVertexResolution_x,
                                                   outerVertexResolution_x, outerVertexResolution_x],  # mm, r-phi direction
                                      yResolution=[innerVertexResolution_y, innerVertexResolution_y, innerVertexResolution_y,
                                                   outerVertexResolution_y, outerVertexResolution_y],  # mm, z direction
                                      tResolution=[innerVertexResolution_t, innerVertexResolution_t, innerVertexResolution_t,
                                                   outerVertexResolution_t, outerVertexResolution_t],  # ns
                                      forceHitsOntoSurface=False,
                                      OutputLevel=INFO
                                      )
        TopAlg += [vtxb_digitizer]

        vtxd_digitizer = VTXdigitizer("VTXDdigitizer",
                                      inputSimHits="VertexEndcapCollection",
                                      outputDigiHits="VTXDDigis",
                                      outputSimDigiAssociation="VTXDSimDigiLinks",
                                      detectorName="Vertex",
                                      readoutName="VertexEndcapCollection",
                                      xResolution=[outerVertexResolution_x, outerVertexResolution_x, outerVertexResolution_x],  # mm, r direction
                                      yResolution=[outerVertexResolution_y, outerVertexResolution_y, outerVertexResolution_y],  # mm, phi direction
                                      tResolution=[outerVertexResolution_t, outerVertexResolution_t, outerVertexResolution_t],  # ns
                                      forceHitsOntoSurface=False,
                                      OutputLevel=INFO
                                      )
        TopAlg += [vtxd_digitizer]

    else:
        # digitize vertex hits through "native" DDPlanarDigi
        from Configurables import DDPlanarDigi
        vxd_barrel_digitizer_args = {
            "IsStrip": False,
            "ResolutionU": [innerVertexResolution_x,innerVertexResolution_x,innerVertexResolution_x, outerVertexResolution_x, outerVertexResolution_x],
            "ResolutionV": [innerVertexResolution_y,innerVertexResolution_y,innerVertexResolution_y, outerVertexResolution_y, outerVertexResolution_y],
            "SimTrackHitCollectionName": ["VertexBarrelCollection"],
            "SimTrkHitRelCollection": ["VTXBSimDigiLinks"],
            "SubDetectorName": "VertexBarrel",
            "TrackerHitCollectionName": ["VTXBDigis"],
        }

        vxd_endcap_digitizer_args = {
            "IsStrip": False,
            "ResolutionU": [outerVertexResolution_x, outerVertexResolution_x, outerVertexResolution_x],
            "ResolutionV": [outerVertexResolution_y, outerVertexResolution_y, outerVertexResolution_y],
            "SimTrackHitCollectionName": ["VertexEndcapCollection"],
            "SimTrkHitRelCollection": ["VTXDSimDigiLinks"],
            "SubDetectorName": "VertexDisks",
            "TrackerHitCollectionName": ["VTXDDigis"],
        }


        VXDBarrelDigitizer = DDPlanarDigi(
            "VXDBarrelDigitizer",
            **vxd_barrel_digitizer_args,
            OutputLevel=INFO
        )

        VXDEndcapDigitizer = DDPlanarDigi(
            "VXDEndcapDigitizer",
            **vxd_endcap_digitizer_args,
            OutputLevel=INFO
        )

        TopAlg += [ VXDBarrelDigitizer ]
        TopAlg += [ VXDEndcapDigitizer ]

    # digitize silicon wrapper hits
    siWrapperResolution_x = 0.050 / math.sqrt(12)  # [mm]
    siWrapperResolution_y = 1.0 / math.sqrt(12)  # [mm]
    siWrapperResolution_t = 0.040  # [ns], assume 40 ps timing resolution for a single layer -> Should lead to <30 ps resolution when >1 hit

    siwrb_digitizer = VTXdigitizer("SiWrBdigitizer",
                                   inputSimHits="SiWrBCollection",
                                   outputDigiHits="SiWrBDigis",
                                   outputSimDigiAssociation="SiWrBSimDigiLinks",
                                   detectorName="SiWrB",
                                   readoutName="SiWrBCollection",
                                   xResolution=[siWrapperResolution_x, siWrapperResolution_x],  # mm, r-phi direction
                                   yResolution=[siWrapperResolution_y, siWrapperResolution_y],  # mm, z direction
                                   tResolution=[siWrapperResolution_t, siWrapperResolution_t],  # ns
                                   forceHitsOntoSurface=False,
                                   OutputLevel=INFO
                                   )
    TopAlg += [siwrb_digitizer]

    siwrd_digitizer = VTXdigitizer("SiWrDdigitizer",
                                   inputSimHits="SiWrDCollection",
                                   outputDigiHits="SiWrDDigis",
                                   outputSimDigiAssociation="SiWrDSimDigiLinks",
                                   detectorName="SiWrD",
                                   readoutName="SiWrDCollection",
                                   xResolution=[siWrapperResolution_x, siWrapperResolution_x],  # mm, r-phi direction
                                   yResolution=[siWrapperResolution_y, siWrapperResolution_y],  # mm, z direction
                                   tResolution=[siWrapperResolution_t, siWrapperResolution_t],  # ns
                                   forceHitsOntoSurface=False,
                                   OutputLevel=INFO
                                   )
    TopAlg += [siwrd_digitizer]

    from Configurables import UniqueIDGenSvc
    ExtSvc += [UniqueIDGenSvc("uidSvc")]
    from Configurables import DCHdigi_v01
    # "https://fccsw.web.cern.ch/fccsw/filesForSimDigiReco/IDEA/DataAlgFORGEANT.root"
    dch_digitizer = DCHdigi_v01("DCHdigi",
                                DCH_simhits=["DCHCollection"],
                                DCH_name="DCH_v2",
                                fileDataAlg=dataFolder + "DataAlgFORGEANT.root",
                                calculate_dndx=False,  # cluster counting disabled (to be validated, see FCC-config#239)
                                create_debug_histograms=False,
                                # zResolution_mm=30.,  # in mm - Note: At this point, the z resolution comes without the stereo measurement
                                # xyResolution_mm=0.1  # in mm
                                # no smearing
                                zResolution_mm=0.,  # in mm - Note: At this point, the z resolution comes without the stereo measurement
                                xyResolution_mm=0.  # in mm
                                )
    TopAlg += [dch_digitizer]
io_svc.outputCommands += ['keep TracksFromGenParticles',
                          'keep TracksFromGenParticlesAssociation',]


#############################################################################
# Calorimeter digitization (merging hits into cells, EM scale calibration via sampling fractions)

caldigi_cfg = ComponentAccumulator()

# - ECAL readouts
ecalBarrelReadoutName2 = "ECalBarrelModuleThetaMerged2"    # barrel, after re-segmentation (for optimisation studies)
ecalBarrelHitsMergedName = 'ECalBarrelCellsMerged'
ecalBarrelPositionedCellsName2 = ecalBarrelReadoutName2 + "Positioned"

# Create cells in ECal barrel (calibrated and positioned - optionally with xtalk and noise added)
# from uncalibrated cells (+cellID info) from ddsim
from Configurables import CreatePositionedCaloCells
from FCC_config.ALLEGRO.CreateCaloCells import CreateECalBarrelCellsCfg
caldigi_cfg.merge(CreateECalBarrelCellsCfg(flags))

# -  now, if we want to also save cells with coarser granularity:
if resegmentECalBarrel:
    # rewrite the cellId using the merged theta-module segmentation
    # (merging several modules and severla theta readout cells).
    # Add noise at this step if you derived the noise already assuming merged cells
    # Step a: compute new cellID of cells based on new readout
    # (merged module-theta segmentation with variable merging vs layer)
    #from Configurables import RedoSegmentation
    from FCC_config.ALLEGRO.CreateCaloCells import redoECalSegmentationCfg
    caldigi_cfg.merge (
        redoECalSegmentationCfg(flags,
                                newReadoutName = ecalBarrelReadoutName2,
                                newCellsName = ecalBarrelHitsMergedName))


    # Step b: merge new cells with same cellID together
    # do not apply cell calibration again since cells were already
    # calibrated in Step 1
    # noise and xtalk off assuming they were applied earlier
    caldigi_cfg.merge (
        CreateECalBarrelCellsCfg(flags,
                                 'CreatePositionedECalBarrelCells2',
                                 hits = ecalBarrelHitsMergedName,
                                 readoutName=ecalBarrelReadoutName2,
                                 addCrosstalk = False,
                                 doCellCalibration = False))

# Create cells in ECal endcap (needed if one wants to apply cell calibration,
# which is not performed by ddsim)
from FCC_config.ALLEGRO.CreateCaloCells import CreateECalEndcapCellsCfg
caldigi_cfg.merge(CreateECalEndcapCellsCfg(flags))

if addNoise:
    # cells with noise not filtered
    caldigi_cfg.merge(
        CreateECalBarrelCellsCfg (flags,
                                  'CreatePositionedECalBarrelCellsWithNoise',
                                  addNoise = True,
                                  cellsNameSuffix = 'WithNoise'))

    # cells with noise filtered
    caldigi_cfg.merge(
        CreateECalBarrelCellsCfg (flags,
                                  'CreatePositionedECalBarrelCellsWithNoiseFiltered',
                                  addNoise = True,
                                  filterCellNoise = True,
                                  cellsNameSuffix = 'WithNoiseFiltered'))


if runHCal:
    from FCC_config.ALLEGRO.CreateCaloCells import \
         CreateHCalBarrelCellsCfg, CreateHCalEndcapCellsCfg
    caldigi_cfg.merge(CreateHCalBarrelCellsCfg(flags))
    caldigi_cfg.merge(CreateHCalEndcapCellsCfg(flags))

caldigi_cfg.toVars (TopAlg, ExtSvc)


#############################################################################
# Muon cells [add longitudinal segmentation to detector?]
# We use the calo digitizer since Pandora and MLPF expect muon hits to be caloHits
if runMuon:
    from Configurables import CellPositionsSimpleCylinderPhiThetaSegTool
    muonBarrelReadoutName = "MuonTaggerBarrelPhiTheta"
    muonBarrelPositionedCellsName = muonBarrelReadoutName + "Positioned"
    muonBarrelLinks = muonBarrelPositionedCellsName + "SimCaloHitLinks"
    cellPositionMuonBarrelTool = CellPositionsSimpleCylinderPhiThetaSegTool(
        "CellPositionsMuonBarrel",
        detectorName="MuonTaggerBarrel",
        readoutName=muonBarrelReadoutName,
        OutputLevel=INFO
    )

    from Configurables import NoiseCaloCellsFlatTool
    MuonBarrelNoiseTool = NoiseCaloCellsFlatTool("MuonBarrelNoiseTool",
                                                 cellNoiseRMS=0.0005,  # in GeV
                                                 filterNoiseThreshold=3,
                                                 OutputLevel=INFO)
    createMuonBarrelCells = CreatePositionedCaloCells("CreatePositionedMuonBarrelCells",
                                                      positionsTool=cellPositionMuonBarrelTool,
                                                      doCellCalibration=False,
                                                      # calibTool=None,
                                                      addCrosstalk=False,
                                                      # crosstalkTool=None
                                                      addCellNoise=False,
                                                      # filterCellNoise=False,
                                                      # noiseTool=None,
                                                      filterCellNoise=True,
                                                      noiseTool=MuonBarrelNoiseTool,
                                                      geometryTool=None,
                                                      OutputLevel=INFO,
                                                      hits=muonBarrelReadoutName,
                                                      cells=muonBarrelPositionedCellsName,
                                                      links=muonBarrelLinks
                                                      )
    TopAlg += [createMuonBarrelCells]

    muonEndcapReadoutName = "MuonTaggerEndcapPhiTheta"
    muonEndcapPositionedCellsName = muonEndcapReadoutName + "Positioned"
    muonEndcapLinks = muonEndcapPositionedCellsName + "SimCaloHitLinks"
    cellPositionMuonEndcapTool = CellPositionsSimpleCylinderPhiThetaSegTool(
        "CellPositionsMuonEndcap",
        detectorName="MuonTaggerEndcap",
        readoutName=muonEndcapReadoutName,
        OutputLevel=INFO
    )
    createMuonEndcapCells = CreatePositionedCaloCells("CreatePositionedMuonEndcapCells",
                                                      positionsTool=cellPositionMuonEndcapTool,
                                                      doCellCalibration=False,
                                                      # calibTool=None,
                                                      addCrosstalk=False,
                                                      # crosstalkTool=None
                                                      addCellNoise=False,
                                                      filterCellNoise=False,
                                                      noiseTool=None,
                                                      geometryTool=None,
                                                      OutputLevel=INFO,
                                                      hits=muonEndcapReadoutName,
                                                      cells=muonEndcapPositionedCellsName,
                                                      links=muonEndcapLinks
                                                      )
    TopAlg += [createMuonEndcapCells]

    if not dropMuonHits:
        io_svc.outputCommands += [f'keep {muonBarrelPositionedCellsName}',
                                  f'keep {muonEndcapPositionedCellsName}',
                                  f'keep {muonBarrelReadoutName}',
                                  f'keep {muonBarrelReadoutName}Contributions',
                                  f'keep {muonEndcapReadoutName}']
else:
    if not dropMuonHits:
        io_svc.outputCommands += ['keep MuonTaggerBarrelPhiTheta',
                                  'keep MuonTaggerBarrelPhiThetaContributions',
                                  'keep MuonTaggerEndcapPhiTheta']

    muonBarrelReadoutName = ""
    muonEndcapReadoutName = ""
    muonBarrelPositionedCellsName = ""
    muonEndcapPositionedCellsName = ""
    muonBarrelLinks = ""
    muonEndcapLinks = ""

if saveHits and saveCells:
    io_svc.outputCommands += ['keep MuonTaggerBarrelPhiThetaPositionedSimCaloHitLinks',
                              'keep MuonTaggerEndcapPhiThetaPositionedSimCaloHitLinks']


from FCC_config.ALLEGRO.CreateCaloClusters import CaloSWClusterCfg
calclust_cfg = ComponentAccumulator()
if doSWClustering:
    # SW ECAL barrel clusters
    calclust_cfg.merge (
        CaloSWClusterCfg (flags,
                          {"ECAL_Barrel": flags.ECal.Barrel.cellsName},
                          'EMBCaloClusters',
                          0.04,  # threshold,
                          'StandardSize',
                          outputSaveClusters))

    # SW ECAL endcap clusters
    calclust_cfg.merge (
        CaloSWClusterCfg (flags,
                          {"ECAL_Endcap": flags.ECal.Endcap.cellsName},
                          'EMECCaloClusters',
                          0.04,  # threshold,
                          'StandardSize',
                          outputSaveClusters))

    # SW ECAL barrel clusters with noise
    if addNoise:
        suffix = 'WithNoise'
        if filterNoiseThreshold >= 0:
            suffix += 'Filtered'
        calclust_cfg.merge (
            CaloSWClusterCfg (flags,
                              {'ECAL_Barrel': flags.ECal.Barrel.cellsName + suffix},
                              'EMBCaloClusters' + suffix,
                              # threshold --- large number of clusters
                              # with noise, consider raising to 0.3 if not
                              # looking at low-energy cluster
                              # reconstruction, or use filtered cells
                              0.1,
                              'StandardSize',
                              outputSaveClusters))

    # ECAL + HCAL clusters
    if runHCal:
        calclust_cfg.merge (
            CaloSWClusterCfg (flags,
                              {'ECAL_Barrel': flags.ECal.Barrel.cellsName,
                               'ECAL_Endcap': flags.ECal.Endcap.cellsName,
                               'HCAL_Barrel': flags.HCal.Barrel.cellsName,
                               'HCAL_Endcap': flags.HCal.Endcap.cellsName,
                               },
                              'CaloClusters',
                              0.04,  # threshold,
                              'StandardSize',
                              outputSaveClusters,
                              applyMVAClusterEnergyCalibration = False,
                              addShapeParameters = False,
                              doPhotonID = False))

    # experimental: MUON clusters
    if runMuon:
        calclust_cfg.merge (
            CaloSWClusterCfg (flags,
                              {'Muon_Barrel': muonBarrelPositionedCellsName,
                               'Muon_Endcap': muonEndcapPositionedCellsName,
                               },
                              'MuonCaloClusters',
                              0.00,  # threshold,
                              'MuonSize',
                              outputSaveClusters,
                              applyMVAClusterEnergyCalibration = False,
                              addShapeParameters = False,
                              doPhotonID = False))


from FCC_config.ALLEGRO.CreateCaloClusters import CaloTopoClusterCfg
if doTopoClustering:
    # ECAL barrel topoclusters
    calclust_cfg.merge (
        CaloTopoClusterCfg (flags,
                            {'ECAL_Barrel': flags.ECal.Barrel.cellsName},
                            'EMBCaloTopoClusters',
                            0,  # threshold,
                            outputSaveClusters))

    # ECAL endcap topoclusters
    calclust_cfg.merge (
        CaloTopoClusterCfg (flags,
                            {'ECAL_Endcap': flags.ECal.Endcap.cellsName},
                            'EMECCaloTopoClusters',
                            0,  # threshold,
                            outputSaveClusters))

    # ECAL topoclusters with noise
    if addNoise:
        suffix = 'WithNoise'
        if filterNoiseThreshold >= 0:
            suffix += 'Filtered'
        calclust_cfg.merge (
            CaloTopoClusterCfg (flags,
                                {'ECAL_Barrel': flags.ECal.Barrel.cellsName + suffix},
                                'EMBCaloTopoClusters' + suffix,
                                0.1,  # threshold,
                                outputSaveClusters))

    # ECAL + HCAL
    if runHCal:
        calclust_cfg.merge (
            CaloTopoClusterCfg (flags,
                                {'ECAL_Barrel': flags.ECal.Barrel.cellsName,
                                 'ECAL_Endcap': flags.ECal.Endcap.cellsName,
                                 'HCAL_Barrel': flags.HCal.Barrel.cellsName,
                                 'HCAL_Endcap': flags.HCal.Endcap.cellsName,
                                 },
                                'CaloTopoClusters',
                                0, # threshold
                                outputSaveClusters,
                                applyMVAClusterEnergyCalibration = False,
                                addShapeParameters = False,
                                doPhotonID = False))
calclust_cfg.toVars (TopAlg, ExtSvc)


########################################################################


# Create CaloHit<->MCParticle links (needed for training datasets for MLPF)
# Also store Cluster<->MCParticle links (for truth matching for efficiency and purity studies)
from Configurables import CreateTruthLinks
caloLinks = [flags.ECal.Barrel.linksName, flags.ECal.Endcap.linksName]
if runHCal:
    caloLinks += [flags.HCal.Barrel.linksName, flags.HCal.Endcap.linksName]
if runMuon:
    caloLinks += [muonBarrelLinks, muonEndcapLinks]
createTruthLinks = CreateTruthLinks("CreateTruthLinks",
                                    cell_hit_links=caloLinks,
                                    mcparticles="MCParticles",
                                    clusters=outputSaveClusters,
                                    cell_mcparticle_links="CaloHitMCParticleLinks",
                                    cluster_mcparticle_links="ClusterMCParticleLinks",
                                    OutputLevel=INFO)
TopAlg += [createTruthLinks]
io_svc.outputCommands += ['keep CaloHitMCParticleLinks',
                          'keep ClusterMCParticleLinks']



# configure the application
print(TopAlg)
print(ExtSvc)
from k4FWCore import ApplicationMgr
applicationMgr = ApplicationMgr(
    TopAlg=TopAlg,
    EvtSel='NONE',
    EvtMax=Nevts,
    ExtSvc=ExtSvc,
    StopOnSignal=True,
)

for algo in applicationMgr.TopAlg:
    algo.AuditExecute = True
    # for debug
    # algo.OutputLevel = DEBUG
