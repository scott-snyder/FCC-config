# run_digi_reco_common.py
# Common Gaudi steering utilities shared across ALLEGRO detector configurations.
#
# Provides:
#   - str2bool              : CLI argument helper
#   - add_parser_args       : register all common CLI options onto a parser
#   - run_digi_reco         : full digitization/reconstruction sequence
#
# Specialised steering files only need to set path_to_detector, detectors_to_use,
# and a wire_tracker SimpleNamespace, then call run_digi_reco.

from Gaudi.Configuration import INFO, WARNING, DEBUG
from GaudiKernel.PhysicalConstants import pi

# debug printouts and verbosity: module-level so that they are also seen by the helper functions below,
# set from the --debug and --verbose options in run_digi_reco
debug = False
verbose = False


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        import argparse
        raise argparse.ArgumentTypeError("Boolean value expected.")


def add_parser_args(parser):
    """Register all common CLI arguments onto *parser* (k4FWCore parseArgs parser)."""
    parser.add_argument("--dataFolder", type=str, help="Path to calibration data folder", default="./")
    parser.add_argument("--includeHCal", type=str2bool, nargs="?", help="Also digitize HCal hits and create ECAL+HCAL clusters", const=True, default=False)
    parser.add_argument("--includeMuon", type=str2bool, nargs="?", help="Also digitize muon hits", const=True, default=False)
    parser.add_argument("--saveHits", type=str2bool, nargs="?", help="Save G4 hits", const=True, default=False)
    parser.add_argument("--saveCells", type=str2bool, nargs="?", help="Save cell collections", const=True, default=False)
    parser.add_argument("--keepUncalibratedCells", type=str2bool, nargs="?", help="Save uncalibrated cell collections", const=True, default=False)
    parser.add_argument("--addNoise", type=str2bool, nargs="?", help="Add noise to cells (ECAL barrel only)", const=True, default=False)
    parser.add_argument("--addCrosstalk", type=str2bool, nargs="?", help="Add cross-talk to cells (ECAL barrel only)", const=True, default=False)
    parser.add_argument("--addTruthTracks", type=str2bool, nargs="?", help="Add reco-level tracks (smeared truth tracks)", const=True, default=False)
    parser.add_argument("--addTracks", type=str2bool, nargs="?", help="Add reco-level tracks", const=True, default=False)
    parser.add_argument("--doSWClustering", type=str2bool, nargs="?", help="Enable or disable sliding window clustering", const=True, default=True)
    parser.add_argument("--createClusterCellCollections", type=str2bool, nargs="?", help="Create new cluster cell collections or just link clusters to cells in standard cell collections", const=True, default=True)
    parser.add_argument("--doTopoClustering", type=str2bool, nargs="?", help="Enable or disable topo clustering", const=True, default=True)
    parser.add_argument("--calibrateClusters", type=str2bool, nargs="?", help="Apply MVA calibration to clusters", const=True, default=False)
    parser.add_argument("--reconstructPi0s", type=str2bool, nargs="?", help="Search for cluster pairs consistent with the pi0 hypothesis", const=True, default=True)
    parser.add_argument("--runPhotonID", type=str2bool, nargs="?", help="Apply BDT-based photon ID tool to clusters", const=True, default=False)
    parser.add_argument("--runTRAPPIST", type=str2bool, nargs="?", help="Run TRAPPIST-based photon/pi0 ID", const=True, default=False)
    parser.add_argument("--runTrkHitDigitization", type=str2bool, nargs="?", help="Digitize tracker hits", const=True, default=False)
    parser.add_argument("--siDigitizer", type=str.lower, choices=["vtxdigitizer", "ddplanardigi", "vtxdigitizerdetailed"], help="Digitizer for silicon tracker hits: vtxdigitizer (smear truth), ddplanardigi or vtxdigitizerdetailed (projection-based)", default="ddplanardigi")
    parser.add_argument("--runTrkFinder", type=str2bool, nargs="?", help="Run Geometric Graph Track Finding (GGTF) on digitized tracker hits", const=True, default=False)
    parser.add_argument("--runTrkFitter", type=str2bool, nargs="?", help="Run track fitter on tracks found by GGTF", const=True, default=False)
    parser.add_argument("--runConformalTracking", type=str2bool, nargs="?", help="Run conformal tracking on digitized tracker hits", const=True, default=False)
    parser.add_argument("--runTrkValidation", type=str2bool, nargs="?", help="Run tracking validation", const=True, default=False)
    parser.add_argument("--debug", type=str2bool, nargs="?", help="Print debug information", const=True, default=False)
    parser.add_argument("--verbose", type=str2bool, nargs="?", help="Set the output level of all algorithms to DEBUG", const=True, default=False)
    parser.add_argument("--resegmentECalBarrel", type=str2bool, nargs="?", help="Resegment ECal barrel", const=True, default=False)


# ---------------------------------------------------------------------------
# Main digitization/reconstruction function
# ---------------------------------------------------------------------------

