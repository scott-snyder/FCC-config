# run_digi_reco.py
# steering file for the ALLEGRO digitization/reconstruction

#
# COMMON IMPORTS
#

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
dataFolderDef = "./"                       # directory containing the calibration files

# - general settings not set via CLI
filterNoiseThreshold = -1                  # if addNoise is true, and filterNoiseThreshold is >0, will filter away cells with abs(energy) below filterNoiseThreshold * expected sigma(noise)

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

parser.add_argument("--dataFolder", type=str, help="Path to calibration data folder", default=dataFolderDef)
parser.add_argument("--includeHCal", type=str2bool, nargs="?", help="Also digitize HCal hits and create ECAL+HCAL clusters", const=True, default=False)
parser.add_argument("--includeMuon", type=str2bool, nargs="?", help="Also digitize muon hits", const=True, default=False)
parser.add_argument("--saveHits", type=str2bool, nargs="?", help="Save G4 hits", const=True, default=False)
parser.add_argument("--saveCells", type=str2bool, nargs="?", help="Save cell collections", const=True, default=False)
parser.add_argument("--keepUncalibratedCells", type=str2bool, nargs="?", help="Save uncalibrated cell collections", const=True, default=False)
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
parser.add_argument("--runTrkFinder", type=str2bool, nargs="?", help="Run Geometric Graph Track Finding (GGTF) on digitized tracker hits", const=True, default=False)
parser.add_argument("--runTrkFitter", type=str2bool, nargs="?", help="Run track fitter on tracks", const=True, default=False)
parser.add_argument("--resegmentECalBarrel", type=str2bool, nargs="?", help="Resegment ECal barrel", const=True, default=False)

opts = parser.parse_known_args()[0]
dataFolder = opts.dataFolder                        # directory containing the calibration files
runHCal = opts.includeHCal                          # if false, it will produce only ECAL clusters. if true, it will also produce ECAL+HCAL clusters
runMuon = opts.includeMuon                          # if false, it will not digitize muon hits
addNoise = opts.addNoise                            # add noise or not to the cell energy
addCrosstalk = opts.addCrosstalk                    # switch on/off the crosstalk
addTracks = opts.addTracks                          # add tracks or not
runTrkHitDigitization = opts.runTrkHitDigitization  # digitize tracker hits (DDPlanarDigi as default)
useLegacyVTXDigitizer = opts.useLegacyVTXDigitizer  # digitize tracker hits (VTXdigitizer, smear truth)
runTrkFinder = opts.runTrkFinder                    # run GGTF on digitized tracker hits
runTrkFitter = opts.runTrkFitter                    # run track fitter on tracks

# - what to save in output file
#
# by default drop uncalibrated cells, but can keep for tests and debugging
dropUncalibratedCells = not opts.keepUncalibratedCells

# for big productions, save significant space removing hits and cells
# however, hits and cluster cells might be wanted for small productions for detailed event displays
# cluster cells are not needed for the training of the MVA energy regression nor the photon ID since needed quantities are stored in cluster shapeParameters
saveHits = opts.saveHits
saveCells = opts.saveCells

dropLumiCalHits = True

# for tracker hits there is a single hit/readout cell so not much gain by dropping them, especially if the corresponding digitized cells (smeared hits) have not been added to output
# dropVertexHits = True
# dropSTTHits = True
# dropSiWrHits = True
# dropMuonHits = True
dropVertexHits = False
dropSTTHits = False
dropSiWrHits = False
dropMuonHits = False


resegmentECalBarrel = opts.resegmentECalBarrel

ecalEndcapWheels = 3
hcalBarrelLayers = 13
hcalEndcapLayers = 22

# - parameters for clustering (could also be made configurable via CLI)
doSWClustering = opts.doSWClustering
doTopoClustering = opts.doTopoClustering
doCreateClusterCellCollection = opts.createClusterCellCollections  # create new collection with clustered cells or just link from cluster to original input cell collections
                                                                   # this applies to both SW and Topo cluster cell collections
outputSaveClusters = []  # list of clusters for which we want to create the truth links