def run_digi_reco(path_to_detector, detectors_to_use, wire_tracker):
    """Run the full ALLEGRO digitization and reconstruction sequence.

    Parameters
    ----------
    path_to_detector : str
        Absolute path to the detector compact directory (ending with '/').
    detectors_to_use : list[str]
        List of XML filenames (relative to path_to_detector) that describe the
        detector geometry to load.
    wire_tracker : SimpleNamespace
        Bundle of wire-tracker-specific configuration.  Required attributes:
          det_id_key               - constant name in DectDimensions.xml, e.g. 'DetID_STT'
          id_name                  - key used in the IDs dict, e.g. 'STT'
          hit_collection           - e.g. 'STTCollection'
          digi_collection          - e.g. 'STTDigis'
          sim_digi_links           - e.g. 'STTDigisSimAssociationCollection'
          dNdx_output_collection
          dNdx_Zmax_param
          dNdx_Zmin_param
          dNdx_Rmin_param
          dNdx_Rmax_param
          dNdx_fill_factor
          digi_algo_name           - e.g. 'WireTrackerV1'
          dchi_name                - e.g. 'STT_o1_v01'
          is_stt                   - bool, pass isSTT=True to WireTrackerDigi_v01 if True
          drop_hits                - initial value of the dropWireHits flag
          drop_hits_command        - collection pattern to drop, e.g. 'STTCollection*'
          readoutWindowDuration_ns - duration of readout window in ns
    """

    import os
    from types import SimpleNamespace

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
    # filterNoiseThreshold = 2                 # if addNoise is true, and filterNoiseThreshold is >0, will filter away cells with abs(energy) below filterNoiseThreshold * expected sigma(noise)
    saveGaudiHists = False                     # save Gaudi::accumulator hists to separate ROOT files (they are filled by e.g. the DDPlanarDigi digitisers and ConformalTracking)

    # - general settings set via CLI
    from k4FWCore.parseArgs import parser
    add_parser_args(parser)
    # override dataFolder default to the value set above
    parser.set_defaults(dataFolder=dataFolderDef)

    opts = parser.parse_known_args()[0]
    dataFolder = opts.dataFolder                        # directory containing the calibration files
    runHCal = opts.includeHCal                          # if false, it will produce only ECAL clusters. if true, it will also produce ECAL+HCAL clusters
    runMuon = opts.includeMuon                          # if false, it will not digitize muon hits
    addNoise = opts.addNoise                            # add noise or not to the cell energy
    addCrosstalk = opts.addCrosstalk                    # switch on/off the crosstalk
    addTruthTracks = opts.addTruthTracks                # add truth tracks or not
    addRecoTracks = opts.addTracks                      # add reco-levelh tracks or not (will turn on tracker hit digitization, track finding and fitting
    runTrkHitDigitization = opts.runTrkHitDigitization  # digitize tracker hits (DDPlanarDigi as default)
    siDigitizer = opts.siDigitizer                      # digitizer for silicon tracker hits (vtxdigitizer, ddplanardigi or vtxdigitizerdetailed)
    runTrkFinder = opts.runTrkFinder                    # run GGTF on digitized tracker hits
    runTrkFitter = opts.runTrkFitter                    # run track fitter on tracks
    runConformalTracking = opts.runConformalTracking    # run conformal tracking on digitized tracker hits
    runTrkValidation = opts.runTrkValidation            # run tracking validation
    global debug, verbose
    debug = opts.debug                                  # print some debug statements
    verbose = opts.verbose                              # as debug and in addition set the output level of all algorithms to DEBUG

    # ensure consistency among options
    if verbose: debug = True
    if runTrkValidation: addRecoTracks = True           # track validation needs tracks
    if addRecoTracks: runTrkFitter = True               # tracks need track fitting
    if runTrkFitter: runTrkFinder = True                # track fitter needs track finder
    if runTrkFinder: runTrkHitDigitization = True       # track finding needs tracker hit digitization
    if runConformalTracking: runTrkHitDigitization = True  # conformal tracking needs tracker hit digitization

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
    # dropWireHits = True
    # dropSiWrHits = True
    # dropMuonHits = True
    dropVertexHits = False
    dropWireHits = wire_tracker.drop_hits
    dropSiWrHits = False
    dropMuonHits = False


    # ECAL barrel parameters for digitization
    # TODO: extract number of layers (for ECAL and HCAL) directly from the detector segmentations
    ecalBarrelLayers = 11
    ecalBarrelUpstreamParameters = [[0.028158491043365624, -1.564259408365951, -76.52312805346982, 0.7442903558010191, -34.894692961350195, -74.19340877431723]]
    ecalBarrelDownstreamParameters = [[0.00010587711361028165, 0.0052371999097777355, 0.69906696456064, -0.9348243433360095, -0.0364714212117143, 8.360401126995626]]
    ecalEndcapLayers = 98

    resegmentECalBarrel = opts.resegmentECalBarrel

    hcalBarrelLayers = 13
    hcalEndcapLayers = 22

    # - parameters for clustering (could also be made configurable via CLI)
    doSWClustering = opts.doSWClustering
    doTopoClustering = opts.doTopoClustering
    doCreateClusterCellCollection = opts.createClusterCellCollections  # create new collection with clustered cells or just link from cluster to original input cell collections
                                                                       # this applies to both SW and Topo cluster cell collections
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
                        # DEBUG also prints the dd4hep::DEBUG messages of the k4geo C++ drivers
                        OutputLevel=DEBUG if verbose else INFO
                        )

    geoservice.detectors = [
        os.path.join(path_to_detector, _det) for _det in detectors_to_use
    ]
    ExtSvc += [geoservice]

    # retrieve constants from the detector xml files:
    # all <constant> elements are collected starting from the main xml file(s) in detectors_to_use and recursively
    # following their <include ref="..."/> elements (paths relative to the including file, ${VAR} expanded from the
    # environment). As in DD4hep, the first definition of a constant is used if it is defined more than once.
    # geoConstants["NAME"] evaluates the expression of the constant NAME, including units (lengths are returned in
    # mm) and references to other constants
    import math
    import xml.etree.ElementTree as ET

    class GeoConstants(dict):
        def __init__(self, expressions, sources):
            super().__init__(mm=1., cm=10., m=1000., um=1.e-3, micrometer=1.e-3, nm=1.e-6,
                             pi=math.pi, sqrt=math.sqrt, sin=math.sin, cos=math.cos, tan=math.tan)
            self.expressions = expressions
            self.sources = sources

        def __missing__(self, name):
            if name not in self.expressions:
                raise RuntimeError(f"Constant {name} not found in {detectors_to_use} or the xml files they include")
            try:
                value = eval(self.expressions[name], {"__builtins__": {}}, self)
            except Exception as e:
                raise RuntimeError(f"Could not evaluate constant {name} = '{self.expressions[name]}' "
                                   f"from {self.sources[name]}: {e}") from e
            self[name] = value
            return value

    def collectConstants(xmlFile, expressions, sources, visited):
        xmlFile = os.path.normpath(os.path.abspath(xmlFile))
        if xmlFile in visited:
            return
        visited.add(xmlFile)
        if not os.path.isfile(xmlFile):
            # e.g. ${DD4hepINSTALL}/DDDetectors/compact/detector_types.xml if DD4hepINSTALL is not set
            if debug:
                print(f"WARNING: xml file {xmlFile} not found, its constants will not be available")
            return
        # ElementTree drops xml comments, so commented-out includes and constants are ignored
        for element in ET.parse(xmlFile).getroot().iter():
            if element.tag == 'constant':
                name, value = element.get('name'), element.get('value')
                if name not in expressions:
                    expressions[name] = value
                    sources[name] = xmlFile
                elif value != expressions[name]:
                    print(f"WARNING: constant {name} = '{value}' in {xmlFile} ignored, "
                          f"already defined as '{expressions[name]}' in {sources[name]}")
            elif element.tag == 'include' and element.get('ref'):
                ref = os.path.expandvars(element.get('ref'))
                collectConstants(os.path.join(os.path.dirname(xmlFile), ref), expressions, sources, visited)

    expressions, sources = {}, {}
    for xmlFile in geoservice.detectors:
        collectConstants(xmlFile, expressions, sources, set())
    geoConstants = GeoConstants(expressions, sources)

    siWrapperNlayers = int(geoConstants['SiWr_nLayers'])
    print("Number of SiWr layers from xml:", siWrapperNlayers, "(from", geoConstants.sources['SiWr_nLayers'] + ")")

    from FCC_config.DetIDs import detIDs

    # Configuration flags.
    class Flags:
        pass
    flags = Flags()
    flags.compactFile = geoservice.detectors[0]
    flags.dataFiles = dataFolder

    from FCC_config.ALLEGRO.CreateCaloCellsConfig import defineCaloCellFlags
    defineCaloCellFlags(flags)
    flags.ECal.Barrel.addCrosstalk = addCrosstalk
    flags.ECal.Barrel.filterNoiseThreshold = filterNoiseThreshold
    flags.ECal.Endcap.filterNoiseThreshold = filterNoiseThreshold

    from FCC_config.ALLEGRO.CreateCaloClustersConfig import defineCaloClusterFlags
    defineCaloClusterFlags(flags,
                           calibrateClusters = opts.calibrateClusters,
                           createClusterCellCollections = opts.createClusterCellCollections,
                           reconstructPi0s = opts.reconstructPi0s,
                           runPhotonID = opts.runPhotonID,
                           runTRAPPIST = opts.runTRAPPIST)


    # Input/Output handling
    from k4FWCore import IOSvc
    from Configurables import EventDataSvc
    io_svc = IOSvc("IOSvc")
    io_svc.Input = inputfile
    io_svc.Output = outputfile
    ExtSvc += [EventDataSvc("EventDataSvc")]

    if addTruthTracks or runTrkHitDigitization or addNoise:
        ExtSvc += ["RndmGenSvc"]


    # Tracking
    # Create tracks from gen particles
    if addTruthTracks:
        from Configurables import TracksFromGenParticles
        tracksFromGenParticles = TracksFromGenParticles("CreateTracksFromGenParticles",
                                                        InputGenParticles=["MCParticles"],
                                                        InputSimTrackerHits=["VertexBarrelCollection",
                                                                             "VertexEndcapCollection",
                                                                             wire_tracker.hit_collection,
                                                                             "SiWrBCollection",
                                                                             "SiWrDCollection"],
                                                        OutputTracks=["TracksFromGenParticles"],
                                                        OutputMCRecoTrackParticleAssociation=["TracksFromGenParticlesAssociation"],
                                                        ExtrapolateToECal=True,
                                                        KeepOnlyBestExtrapolation=False,
                                                        TrackerIDs=detIDs(flags,
                                                                          ["VXD_Barrel",
                                                                           "VXD_Disks",
                                                                           wire_tracker.id_name,
                                                                           "SiWr_Barrel",
                                                                           "SiWr_Disks"]),
                                                        OutputLevel=INFO)
        TopAlg += [tracksFromGenParticles]

        # Calculate dNdx from tracks
        from Configurables import TrackdNdxDelphesBased
        from Gaudi.Configuration import ERROR
        dNdxFromTracks = TrackdNdxDelphesBased("dNdxFromTracks",
                                               InputLinkCollection=tracksFromGenParticles.OutputMCRecoTrackParticleAssociation,
                                               OutputCollection=[wire_tracker.dNdx_output_collection],
                                               ZmaxParameterName=wire_tracker.dNdx_Zmax_param,
                                               ZminParameterName=wire_tracker.dNdx_Zmin_param,
                                               RminParameterName=wire_tracker.dNdx_Rmin_param,
                                               RmaxParameterName=wire_tracker.dNdx_Rmax_param,
                                               FillFactor=wire_tracker.dNdx_fill_factor,
                                               OutputLevel=ERROR)
        TopAlg += [dNdxFromTracks]


    # Tracker digitization
    if runTrkHitDigitization:
        import math
        # different sensors for inner and outer barrel/disks layers (see https://indico.cern.ch/event/1244371/contributions/5350233)
        # but assume DRD3 OCTOPUS resolutions (see https://indico.cern.ch/event/1702794/contributions/7161947/attachments/3320556/5945016/ALLEGRO_ID_INTRODUCTION_28July.pdf)
        # pixel pitches [mm] from the detector xmls: x and y follow grid_size_x and grid_size_y of the readout
        # segmentations (barrels: x = phi, y = z; disks: x = r, y = phi)
        innerVertexPitch_x = geoConstants["VTXIB_pitch_phi"]
        innerVertexPitch_y = geoConstants["VTXIB_pitch_z"]
        # 3 for the IDEA inner vertex detector, 4 for the ultra-light one, 5 for FCC-SEED
        # (selected in $K4GEO/FCCee/IDEA/compact/IDEA_o1_v04/VertexComplete_o1_v04.xml)
        innerVertexNlayers = int(geoConstants["nInnerVertexLayers"])
        if debug:
            print("Inner vertex barrel number of layers:", innerVertexNlayers, "(from", geoConstants.sources["nInnerVertexLayers"] + ")")
            print("Inner vertex barrel pitch x (phi) [mm]:", innerVertexPitch_x, "(from", geoConstants.sources["VTXIB_pitch_phi"] + ")")
            print("Inner vertex barrel pitch y (z) [mm]:", innerVertexPitch_y, "(from", geoConstants.sources["VTXIB_pitch_z"] + ")")
        innerVertexResolution_x = 0.003 # [mm], assume 3 µm resolution for DRD3 OCTOPUS sensors
        innerVertexResolution_y = 0.003 # [mm], assume 3 µm resolution for DRD3 OCTOPUS sensors
        innerVertexResolution_t = 5     # [ns], assume 5 ns timing resolution from time-over-threshold for DRD3 OCTOPUS sensors

        outerVertexPitch_x = geoConstants["VTXOB_pitch_phi"]
        outerVertexPitch_y = geoConstants["VTXOB_pitch_z"]
        outerVertexBarrelNlayers = 2
        if debug:
            print("Outer vertex barrel number of layers:", outerVertexBarrelNlayers)
            print("Outer vertex barrel pitch x (phi) [mm]:", outerVertexPitch_x, "(from", geoConstants.sources["VTXOB_pitch_phi"] + ")")
            print("Outer vertex barrel pitch y (z) [mm]:", outerVertexPitch_y, "(from", geoConstants.sources["VTXOB_pitch_z"] + ")")
        outerVertexResolution_x = 0.003 # [mm], assume 3 µm resolution for DRD3 OCTOPUS sensors
        outerVertexResolution_y = 0.003 # [mm], assume 3 µm resolution for DRD3 OCTOPUS sensors
        outerVertexResolution_t = 5     # [ns], assume 5 ns timing resolution from time-over-threshold for DRD3 OCTOPUS sensors

        vertexDisksNlayers = 3
        vertexDisksPitch_x = geoConstants["VTXD_pitch_r"]
        vertexDisksPitch_y = geoConstants["VTXD_pitch_phi"]
        if debug:
            print("Vertex disks number of layers:", vertexDisksNlayers)
            print("Vertex disks pitch x (r) [mm]:", vertexDisksPitch_x, "(from", geoConstants.sources["VTXD_pitch_r"] + ")")
            print("Vertex disks pitch y (phi) [mm]:", vertexDisksPitch_y, "(from", geoConstants.sources["VTXD_pitch_phi"] + ")")

        # silicon wrapper hits parameters
        siWrapperResolution_t = 0.040                  # [ns], assume 40 ps timing resolution per hit
        # one pitch per layer, indexed by the layer field of the cellID: in the barrel, both staves of a layer have
        # the same layer ID (the id of the <layer> element in the k4geo xml)
        siWrBarrelPitch_x = [geoConstants[f"SiWrB_pitch_phi{layer}"] for layer in range(siWrapperNlayers)]
        siWrBarrelPitch_y = [geoConstants[f"SiWrB_pitch_z{layer}"] for layer in range(siWrapperNlayers)]
        siWrDisksPitch_x = [geoConstants[f"SiWrD_pitch_r{layer}"] for layer in range(siWrapperNlayers)]
        siWrDisksPitch_y = [geoConstants[f"SiWrD_pitch_phi{layer}"] for layer in range(siWrapperNlayers)]
        if debug:
            print("SiWr barrel pitch x (phi) [mm]:", siWrBarrelPitch_x, "(from", geoConstants.sources["SiWrB_pitch_phi0"] + ")")
            print("SiWr barrel pitch y (z) [mm]:", siWrBarrelPitch_y, "(from", geoConstants.sources["SiWrB_pitch_z0"] + ")")
            print("SiWr disks pitch x (r) [mm]:", siWrDisksPitch_x, "(from", geoConstants.sources["SiWrD_pitch_r0"] + ")")
            print("SiWr disks pitch y (phi) [mm]:", siWrDisksPitch_y, "(from", geoConstants.sources["SiWrD_pitch_phi0"] + ")")
        # assume binary readout
        siWrBarrelResolution_x = [pitch / math.sqrt(12) for pitch in siWrBarrelPitch_x]
        siWrBarrelResolution_y = [pitch / math.sqrt(12) for pitch in siWrBarrelPitch_y]
        siWrDisksResolution_x = [pitch / math.sqrt(12) for pitch in siWrDisksPitch_x]
        siWrDisksResolution_y = [pitch / math.sqrt(12) for pitch in siWrDisksPitch_y]

        # Define arguments for digitizers
        vxd_barrel_digi_args = {
            "IsStrip": False,
            "ResolutionU": [innerVertexResolution_x]*innerVertexNlayers + [outerVertexResolution_x]*outerVertexBarrelNlayers,
            "ResolutionV": [innerVertexResolution_y]*innerVertexNlayers + [outerVertexResolution_y]*outerVertexBarrelNlayers,
            "ResolutionT": [innerVertexResolution_t]*innerVertexNlayers + [outerVertexResolution_t]*outerVertexBarrelNlayers,
            "SimTrackHitCollectionName": ["VertexBarrelCollection"],
            "SimTrkHitRelCollection": ["VTXBSimDigiLinks"],
            "SubDetectorName": "Vertex",
            "TrackerHitCollectionName": ["VTXBDigis"],
            "ForceHitsOntoSurface": True,
            "CellIDBits": 32,
        }

        vxd_endcap_digi_args = {
            "IsStrip": False,
            "ResolutionU": [outerVertexResolution_x]*vertexDisksNlayers,
            "ResolutionV": [outerVertexResolution_y]*vertexDisksNlayers,
            "ResolutionT": [outerVertexResolution_t]*vertexDisksNlayers,
            "SimTrackHitCollectionName": ["VertexEndcapCollection"],
            "SimTrkHitRelCollection": ["VTXDSimDigiLinks"],
            "SubDetectorName": "VertexDisks",
            "TrackerHitCollectionName": ["VTXDDigis"],
            "ForceHitsOntoSurface": True,
            "CellIDBits": 32,
        }

        siWr_barrel_digi_args = {
            "IsStrip": False,
            "ResolutionU": siWrBarrelResolution_x,
            "ResolutionV": siWrBarrelResolution_y,
            "ResolutionT": [siWrapperResolution_t]*len(siWrBarrelResolution_x),
            "SimTrackHitCollectionName": ["SiWrBCollection"],
            "SimTrkHitRelCollection": ["SiWrBSimDigiLinks"],
            "SubDetectorName": "SiWrB",
            "TrackerHitCollectionName": ["SiWrBDigis"],
            "ForceHitsOntoSurface": True,
            "CellIDBits": 32,
        }

        siWr_endcap_digi_args = {
            "IsStrip": False,
            "ResolutionU": siWrDisksResolution_x,
            "ResolutionV": siWrDisksResolution_y,
            "ResolutionT": [siWrapperResolution_t]*len(siWrDisksResolution_x),
            "SimTrackHitCollectionName": ["SiWrDCollection"],
            "SimTrkHitRelCollection": ["SiWrDSimDigiLinks"],
            "SubDetectorName": "SiWrD",
            "TrackerHitCollectionName": ["SiWrDDigis"],
            "ForceHitsOntoSurface": True,
            "CellIDBits": 32,
        }


        if siDigitizer == "vtxdigitizer":
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

        elif siDigitizer == "ddplanardigi":
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

        elif siDigitizer == "vtxdigitizerdetailed":

            # use projection-based digitiser
            # note: in order to work, barrel detector need ZPlanarData extension and disks need ZDiskPetalsData extension
            # both containing layer information
            # from which the sensor thickness is determined
            # see also https://github.com/key4hep/k4geo/blob/e1ba7bc3e0d7291ebe3f6a02abfa784f879e36cb/detector/tracker/VertexEndcap_o1_v06_geo.cpp#L117
            from Configurables import VTXdigitizerDetailed

            VXDBarrelDigitizer = VTXdigitizerDetailed(
                "VXDBarrelDigitizer",
                inputSimHits="VertexBarrelCollection",
                outputDigiHits="VTXBDigis",
                outputSimDigiAssociation="VTXBSimDigiLinks",
                detectorName="Vertex",  # compound detector: inner and outer vertex barrels both write to VertexBarrelCollection
                PixSizePhi=[innerVertexPitch_x]*innerVertexNlayers + [outerVertexPitch_x]*outerVertexBarrelNlayers,  # FIXME check x/y vs phi/theta
                PixSizeTheta=[innerVertexPitch_y]*innerVertexNlayers + [outerVertexPitch_y]*outerVertexBarrelNlayers,  # FIXME check x/y vs phi/theta
                tResolution=vxd_barrel_digi_args["ResolutionT"],
                Threshold=500.0,  # initial guess for ARCADIA-like sensors
                ThresholdSmearing=50.0,  # 10% of threshold
                OutputLevel=INFO,
                DebugHistos=False,
                DebugFileName="Debug_VTXBarrelDigitizer.root",
            )

            VXDEndcapDigitizer = VTXdigitizerDetailed(
                "VXDEndcapDigitizer",
                inputSimHits="VertexEndcapCollection",
                outputDigiHits="VTXDDigis",
                outputSimDigiAssociation="VTXDSimDigiLinks",
                detectorName="VertexDisks",
                PixSizePhi=[vertexDisksPitch_x]*vertexDisksNlayers,  # FIXME check x/y vs phi/theta
                PixSizeTheta=[vertexDisksPitch_y]*vertexDisksNlayers,  # FIXME check x/y vs phi/theta
                tResolution=vxd_endcap_digi_args["ResolutionT"],
                Threshold=500.0,  # initial guess for ARCADIA-like sensors
                ThresholdSmearing=50.0,  # 10% of threshold
                OutputLevel=INFO,
                DebugHistos=False,
                DebugFileName="Debug_VTXEndcapDigitizer.root",
            )

            SiWrBarrelDigitizer = VTXdigitizerDetailed(
                "SiWrBarrelDigitizer",
                inputSimHits="SiWrBCollection",
                outputDigiHits="SiWrBDigis",
                outputSimDigiAssociation="SiWrBSimDigiLinks",
                detectorName="SiWrB",
                PixSizePhi=siWrBarrelPitch_x,  # FIXME check x/y vs phi/theta
                PixSizeTheta=siWrBarrelPitch_y,  # FIXME check x/y vs phi/theta
                tResolution=siWr_barrel_digi_args["ResolutionT"],
                Threshold=500.0,  # number used in the past for beam background studies
                ThresholdSmearing=50.0,  # 10% of threshold
                OutputLevel=INFO,
                DebugHistos=False,
                DebugFileName="Debug_SiWrBarrelDigitizer.root",
            )

            SiWrEndcapDigitizer = VTXdigitizerDetailed(
                "SiWrEndcapDigitizer",
                inputSimHits="SiWrDCollection",
                outputDigiHits="SiWrDDigis",
                outputSimDigiAssociation="SiWrDSimDigiLinks",
                detectorName="SiWrD",
                PixSizePhi=siWrDisksPitch_x,  # FIXME check x/y vs phi/theta
                PixSizeTheta=siWrDisksPitch_y,  # FIXME check x/y vs phi/theta
                tResolution=siWr_endcap_digi_args["ResolutionT"],
                Threshold=500.0,  # number used in the past for beam background studies
                ThresholdSmearing=50.0,  # 10% of threshold
                OutputLevel=INFO,
                DebugHistos=False,
                DebugFileName="Debug_SiWrEndcapDigitizer.root",
            )

            TopAlg += [ VXDBarrelDigitizer ]
            TopAlg += [ VXDEndcapDigitizer ]
            TopAlg += [ SiWrBarrelDigitizer ]
            TopAlg += [ SiWrEndcapDigitizer ]

        from Configurables import UniqueIDGenSvc
        ExtSvc += [UniqueIDGenSvc("uidSvc")]

        from Configurables import WireTrackerDigi_v01
        wire_digi_kwargs = dict(
            InputSimHitCollection=[wire_tracker.hit_collection],
            OutputDigihitCollection=[wire_tracker.digi_collection],
            OutputLinkCollection=[wire_tracker.sim_digi_links],
            DCH_name=wire_tracker.dchi_name,
            zResolution_mm = 30.,               # in mm
            xyResolution_mm = 0.1,              # in mm
            Deadtime_ns = 400.0,                # in ns
            GasType=0,                          # 0: He(90%)-Isobutane(10%), 1: pure He, 2: Ar(50%)-Ethane(50%), 3: pure Ar
            ReadoutWindowStartTime_ns=1.0,      # in ns (taking into account time of flight, drift, and signal travel)
            ReadoutWindowDuration_ns=wire_tracker.readoutWindowDuration_ns,     # in ns
            DriftVelocity_um_per_ns=-1.0,       # in um/ns, if negative, automatically chosen based on GasType
            SignalVelocity_mm_per_ns=200.0,     # in mm/ns (Default: 2/3 of the speed of light)
            isSTT=wire_tracker.is_stt,
            OutputLevel=INFO,
        )
        wire_digitizer = WireTrackerDigi_v01(wire_tracker.digi_algo_name, **wire_digi_kwargs)
        TopAlg += [wire_digitizer]

    if runConformalTracking:
        from Configurables import ConformalTracking
        conformalTracking = ConformalTracking("ConformalTracking",
                                              TrackerHitCollectionNames=["VTXBDigis", "VTXDDigis", "SiWrBDigis", "SiWrDDigis"],
                                              RelationsNames=["VTXBSimDigiLinks", "VTXDSimDigiLinks", "SiWrBSimDigiLinks", "SiWrDSimDigiLinks"],
                                              MCParticleCollectionName=["MCParticles"],
                                              SiTrackCollectionName="ConformalSiTracks",
                                              MainTrackerHitCollectionNames=[],
                                              VertexBarrelHitCollectionNames=["VTXBDigis"],
                                              VertexEndcapHitCollectionNames=["VTXDDigis"],
                                              DebugPlots=True,
                                              DebugTiming=False,
                                              # the following parameters have not yet been tuned to ALLEGRO
                                              MaxHitInvertedFit=0,
                                              MinClustersOnTrackAfterFit=3,
                                              RetryTooManyTracks=False,
                                              SortTreeResults=True,
                                              ThetaRange=0.05,
                                              TooManyTracks=100000,
                                              trackPurity=0.7,
                                              ECalBarrelFaceSystemID=detIDs(flags,"ECAL_Barrel"),
                                              ECalEndcapFaceSystemID=detIDs(flags,"ECAL_Endcap"),
                                              OutputLevel=INFO)

        # the following parameters have not yet been tuned to ALLEGRO
        parameters = {
            "SiliconTracking": {
                "collections": ["VTXBDigis","VTXDDigis","SiWrBDigis","SiWrDDigis"],
                "params": {
                    "MaxCellAngle": 0.01,
                    "MaxCellAngleRZ": 0.01,
                    "Chi2Cut": 100,
                    "MinClustersOnTrack": 3,
                    "MaxDistance": 0.05,
                    "SlopeZRange": 10.0,
                    "HighPTCut": 10.0,
                },
                "flags": ["HighPTFit", "VertexToTracker"],
                "functions": ["CombineCollections", "BuildNewTracks"],
            },
        }

        from conformal_tracking_utils import configure_conformal_tracking_steps
        configure_conformal_tracking_steps(conformalTracking, parameters)
        TopAlg += [conformalTracking]

        saveGaudiHists = True

    if runTrkFinder:
        # Run consistency checks first
        if not runTrkHitDigitization:
            raise RuntimeError("To run the track finder, the tracker hits digitization must be enabled.")
        if siDigitizer == "vtxdigitizer":
            raise RuntimeError("The track finder does not support VTXdigitizer digitization of silicon detector hits.")

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
            InputWireHitCollections=[wire_tracker.digi_collection],
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

        trk_fitter_kwargs = dict(
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
            WireTrackerName = wire_tracker.dchi_name,
            OutputLevel=INFO,
        )
        trackFitter = GenfitTrackFitter("GenfitTrackFitter", **trk_fitter_kwargs)
        TopAlg += [trackFitter]

    if runTrkValidation:
        # perfect track fitting
        from Configurables import PerfectTrackFinder, GenfitTrackFitter
        perfect_finder = PerfectTrackFinder(
            "PerfectTrackFinder",
            InputMCParticles=["MCParticles"],
            InputPlanarHitCollections=["VTXBSimDigiLinks","VTXDSimDigiLinks","SiWrBSimDigiLinks","SiWrDSimDigiLinks"],
            InputWireHitCollections=[wire_tracker.sim_digi_links],
            OutputPerfectTracks=["PerfectPrefitTracks"],
            OutputLevel=INFO
        )
        perf_fitter_kwargs = dict(
            InputTracks=["PerfectPrefitTracks"],
            OutputFittedTracks=["PerfectFittedTracks"],
            OutputFittedTracksWithFilteredHits=["PerfectFittedTracksWithFilteredHits"],
            OutputFittedHits=["PerfectFittedHits"],
            RunSingleEvaluation=True,
            UseBrems=True,
            BetaInit=100.0,
            BetaFinal=0.1,
            BetaSteps=15,
            InitializationType=1,
            SkipTrackOrdering=False,
            FilterTrackHits=True,
            WireTrackerName=wire_tracker.dchi_name,
            OutputLevel=INFO
        )
        perfect_fitter = GenfitTrackFitter("PerfectTrackFitter", **perf_fitter_kwargs)

        TopAlg += [perfect_finder, perfect_fitter]

        from Configurables import TrackingValidation
        outputFileValid = io_svc.Output.replace(".root", "_trkval.root")
        trackValidation = TrackingValidation(
            "TrackingValidation",
            OutputFile=outputFileValid,
            Mode=0,
            Bz=2.0,
            RefPointX=0.0,
            RefPointY=0.0,
            RefPointZ=0.0,
            DoPerfectFit=1,
            FinderEfficiencyDefinition=1,
            FinderPurityThreshold=0.75,
            MCParticles=["MCParticles"],
            HitSimLinks=["VTXBSimDigiLinks","VTXDSimDigiLinks","SiWrBSimDigiLinks","SiWrDSimDigiLinks",wire_tracker.sim_digi_links],
            FinderTracks=["PrefitTracks"],
            FittedTracks=["FittedTracks"],
            PerfectFittedTracks=["PerfectFittedTracks"],
            OutputLevel=INFO)
        TopAlg += [trackValidation]

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

        # ecal endcap cells with noise not filtered
        caldigi_cfg.merge(
            CreateECalEndcapCellsCfg (flags,
                                      'CreatePositionedECalEndcapCellsWithNoise',
                                      addNoise = True,
                                      cellsNameSuffix = 'WithNoise'))

        # ecal endcap cells with noise filtered
        caldigi_cfg.merge(
            CreateECalEndcapCellsCfg (flags,
                                      'CreatePositionedECalEndcapCellsWithNoiseFiltered',
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
    else:
        muonBarrelReadoutName = ""
        muonEndcapReadoutName = ""
        muonBarrelPositionedCellsName = ""
        muonEndcapPositionedCellsName = ""
        muonBarrelLinks = ""
        muonEndcapLinks = ""

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
                              clusterOnly = True))
        calclust_cfg.toVars (TopAlg, ExtSvc)

        # SW ECAL barrel and endcap clusters with noise
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

            calclust_cfg.merge (
                CaloSWClusterCfg (flags,
                                  {'ECAL_Endcap': flags.ECal.Endcap.cellsName + suffix},
                                  'EMECCaloClusters' + suffix,
                                  # threshold --- large number of clusters
                                  # with noise, consider raising to 0.3 if not
                                  # looking at low-energy cluster
                                  # reconstruction, or use filtered cells
                                  0.1,
                                  'StandardSize',
                                  outputSaveClusters,
                                  clusterOnly = True))

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
                                  clusterOnly = True))

        # experimental: MUON clusters
        if (runMuon):
            calclust_cfg.merge (
                CaloSWClusterCfg (flags,
                                  {'Muon_Barrel': muonBarrelPositionedCellsName,
                                   'Muon_Endcap': muonEndcapPositionedCellsName,
                                   },
                                  'MuonCaloClusters',
                                  0.00,  # threshold,
                                  'MuonSize',
                                  outputSaveClusters,
                                  clusterOnly = True))

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
                                clusterOnly = True))

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

            calclust_cfg.merge(
                CaloTopoClusterCfg (flags,
                                    {'ECAL_Endcap': flags.ECal.Endcap.cellsName + suffix},
                                    'EMECCaloTopoClusters' + suffix,
                                    0.1,  # threshold,
                                    outputSaveClusters,
                                    clusterOnly = True))

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
                                    clusterOnly = True))

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


    # Configure the output

    # drop the empty cells
    io_svc.outputCommands = ["keep *",
                             "drop emptyCaloCells"]

    # drop the uncalibrated cells
    if dropUncalibratedCells:
        io_svc.outputCommands.append("drop %s" % flags.ECal.Barrel.readoutName)
        io_svc.outputCommands.append("drop %s" % ecalBarrelReadoutName2)
        io_svc.outputCommands.append("drop %s" % flags.ECal.Endcap.readoutName)
        if runHCal:
            io_svc.outputCommands.append("drop %s" % flags.HCal.Barrel.readoutName)
            io_svc.outputCommands.append("drop %s" % flags.HCal.Endcap.readoutName)
        else:
            io_svc.outputCommands += ["drop HCal*"]

        # drop the intermediate ecal barrel cells in case of a resegmentation
        if resegmentECalBarrel:
            io_svc.outputCommands.append("drop ECalBarrelCellsMerged")

    # drop lumi, vertex, DCH, Muons (unless want to keep for event display)
    if dropLumiCalHits:
        io_svc.outputCommands.append("drop Lumi*")
    if dropVertexHits:
        io_svc.outputCommands.append("drop VertexBarrelCollection*")
        io_svc.outputCommands.append("drop VertexEndcapCollection*")
    if dropWireHits:
        io_svc.outputCommands.append("drop " + wire_tracker.drop_hits_command)
    if dropSiWrHits:
        io_svc.outputCommands.append("drop SiWrBCollection*")
        io_svc.outputCommands.append("drop SiWrDCollection*")
    if dropMuonHits:
        io_svc.outputCommands.append("drop MuonTagger*PhiThetaContributions")   # hits
        io_svc.outputCommands.append("drop MuonTagger*PhiTheta")                # uncalibrated cells
        io_svc.outputCommands.append("drop MuonTagger*PhiThetaPositioned")      # calibrated cells

    # drop hits/positioned cells/cluster cells if desired
    if not saveHits:
        io_svc.outputCommands.append("drop *%sContributions" % flags.ECal.Barrel.readoutName)
        io_svc.outputCommands.append("drop *%sContributions" % ecalBarrelReadoutName2)
        io_svc.outputCommands.append("drop *%sContributions" % flags.ECal.Endcap.readoutName)
        if runHCal:
            io_svc.outputCommands.append("drop *%sContributions" % flags.HCal.Barrel.readoutName)
            io_svc.outputCommands.append("drop *%sContributions" % flags.HCal.Endcap.readoutName)
    if not saveCells:
        io_svc.outputCommands.append("drop %s" % flags.ECal.Barrel.cellsName)
        io_svc.outputCommands.append("drop %s" % flags.ECal.Endcap.cellsName)
        if addNoise:
            io_svc.outputCommands.append("drop %sWithNoise*" % flags.ECal.Barrel.cellsName)
            io_svc.outputCommands.append("drop %sWithNoise*" % flags.ECal.Endcap.cellsName)
        if resegmentECalBarrel:
            io_svc.outputCommands.append("drop %s" % ecalBarrelPositionedCellsName2)
        if runHCal:
            io_svc.outputCommands.append("drop %s" % hcalBarrelPositionedCellsName)
            io_svc.outputCommands.append("drop %s" % hcalEndcapPositionedCellsName)
    # only save cluster cells if the user creates these collections
    if not flags.CaloSW.createClusterCellCollections and not flags.CaloTopo.createClusterCellCollections:
        io_svc.outputCommands.append("drop *Calo*Cluster*Cells*")
    # drop hits<->cells links if either of the two collections are not saved
    if not saveHits or not saveCells:
        io_svc.outputCommands.append("drop *SimCaloHitLinks")

    # if we decorate the clusters, we can drop the non-decorated ones
    if flags.CaloSW.addShapeParameters or flags.CaloTopo.addShapeParameters:
        for algo in TopAlg:
            if algo.__class__.__name__ == "AugmentClustersFCCee":
                io_svc.outputCommands.append("drop %s" % algo.inClusters)

    # If running TRAPPIST, the unpaired clusters produced by PairCaloClustersPi0
    # can be dropped because TRAPPIST produces a copy with the score added.
    if opts.runTRAPPIST:
        for algo in TopAlg:
            if algo.__class__.__name__ == "PairCaloClustersPi0":
                io_svc.outputCommands.append(
                    "drop %s" % algo.unpairedClusters.Path
               )

    # this dumps to a separate output ROOT file the Gaudi::accumulator histograms
    # filled by the scheduled algorithms, in our case ConformalTracking (if enabled)
    # and all the Si digitisers based on DDPlanarDigi
    if saveGaudiHists:
        from Configurables import RootHistSvc
        from Configurables import Gaudi__Histograming__Sink__Root as RootHistoSink
        hps = RootHistSvc("HistogramPersistencySvc")
        root_hist_svc = RootHistoSink("RootHistoSink")
        root_hist_svc.FileName = "ALLEGRO_gaudi_hist.root"
        ExtSvc += [root_hist_svc]

    # configure the application
    print("Scheduled algorithms:")
    print(TopAlg)
    print("External services:")
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
        if verbose:
            algo.OutputLevel = DEBUG