# cluster energy corrections
# simple parametrisations of up/downstream losses for ECAL-only clusters
# not to be applied for ECAL+HCAL clustering
# superseded by MVA calibration, but can be turned on here for the purpose of testing that the code is not broken - will end up in separate cluster collection
applyUpDownstreamCorrections = False


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
import os
geoservice = GeoSvc("GeoSvc",
                    OutputLevel=INFO
                    # OutputLevel=DEBUG  # set to DEBUG to print dd4hep::DEBUG messages in k4geo C++ drivers
                    )

path_to_detector = os.environ.get("K4GEO", "") + "/FCCee/ALLEGRO/compact/ALLEGRO_o2_v01/"
detectors_to_use = [
    'ALLEGRO_o2_v01.xml'
]
geoservice.detectors = [
    os.path.join(path_to_detector, _det) for _det in detectors_to_use
]
ExtSvc += [geoservice]

from FCC_config.DetIDs import detIDs


# Configuration flags.
class Flags:
    pass
flags = Flags()
flags.compactFile = geoservice.detectors[0]
flags.dataFiles = dataFolder
flags.IO = Flags()
flags.IO.inputFile = [inputfile]
flags.IO.outputFile = outputfile
flags.saveHits = saveHits   # should be elsewhere?
flags.saveCells = saveCells

from FCC_config.ALLEGRO.CreateCaloCellsConfig import defineCaloCellFlags
defineCaloCellFlags(flags)
flags.ECal.Barrel.addCrosstalk = addCrosstalk

from FCC_config.ALLEGRO.CreateCaloClustersConfig import defineCaloClusterFlags
defineCaloClusterFlags(flags,
                       calibrateClusters = opts.calibrateClusters,
                       createClusterCellCollections = opts.createClusterCellCollections,
                       reconstructPi0s = opts.reconstructPi0s,
                       runPhotonID = opts.runPhotonID)


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

if addTracks or runTrkHitDigitization or addNoise:
    ExtSvc += ["RndmGenSvc"]


# Tracking
# Create tracks from gen particles
if addTracks:
    from Configurables import TracksFromGenParticles
    tracksFromGenParticles = TracksFromGenParticles("CreateTracksFromGenParticles",
                                                    InputGenParticles=["MCParticles"],
                                                    InputSimTrackerHits=["VertexBarrelCollection",
                                                                         "VertexEndcapCollection",
                                                                         "STTCollection",
                                                                         "SiWrBCollection",
                                                                         "SiWrDCollection"],
                                                    OutputTracks=["TracksFromGenParticles"],
                                                    OutputMCRecoTrackParticleAssociation=["TracksFromGenParticlesAssociation"],
                                                    ExtrapolateToECal=True,
                                                    KeepOnlyBestExtrapolation=False,
                                                    TrackerIDs=detIDs(flags,
                                                                      ["VXD_Barrel",
                                                                       "VXD_Disks",
                                                                       "STT",
                                                                       "SiWr_Barrel",
                                                                       "SiWr_Disks"]),
                                                    OutputLevel=INFO)
    TopAlg += [tracksFromGenParticles]

    # Calculate dNdx from tracks
    from Configurables import TrackdNdxDelphesBased
    dNdxFromTracks = TrackdNdxDelphesBased("dNdxFromTracks",
                                           InputLinkCollection=tracksFromGenParticles.OutputMCRecoTrackParticleAssociation,
                                           OutputCollection=["STTdNdxCollection"],
                                           ZmaxParameterName="STT_half_length_total",
                                           ZminParameterName="STT_half_length_total",
                                           RminParameterName="STT_inner_cyl_R_total",
                                           RmaxParameterName="STT_outer_cyl_R_total",
                                           FillFactor=1.0,   #FIXME: get number for STT
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
if not dropSTTHits:
    io_svc.outputCommands.append("keep STTCollection*")
if not dropSiWrHits:
    io_svc.outputCommands += ['keep SiWrBCollection',
                              'keep SiWrDCollection']
if not dropMuonHits:
    io_svc.outputCommands += ['keep VertexBarrelCollection',
                              'keep VertexEndcapCollection']


# Tracker digitization
if runTrkHitDigitization:
    import math
    # different sensors for inner/outer barrel layers
    # see https://indico.cern.ch/event/1244371/contributions/5350233
    innerVertexResolution_x = 0.003  # [mm], assume 3 µm resolution for ARCADIA sensor
    innerVertexResolution_y = 0.003  # [mm], assume 3 µm resolution for ARCADIA sensor
    innerVertexResolution_t = 1000  # [ns]
    outerVertexResolution_x = 0.050 / math.sqrt(12)  # [mm], assume ATLASPix3 sensor with 50 µm pitch
    outerVertexResolution_y = 0.150 / math.sqrt(12)  # [mm], assume ATLASPix3 sensor with 150 µm pitch
    outerVertexResolution_t = 1000  # [ns]

    # silicon wrapper hits parameters
    siWrapperResolution_x = 0.050 / math.sqrt(12)  # [mm]
    siWrapperResolution_y = 1.0 / math.sqrt(12)  # [mm]
    siWrapperResolution_t = 0.040  # [ns], assume 40 ps timing resolution for a single layer -> Should lead to <30 ps resolution when >1 hit

    # Define arguments for digitizers
    vxd_barrel_digi_args = {
        "IsStrip": False,
        "ResolutionU": [innerVertexResolution_x]*3 + [outerVertexResolution_x]*2,
        "ResolutionV": [innerVertexResolution_y]*3 + [outerVertexResolution_y]*2,
        "ResolutionT": [innerVertexResolution_t]*3 + [outerVertexResolution_t]*2,
        "SimTrackHitCollectionName": ["VertexBarrelCollection"],
        "SimTrkHitRelCollection": ["VTXBSimDigiLinks"],
        "SubDetectorName": "VertexBarrel",
        "TrackerHitCollectionName": ["VTXBDigis"],
        "ForceHitsOntoSurface": True,
        "CellIDBits": 32,
    }

    vxd_endcap_digi_args = {
        "IsStrip": False,
        "ResolutionU": [outerVertexResolution_x]*3,
        "ResolutionV": [outerVertexResolution_y]*3,
        "ResolutionT": [outerVertexResolution_t]*3,
        "SimTrackHitCollectionName": ["VertexEndcapCollection"],
        "SimTrkHitRelCollection": ["VTXDSimDigiLinks"],
        "SubDetectorName": "VertexDisks",
        "TrackerHitCollectionName": ["VTXDDigis"],
        "ForceHitsOntoSurface": True,
        "CellIDBits": 32,
    }

    siWr_barrel_digi_args = {
        "IsStrip": False,
        "ResolutionU": [siWrapperResolution_x]*4,
        "ResolutionV": [siWrapperResolution_y]*4,
        "ResolutionT": [siWrapperResolution_t]*4,
        "SimTrackHitCollectionName": ["SiWrBCollection"],
        "SimTrkHitRelCollection": ["SiWrBSimDigiLinks"],
        "SubDetectorName": "SiWrB",
        "TrackerHitCollectionName": ["SiWrBDigis"],
        "ForceHitsOntoSurface": True,
        "CellIDBits": 32,
    }

    siWr_endcap_digi_args = {
        "IsStrip": False,
        "ResolutionU": [siWrapperResolution_x]*4,
        "ResolutionV": [siWrapperResolution_y]*4,
        "ResolutionT": [siWrapperResolution_t]*4,
        "SimTrackHitCollectionName": ["SiWrDCollection"],
        "SimTrkHitRelCollection": ["SiWrDSimDigiLinks"],
        "SubDetectorName": "SiWrD",
        "TrackerHitCollectionName": ["SiWrDDigis"],
        "ForceHitsOntoSurface": True,
        "CellIDBits": 32,
    }


    if useLegacyVTXDigitizer:
        # digitize silicon hits through VTXdigitizer (smearing truth hits)
        from Configurables import VTXdigitizer
        vtxb_digitizer = VTXdigitizer("VTXBdigitizer",
                                      inputSimHits=vxd_barrel_digi_args["SimTrackHitCollectionName"][0],
                                      outputDigiHits=vxd_barrel_digi_args["TrackerHitCollectionName"][0],
                                      outputSimDigiAssociation= vxd_barrel_digi_args["SimTrkHitRelCollection"][0],
                                      detectorName=vxd_barrel_digi_args["SubDetectorName"],
                                      readoutName=vxd_barrel_digi_args["SimTrackHitCollectionName"][0],
                                      xResolution=vxd_barrel_digi_args["ResolutionU"],  # mm, r-phi direction
                                      yResolution=vxd_barrel_digi_args["ResolutionV"],  # mm, z direction
                                      tResolution=vxd_barrel_digi_args["ResolutionT"],  # ns
                                      forceHitsOntoSurface=False,
                                      OutputLevel=INFO
                                      )
        TopAlg += [vtxb_digitizer]

        vtxd_digitizer = VTXdigitizer("VTXDdigitizer",
                                      inputSimHits=vxd_endcap_digi_args["SimTrackHitCollectionName"][0],
                                      outputDigiHits=vxd_endcap_digi_args["TrackerHitCollectionName"][0],
                                      outputSimDigiAssociation= vxd_endcap_digi_args["SimTrkHitRelCollection"][0],
                                      detectorName=vxd_endcap_digi_args["SubDetectorName"],
                                      readoutName=vxd_endcap_digi_args["SimTrackHitCollectionName"][0],
                                      xResolution=vxd_endcap_digi_args["ResolutionU"],  # mm, r direction
                                      yResolution=vxd_endcap_digi_args["ResolutionV"],  # mm, phi direction
                                      tResolution=vxd_endcap_digi_args["ResolutionT"],  # ns
                                      forceHitsOntoSurface=False,
                                      OutputLevel=INFO
                                      )
        TopAlg += [vtxd_digitizer]

        siwrb_digitizer = VTXdigitizer("SiWrBdigitizer",
                                      inputSimHits=siWr_barrel_digi_args["SimTrackHitCollectionName"][0],
                                      outputDigiHits=siWr_barrel_digi_args["TrackerHitCollectionName"][0],
                                      outputSimDigiAssociation= siWr_barrel_digi_args["SimTrkHitRelCollection"][0],
                                      detectorName=siWr_barrel_digi_args["SubDetectorName"],
                                      readoutName=siWr_barrel_digi_args["SimTrackHitCollectionName"][0],
                                      xResolution=siWr_barrel_digi_args["ResolutionU"],  # mm, r-phi direction
                                      yResolution=siWr_barrel_digi_args["ResolutionV"],  # mm, z direction
                                      tResolution=siWr_barrel_digi_args["ResolutionT"],  # ns
                                      forceHitsOntoSurface=False,
                                      OutputLevel=INFO
                                      )
        TopAlg += [siwrb_digitizer]

        siwrd_digitizer = VTXdigitizer("SiWrDdigitizer",
                                       inputSimHits=siWr_endcap_digi_args["SimTrackHitCollectionName"][0],
                                       outputDigiHits=siWr_endcap_digi_args["TrackerHitCollectionName"][0],
                                       outputSimDigiAssociation= siWr_endcap_digi_args["SimTrkHitRelCollection"][0],
                                       detectorName=siWr_endcap_digi_args["SubDetectorName"],
                                       readoutName=siWr_endcap_digi_args["SimTrackHitCollectionName"][0],
                                       xResolution=siWr_endcap_digi_args["ResolutionU"],  # mm, r direction
                                       yResolution=siWr_endcap_digi_args["ResolutionV"],  # mm, phi direction
                                       tResolution=siWr_endcap_digi_args["ResolutionT"],  # ns
                                       forceHitsOntoSurface=False,
                                       OutputLevel=INFO
                                       )
        TopAlg += [siwrd_digitizer]

    else:
        # digitize vertex hits through "native" DDPlanarDigi
        from Configurables import DDPlanarDigi

        VXDBarrelDigitizer = DDPlanarDigi(
            "VXDBarrelDigitizer",
            **vxd_barrel_digi_args,
            OutputLevel=INFO
        )

        VXDEndcapDigitizer = DDPlanarDigi(
            "VXDEndcapDigitizer",
            **vxd_endcap_digi_args,
            OutputLevel=INFO
        )

        SiWrBarrelDigitizer = DDPlanarDigi(
            "SiWrBarrelDigitizer",
            **siWr_barrel_digi_args,
            OutputLevel=INFO
        )

        SiWrEndcapDigitizer = DDPlanarDigi(
            "SiWrEndcapDigitizer",
            **siWr_endcap_digi_args,
            OutputLevel=INFO
        )

        TopAlg += [ VXDBarrelDigitizer ]
        TopAlg += [ VXDEndcapDigitizer ]
        TopAlg += [ SiWrBarrelDigitizer ]
        TopAlg += [ SiWrEndcapDigitizer ]

    from Configurables import UniqueIDGenSvc
    ExtSvc += [UniqueIDGenSvc("uidSvc")]

    ### FIXME: add the STT digitizer once available
    # from Configurables import DCHdigi_v02
    # dch_digitizer = DCHdigi_v02(
    #     "DCHdigi2",
    #     InputSimHitCollection=["DCHCollection"],
    #     OutputDigihitCollection = ["DCHDigis"],
    #     OutputLinkCollection = ["DCHDigisSimAssociationCollection"],
    #     DCH_name="DCH_v2",
    #     zResolution_mm = 30.,               # in mm
    #     xyResolution_mm = 0.1,              # in mm
    #     Deadtime_ns = 400.0,                # in ns
    #     GasType=0,                          # 0: He(90%)-Isobutane(10%), 1: pure He, 2: Ar(50%)-Ethane(50%), 3: pure Ar
    #     ReadoutWindowStartTime_ns=1.0,      # in ns (taking into account time of flight, drift, and signal travel)
    #     ReadoutWindowDuration_ns=450.0,     # in ns
    #     DriftVelocity_um_per_ns=-1.0,       # in um/ns, if negative, automatically chosen based on GasType
    #     SignalVelocity_mm_per_ns=200.0,     # in mm/ns (Default: 2/3 of the speed of light)
    #     OutputLevel=INFO,
    # )
    # TopAlg += [dch_digitizer]

if runTrkFinder:
    # Run consistency checks first
    if not runTrkHitDigitization:
        raise RuntimeError("To run the track finder, the tracker hits digitization must be enabled.")
    if useLegacyVTXDigitizer:
        raise RuntimeError("The track finder requires DDPlanarDigi digitization of silicon detector hits.")

    # Load the GGTF, following example from:
    # k4RecTracker/Tracking/test/testTrackFinder/runTestTrackFinder.py
    from Configurables import GGTFTrackFinder

    modelPath = dataFolder + "SimpleGatrIDEAv3o1.onnx"   #FIXME: update to ALLEGRO-trained model when available

    # using default parameters for now
    tbeta = 0.6     # tbeta clustering parameter
    td = 0.3        # td clustering parameter

    trackFinder = GGTFTrackFinder(
        "GGTFTrackFinder",
        InputPlanarHitCollections=["VTXBDigis", "VTXDDigis", "SiWrDDigis", "SiWrBDigis"],
        InputWireHitCollections=[],  #FIXME: add STT hits when available
        OutputTracksGGTF=["PrefitTracks"],
        ModelPath=modelPath,
        Tbeta=tbeta,    # default clustering parameters
        Td=td,       # form the example in k4RecTracker
        OutputLevel=INFO,
    )
    TopAlg += [trackFinder]

if runTrkFitter:

    # Track fitter using Genfit2, following example from
    # k4RecTracker/Tracking/test/testTrackFitter/runTestTrackFitter.py
    from Configurables import GenfitTrackFitter

    trackFitter = GenfitTrackFitter(
        "GenfitTrackFitter",
        InputTracks=["PrefitTracks"],
        OutputFittedTracks=["FittedTracks"],
        OutputFittedTracksWithFilteredHits=["FittedTracksWithFilteredHits"],
        RunSingleEvaluation = True,
        UseBrems = True,
        BetaInit = 100,
        BetaFinal = 0.1,
        BetaSteps = 15,
        InitializationType = 1,
        SkipTrackOrdering = False,
        FilterTrackHits = True,
        OutputLevel=INFO,
    )
    TopAlg += [trackFitter]

#############################################################################
# Calorimeter digitization (merging hits into cells, EM scale calibration via sampling fractions)

caldigi_cfg = ComponentAccumulator()

# - ECAL readouts
ecalBarrelReadoutName2 = "ECalBarrelModuleThetaMerged2"    # barrel, after re-segmentation (for optimisation studies)
ecalBarrelHitsMergedName = 'ECalBarrelCellsMerged'
ecalBarrelPositionedCellsName2 = ecalBarrelReadoutName2 + "Positioned"

# Create cells in ECal barrel (calibrated and positioned - optionally with xtalk and noise added)
# from uncalibrated cells (+cellID info) from ddsim
from FCC_config.ALLEGRO.CreateCaloCellsConfig import CreateECalBarrelCellsCfg
caldigi_cfg.merge(CreateECalBarrelCellsCfg(flags))

# -  now, if we want to also save cells with coarser granularity:
if resegmentECalBarrel:
    # rewrite the cellId using the merged theta-module segmentation
    # (merging several modules and several theta readout cells).
    # Add noise at this step if you derived the noise already assuming merged cells
    # Step a: compute new cellID of cells based on new readout
    # (merged module-theta segmentation with variable merging vs layer)
    from FCC_config.ALLEGRO.CreateCaloCellsConfig import ReSegmentationECalBarrelCfg
    caldigi_cfg.merge (
        ReSegmentationECalBarrelCfg(flags,
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
from FCC_config.ALLEGRO.CreateCaloCellsConfig import CreateECalEndcapCellsCfg
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
    from FCC_config.ALLEGRO.CreateCaloCellsConfig import \
         CreateHCalBarrelCellsCfg, CreateHCalEndcapCellsCfg
    caldigi_cfg.merge(CreateHCalBarrelCellsCfg(flags))
    caldigi_cfg.merge(CreateHCalEndcapCellsCfg(flags))

caldigi_cfg.toVars (TopAlg, ExtSvc)


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

    from Configurables import CreatePositionedCaloCells
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
                                  f'keep {muonEndcapReadoutName}',
                                  f'keep {muonEndcapReadoutName}Contributions']
else:
    if not dropMuonHits:
        io_svc.outputCommands += ['keep MuonTaggerBarrelPhiTheta',
                                  'keep MuonTaggerBarrelPhiThetaContributions',
                                  'keep MuonTaggerEndcapPhiTheta',
                                  'keep MuonTaggerBarrelPhiThetaContributions']

    muonBarrelReadoutName = ""
    muonEndcapReadoutName = ""
    muonBarrelPositionedCellsName = ""
    muonEndcapPositionedCellsName = ""
    muonBarrelLinks = ""
    muonEndcapLinks = ""


if saveHits and saveCells:
    io_svc.outputCommands += ['keep MuonTaggerBarrelPhiThetaPositionedSimCaloHitLinks',
                              'keep MuonTaggerEndcapPhiThetaPositionedSimCaloHitLinks']


calclust_cfg = ComponentAccumulator()

if doSWClustering:
    from FCC_config.ALLEGRO.CreateCaloClustersConfig import CaloSWClusterCfg

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
                          outputSaveClusters,
                          runPhotonID = False,
                          calibrateClusters = False,
                          ))

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
                              calibrateClusters = False,
                              runPhotonID = False))

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
                              calibrateClusters = False,
                              addShapeParameters = False,
                              runPhotonID = False))


if doTopoClustering:
    from FCC_config.ALLEGRO.CreateCaloClustersConfig import CaloTopoClusterCfg

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
                            outputSaveClusters,
                            runPhotonID = False,
                            calibrateClusters = False,
                            ))

    # ECAL topoclusters with noise
    if addNoise:
        suffix = 'WithNoise'
        if filterNoiseThreshold >= 0:
            suffix += 'Filtered'

        calclust_cfg.merge(
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
                                calibrateClusters = False,
                                runPhotonID = False))

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
