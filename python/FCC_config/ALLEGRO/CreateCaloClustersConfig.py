#
# File: python/FCC_config/ALLEGRO/CreateCaloClustersConfig.py
# Author: scott snyder <snyder@bnl.gov>
# Date: Jun, 2026
# Purpose: ALLEGRO job configuration functions for creating calorimeter clusters.
#
# ComponentAccumulator style configuration functions for ALLEGRO calorimeter
# cluster making.
#
# The main configuration functiosns for clsuter making are
# CaloSWClusterCfg and CaloTopoClusterCfg.  See those two below,
# as well as CaloClusterCfg (which does most of the work), for details.
# Here is an example of configuring sliding-window clustering:
#
#    class Flags:
#        pass
#    flags = Flags()
#    flags.compactFile = os.environ.get("K4GEO", "") + "/FCCee/ALLEGRO/compact/ALLEGRO_o1_v03/ALLEGRO_o1_v03.xml"
#    from FCC_config.ALLEGRO.CreateCaloCellsConfig import defineCaloCellFlags
#    from FCC_config.ALLEGRO.CreateCaloClustersConfig import defineCaloClsuterFlags
#    defineCaloCellFlags(flags)
#    defineCaloClusterFlags(flags)
#
#    outputSaveClusters = []
#    from FCC_config.ComponentAccumulator import ComponentAccumulator
#    from FCC_config.ALLEGRO.CreateCaloClustersConfig import CaloSWClusterCfg
#    calclus_cfg = ComponentAccumulator()
#    calclus_cfg.merge (
#      CaloSWClusterCfg (flags,
#                       { 'ECAL_Barrel' : flags.ECal.Barrel.cellsName },
#                       'EMBCaloClusters',
#                       0.04,  # threshold
#                       'StandardSize',
#                       outputSaveClusters))
#    calclus_cfg.toVars (TopAlg, ExtSvc)
#


from FCC_config.ComponentAccumulator import ComponentAccumulator
import Configurables as C
from math import pi
from FCC_config.DetIDs import detIDs


############################################################################
# Parameters
#

# ECAL barrel parameters for digitization
from .CreateCaloCellsConfig import ecalBarrelLayers, ecalEndcapLayers, hcalBarrelLayers, hcalEndcapLayers

# to be recalculated for V03, separately for topo and calo clusters...
ecalBarrelThetaWeights = [-1, 3.0, 3.0, 3.0, 4.25, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0]

ecalBarrelUpstreamParameters = [[  0.028158491043365624,
                                  -1.564259408365951,
                                 -76.52312805346982,
                                   0.7442903558010191,
                                 -34.894692961350195,
                                 -74.19340877431723]]

ecalBarrelDownstreamParameters = [[ 0.00010587711361028165,
                                    0.0052371999097777355,
                                    0.69906696456064,
                                   -0.9348243433360095,
                                   -0.0364714212117143,
                                    8.360401126995626]]


swClustertypes = {}

# to be tested: about -2% of energy but smaller cluster, less noise
swClustertypes['ReducedSize'] = {
    'nThetaWindow'     : 7,
    'nPhiWindow'       : 9,
    'nThetaPosition'   : 5,
    'nPhiPosition'     : 7,
    'nThetaDuplicates' : 7,
    'nPhiDuplicates'   : 9,
    'nThetaFinal'      : 7,
    'nPhiFinal'        : 9,
    }

# muon clusters
swClustertypes['MuonSize'] = {
    'nThetaWindow'     : 3,
    'nPhiWindow'       : 5,
    'nThetaPosition'   : 3,
    'nPhiPosition'     : 5,
    'nThetaDuplicates' : 3,
    'nPhiDuplicates'   : 5,
    'nThetaFinal'      : 3,
    'nPhiFinal'        : 5,
    }

# default
swClustertypes['StandardSize'] = {
    'nThetaWindow'     :  9,
    'nPhiWindow'       : 17,
    'nThetaPosition'   :  5,
    'nPhiPosition'     : 11,
    'nThetaDuplicates' :  7,
    'nPhiDuplicates'   : 13,
    'nThetaFinal'      :  9,
    'nPhiFinal'        : 17,
    }


############################################################################
# SW cluster creation.
#

def CaloTowerTool (flags, name, cells, caloIDs):
    """Return tool to combine cells into towers for SW cluster making.

flags: Configuration flags.
name: The name of the tool
cells: List of names of cell collections to read.
caloIDs: List of corresponding detector IDs.
"""
    return C.CaloTowerToolFCCee(name,
                                deltaThetaTower=4 * 0.009817477 / 4,
                                deltaPhiTower=2 * 2 * pi / 1536.,
                                thetaMin=0.0, thetaMax=pi,
                                phiMin=-pi, phiMax=pi,
                                cells=cells,
                                calorimeterIDs=caloIDs,
                                nSubDetectors=3)


def CreateCaloSWClustersCfg (flags,
                             outputClusters,
                             cells,
                             caloIDs,
                             threshold,
                             clusterType,
                             **kw):
    """Return a CA to create SW clusters.

flags: Configuration flags.
outputClusters: The name of the cluster collection being made.
cells: The name of the input cell collection.
caloIDs: List of detector IDs being used.
threshold: Et cut for cluster finding.
clusterType: One of ReducedSize, MuonSize, StandardSize.
"""
    cfg = ComponentAccumulator()

    towerTool = CaloTowerTool(flags,
                              outputClusters + "TowerTool",
                              cells,
                              caloIDs)

    kw.update (swClustertypes[clusterType])
    alg = C.CreateCaloClustersSlidingWindowFCCee("Create" + outputClusters,
                                                 towerTool = towerTool,
                                                 energyThreshold = threshold,
                                                 energySharingCorrection = False,
                                                 createClusterCellCollection = flags.CaloSW.createClusterCellCollections,
                                                 clusters = outputClusters,
                                                 clusterCells = outputClusters.replace('Clusters', 'Cluster') + 'Cells',
                                                 **kw
                                                 )
    cfg.addAlg(alg)
    return cfg


############################################################################
# Topo cluster creation.
#


def CaloTopoNeighboursTool (flags, clusterNameRoot, caloIDs):
    """Return tool to find cell neighbours for topo cluster making.

flags: Configuration flags.
clusterNameRoot: Name of the clusters we're making.  The tool name
    will be derived from this.
caloIDs: List of detector IDs being used.
"""
    # Pick appropriate neighbour map based on the set of IDs.
    if caloIDs == [detIDs(flags, 'ECAL_Barrel')]:
        neighboursMap = flags.CaloTopo.EMBNeighbours
    elif caloIDs == [detIDs(flags, 'ECAL_Endcap')]:
        neighboursMap = flags.CaloTopo.EMECNeighbours
    else:
        neighboursMap = flags.CaloTopo.AllNeighbours
    return C.TopoCaloNeighbours(clusterNameRoot + 'NeighboursMap',
                                fileName = flags.dataFiles + neighboursMap + '.root')


def CaloTopoNoiseTool (flags, clusterNameRoot, caloIDs):
    """Return tool to find cell noise for topo cluster making.

flags: Configuration flags.
caloIDs: List of detector IDs being used.
clusterNameRoot: Name of the clusters we're making.  The tool name
    will be derived from this.
"""
    # Pick appropriate noise map based on the set of IDs.
    if caloIDs == [detIDs(flags, 'ECAL_Barrel')]:
        noiseMap = flags.CaloTopo.EMBNoise
    elif caloIDs == [detIDs(flags, 'ECAL_Endcap')]:
        noiseMap = flags.CaloTopo.EMECNoise
    else:
        noiseMap = flags.CaloTopo.AllNoise
    return C.TopoCaloNoisyCells(clusterNameRoot + 'NoiseMap',
                                fileName = flags.dataFiles + noiseMap + '.root')



def CreateCaloTopoClustersCfg (flags,
                               outputClusters,
                               cells,
                               caloIDs,
                               threshold):
    """Return a CA to create topo clusters.

flags: Configuration flags.
outputClusters: The name of the cluster collection being made.
cells: The name of the input cell collection.
caloIDs: List of detector IDs being used.
threshold: Et cut for cluster finding.
"""
    cfg = ComponentAccumulator()
    alg = C.CaloTopoClusterFCCee('Create' + outputClusters,
                                 cells = cells,
                                 clusters = outputClusters,
                                 clusterCells = outputClusters.replace("Clusters", "Cluster") + "Cells",
                                 neigboursTool = CaloTopoNeighboursTool(flags,
                                                                        outputClusters,
                                                                        caloIDs),
                                 noiseTool = CaloTopoNoiseTool(flags,
                                                               outputClusters,
                                                               caloIDs),
                                 seedSigma = flags.CaloTopo.seedSigma,
                                 neighbourSigma = flags.CaloTopo.neighbourSigma,
                                 lastNeighbourSigma = flags.CaloTopo.lastNeighbourSigma,
                                 minClusterEnergy = threshold,
                                 calorimeterIDs = caloIDs,
                                 createClusterCellCollection = flags.CaloTopo.createClusterCellCollections)

    cfg.addAlg(alg)
    return cfg



def PairCaloClustersPi0Cfg (flags, inputClusters, outputClusters):
    """Return a CA to find pi0 candidates.

Creates algorithm to identify resolved pi0->two photon cluster candidates.
see: https://indico.cern.ch/event/1483299/contributions/6488594/attachments/3056315/5403634/ALLEGRO_photon_pi0_20250424.pdf

flags: Configuration flags.
inputClusters: The name of the cluster collection to use as input.
outputClusters: Root name for resolved pi0 clusters being made.
"""
    cfg = ComponentAccumulator()
    alg = C.PairCaloClustersPi0('resolvedPi0FromClusterPair' + outputClusters,
                                inClusters = inputClusters,
                                unpairedClusters = 'Unpaired' + inputClusters,
                                pairedClusters  = 'Paired' + inputClusters,
                                reconstructedPi0 = 'ResolvedPi0Particle' + outputClusters,
                                massPeak = flags.CaloTopo.pi0MassPeak,
                                massLow  = flags.CaloTopo.pi0MassLow,
                                massHigh = flags.CaloTopo.pi0MassHigh)
    cfg.addAlg(alg)
    return cfg
    

############################################################################
# Common algorithms.
#

def CorrectCaloClustersCfg (flags, inputClusters, outputClusters):
    """Return a CA to do cluster correction.

Simple parametrisations of up/downstream losses for ECAL-only clusters.
Not to be applied for ECAL+HCAL clustering.
Superseded by MVA calibration, but can be turned on here for the purpose
of testing that the code is not broken - will end up in separate cluster
collection.

Note that this only works for ECal barrel given various  hardcoded quantities.

flags: Configuration flags.
inputClusters: The name of the cluster collection to use as input.
outputClusters: Root name for the output cluster collection.
"""
    cfg = ComponentAccumulator()

    alg = C.CorrectCaloClusters("Correct" + outputClusters,
                                inClusters = inputClusters,
                                outClusters = "Corrected" + outputClusters,
                                systemIDs = detIDs(flags,["ECAL_Barrel"]),
                                numLayers = [ecalBarrelLayers],
                                firstLayerIDs = [0],
                                lastLayerIDs = [ecalBarrelLayers - 1],
                                readoutNames = [flags.ECal.Barrel.readoutName],
                                upstreamParameters = ecalBarrelUpstreamParameters,
                                upstreamFormulas = [['[0]+[1]/(x-[2])', '[0]+[1]/(x-[2])']],
                                downstreamParameters = ecalBarrelDownstreamParameters,
                                downstreamFormulas=[['[0]+[1]*x', '[0]+[1]/sqrt(x)', '[0]+[1]/x']])

    cfg.addAlg(alg)
    return cfg


def AugmentCaloClustersCfg (flags, clusterFlags, detectors, inputClusters, outputClusters):
    cfg = ComponentAccumulator()

    detectors = detectors[:]
    detectors.sort()

    systemNames = []
    numLayers = []
    readoutNames = []
    thetaRecalcWeights = []
    if 'ECAL_Barrel' in detectors:
        systemNames.append ('EMB')
        numLayers.append (ecalBarrelLayers)
        readoutNames.append (flags.ECal.Barrel.readoutName)
        thetaRecalcWeights.append (ecalBarrelThetaWeights)
    if 'ECAL_Endcap' in detectors:
        systemNames.append ('EMEC')
        numLayers.append (ecalEndcapLayers)
        readoutNames.append (flags.ECal.Endcap.readoutName)
        thetaRecalcWeights.append ([-1] * ecalEndcapLayers)
    if 'HCAL_Barrel' in detectors:
        systemNames.append ('HCALB')
        numLayers.append (hcalBarrelLayers)
        readoutNames.append (flags.HCal.Barrel.readoutName)
        thetaRecalcWeights.append ([-1] * hcalBarrelLayers)
    if 'HCAL_Endcap' in detectors:
        systemNames.append ('HCALE')
        numLayers.append (hcalEndcapLayers)
        readoutNames.append (flags.HCal.Endcap.readoutName)
        thetaRecalcWeights.append ([-1] * hcalEndcapLayers)

    ndet = len(systemNames)

    from Gaudi.Configuration import INFO, DEBUG, VERBOSE, ERROR
    alg = C.AugmentClustersFCCee('Augment' + outputClusters,
                                 inClusters = inputClusters,
                                 outClusters = 'Augmented' + outputClusters,
                                 systemIDs = detIDs(flags, detectors),
                                 systemNames = systemNames,
                                 numLayers = numLayers,
                                 readoutNames = readoutNames,
                                 # would make more sense to use pseudolayers for endcaps
                                 layerFieldNames = ['layer'] * ndet,
                                 # will be ignored for systems!=EMB
                                 thetaFieldNames = ['theta'] * ndet,
                                 # will be ignored for systems!=EMB
                                 moduleFieldNames = ['module'] * ndet,
                                 thetaRecalcWeights = thetaRecalcWeights,
                                 # we want these variables to train the photon
                                 # ID BDT (but only for ECAL-only clusters!)
                                 do_photon_shapeVar = (systemNames == ['EMB']),
                                 do_widthTheta_logE_weights = clusterFlags.logEWeightInPhotonID,
                                 )
    
    cfg.addAlg(alg)
    return cfg


def CalibrateCaloClustersCfg (flags, clusterFlags, inputClusters, outputClusters):
    """Return a CA to do cluster MVA calibration.

Note that this only works for ECal barrel given various  hardcoded quantities.

flags: Configuration flags.
clusterFlags: Cluster-specific configuration flags (flags.CaloSW or flags.CaloTopo).
inputClusters: The name of the cluster collection to use as input.
outputClusters: Root name for the output cluster collection.
"""
    cfg = ComponentAccumulator()

    alg = C.CalibrateCaloClusters('Calibrate' + outputClusters,
                                  inClusters = inputClusters,
                                  outClusters = 'Calibrated' + outputClusters,
                                  systemIDs = detIDs(flags, ['ECAL_Barrel']),
                                  systemNames = ['EMB'],
                                  numLayers = [ecalBarrelLayers],
                                  firstLayerIDs = [0],
                                  readoutNames = [flags.ECal.Barrel.readoutName],
                                  layerFieldNames = ['layer'],
                                  calibrationFile = flags.dataFiles + clusterFlags.calibrationFile,
                                  )
    cfg.addAlg(alg)
    return cfg



def CaloPhotonIDCfg (flags, inputClusters, nameRoot, modelNameRoot):
    """Return a CA to run photon ID.

flags: Configuration flags.
inputClusters: The name of the cluster collection to use as input, and the
   root for the output cluster container.
nameRoot: Suffix to add to the algorithm name.
modelNameRoot: Root name of the onnx model to use.
"""
    cfg = ComponentAccumulator()
    alg = C.PhotonIDTool("PhotonID" + nameRoot,
                         inClusters = inputClusters,
                         outClusters = "PhotonID" + inputClusters,
                         mvaModelFile = f'{flags.dataFiles}bdt-photonid-weights-{modelNameRoot}.onnx',
                         mvaInputsFile = f'{flags.dataFiles}bdt-photonid-settings-{modelNameRoot}.json',
                         )
    cfg.addAlg(alg)
    return cfg


############################################################################
# Overall configuration.
#

def CaloClusterCfg (flags,
                    clusterFlags,
                    inputCells,
                    outputClusters,
                    outputSaveClusters,
                    creatorCfg,
                    creatorCfgArgs,
                    applyUpDownstreamCorrections = None,
                    addShapeParameters = None,
                    calibrateClusters = None,
                    runPhotonID = None):
    """Return a CA to run calorimeter clustering (either SW or topo).

This set up a chain of algorithms to run cluster finding.
Below, assume outputClusters is "Clusts".

 - The clustering algorithm itself.  This is set up by clusterCfg.
   This will make a collection "Clusts".
 - If applyUpDownstreamCorrections is set, then the old up/downstream
   corrections will be used to produce "CorrectedClusts".
   These are not used further.
 - If applyShapeParameters is set, then cluster augmentation is done
   producing from "Clusts" the collection "AugmentedClusts".
   This can currently be done for EMBCalo[Topo]Clusters, EMECCalo{Topo]Clusters,
   and Calo[Topo]Clusters.

   For topo clusters, we then reconstruct pi0 candidates, producing
   "UnpairedClusts", "PairedClusts", and "ResolvedPi0ParticleClusts".
 - If calibrateClusters is set, then we apply MVA cluster calibration,
   producing "CalibratedClusts".
 - If runPhotonID and applyShapeParameters are set, then we run photon ID,
   producing "PhotonIDClusts".

flags: Configuration flags.
clusterFlags: Cluster-specific configuration flags (flags.CaloSW or flags.CaloTopo).
inputCells: List of input cell collections to use.
  Should be a map from detector name (such as ECAL_Barrel) to cell
  collection name.
outputClusters: Root name for the clusters we produce.
  Should start with one of EMBCalo[Topo]Clusters, EMECCalo[Topo]Clusters,
  Calo[Topo]Clusters.
outputSaveClusters: List of clusters for which we want to create the
  truth with links.
creatorCfg: Function to call to set up the actual cluster creation.
  Should return a CA and have an argument list starting with
  flags, outputClusters, cells, caloIDs.
  Additional arguments given by creatorCfgArgs.
creatorCfgArgs: Additional keyword arguments to pass to creatorCfg, as a map.
applyUpDownstreamCorrections: Control if (non-MVA) cluster correction
  is applied.  If defaulted, taken from the cluster flags.
addShapeParameters: Control if cluster augmentation is done.
  If defaulted, taken from the cluster flags.
calibrateClusters: Control if MVA cluster calibration is done.
  If defaulted, taken from the cluster flags.
runPhotonID: Control if photonID done.
  If defaulted, taken from the cluster flags.
  addShapeParameters must also be true for this to run.
"""
    cfg = ComponentAccumulator()

    if applyUpDownstreamCorrections is None:
        applyUpDownstreamCorrections = clusterFlags.applyUpDownstreamCorrections
    if addShapeParameters is None:
        addShapeParameters = clusterFlags.addShapeParameters
    if calibrateClusters is None:
        calibrateClusters = clusterFlags.calibrateClusters
    if runPhotonID is None:
         runPhotonID = clusterFlags.runPhotonID

    cells = []
    caloIDs = []
    for (k, v) in inputCells.items():
        cells.append(v)
        caloIDs.append(detIDs(flags, k))

    cfg.merge (creatorCfg (flags,
                           outputClusters,
                           cells,
                           caloIDs,
                           **creatorCfgArgs))
    clustersName = cfg.algs()[-1].clusters.Path
    outputSaveClusters.append (clustersName)

    keep = []
    if not addShapeParameters:
        keep.append (clustersName)
    if clusterFlags.saveClusterCells:
        keep.append (cfg.algs()[-1].clusterCells.Path)

    if applyUpDownstreamCorrections:
        # note that this only works for ecal barrel given various hardcoded quantities
        # to be generalized, pass more input parameters to function
        cfg.merge (CorrectCaloClustersCfg (flags,
                                           clustersName,
                                           outputClusters))

    augmentClusterAlg = None
    if addShapeParameters:
        detectors = None
        if (outputClusters.startswith ("EMBCaloClusters") or
            outputClusters.startswith ("EMBCaloTopoClusters")):
            detectors = ['ECAL_Barrel']
        elif (outputClusters.startswith ("EMECCaloClusters") or
              outputClusters.startswith ("EMECCaloTopoClusters")):
            detectors = ['ECAL_Endcap']
        elif (outputClusters.startswith ("CaloClusters") or
              outputClusters.startswith ("CaloTopoClusters")):
            # temporary to demonstrate possibility of doing an MVA calibration of pions reconstructed by ECAL+HCAL
            detectors = ['ECAL_Barrel', 'HCAL_Barrel']

        if detectors:
            cfg.merge (AugmentCaloClustersCfg (flags,
                                               clusterFlags,
                                               detectors,
                                               clustersName,
                                               outputClusters))
            clustersName = cfg.algs()[-1].outClusters.Path
            augmentClusterAlg = cfg.algs()[-1]

            # since the non-decorated version of the clusters will be dropped,
            # we update the list of clusters for which we store the truth links
            outputSaveClusters[-1] = clustersName

            # tool to identify resolved pi0->two photon cluster candidates
            # see: https://indico.cern.ch/event/1483299/contributions/6488594/attachments/3056315/5403634/ALLEGRO_photon_pi0_20250424.pdf
            if clusterFlags.reconstructPi0s:
                cfg.merge(PairCaloClustersPi0Cfg(flags, clustersName, outputClusters))
                keep += [f'Unpaired{clustersName}',
                         f'Paired{clustersName}',
                         f'ResolvedPi0Particle{outputClusters}',
                         ]
    keep.append (clustersName)

    if calibrateClusters:
        # note that this only works for ecal barrel given various
        # hardcoded quantities
        cfg.merge (CalibrateCaloClustersCfg (flags, clusterFlags, clustersName, outputClusters))
        clustersName = cfg.algs()[-1].outClusters.Path
        keep.append (clustersName)

    if runPhotonID and augmentClusterAlg is not None:
        cfg.merge (CaloPhotonIDCfg (flags, clustersName, outputClusters,
                                    clusterFlags.photonIDModelNameRoot))
        clustersName = cfg.algs()[-1].outClusters.Path
        keep.append (clustersName)

    if keep:
        from FCC_config.CoreConfig import IOSvcCfg
        cfg.merge(IOSvcCfg(flags, keep=keep))
    return cfg



def CaloSWClusterCfg (flags,
                      inputCells,
                      outputClusters,
                      threshold,
                      clusterType,
                      outputSaveClusters,
                      **kw):
    """Return a CA to run sliding window calorimeter clustering.

This set up a chain of algorithms to run cluster finding.
See CaloClusterCfg for details.

flags: Configuration flags.
inputCells: List of input cell collections to use.
  Should be a map from detector name (such as ECAL_Barrel) to cell
  collection name.
outputClusters: Root name for the clusters we produce.
  Should start with one of EMBCaloClusters, EMECCaloClusters,
  CaloClusters.
threshold: Et cut for cluster finding.
clusterType: One of ReducedSize, MuonSize, StandardSize.

Other arguments are passed gthrough to CaloClusterCfg.
"""
    return CaloClusterCfg (flags, flags.CaloSW,
                           inputCells, outputClusters, outputSaveClusters,
                           CreateCaloSWClustersCfg,
                           {'threshold' : threshold,
                            'clusterType' : clusterType},
                           **kw)


def CaloTopoClusterCfg (flags,
                        inputCells,
                        outputClusters,
                        threshold,
                        outputSaveClusters,
                        **kw):
    """Return a CA to run topological calorimeter clustering.

This set up a chain of algorithms to run cluster finding.
See CaloClusterCfg for details.

flags: Configuration flags.
inputCells: List of input cell collections to use.
  Should be a map from detector name (such as ECAL_Barrel) to cell
  collection name.
outputClusters: Root name for the clusters we produce.
  Should start with one of EMBCaloClusters, EMECCaloClusters,
  CaloClusters.
threshold: Et cut for cluster finding.

Other arguments are passed gthrough to CaloClusterCfg.
"""
    return CaloClusterCfg (flags, flags.CaloTopo,
                           inputCells, outputClusters, outputSaveClusters,
                           CreateCaloTopoClustersCfg,
                           {'threshold' : threshold},
                           **kw)


class Flags:
    pass
class ClusterFlags:
    """Clustering flags common between SW and topo clusters"""

    def __init__ (self,
                  createClusterCellCollections = True,
                  calibrateClusters = False,
                  runPhotonID = False):

        # create new collection with clustered cells or just link from cluster
        # to original input cell collections
        self.createClusterCellCollections = createClusterCellCollections

        # calculate cluster energy and barycenter per layer and save it
        # as extra parameters
        self.addShapeParameters = True

        # BDT regression from total cluster energy and fraction of energy
        # in each layer (after correction for sampling fraction)
        # not to be applied (yet) for ECAL+HCAL clustering (MVA trained
        # only on ECAL so far)
        self.calibrateClusters = calibrateClusters

        # run photon ID algorithm
        # not run by default in production, but to be turned on here for the purpose of testing that the code is not broken
        # currently off till we provide the onnx files
        #self.runPhotonID = False
        self.runPhotonID = runPhotonID

        self.logEWeightInPhotonID = False

        # resolved pi0 reconstruction by cluster pairing
        self.reconstructPi0s = False

        # cluster energy corrections
        # simple parametrisations of up/downstream losses for ECAL-only clusters
        # not to be applied for ECAL+HCAL clustering
        # superseded by MVA calibration, but can be turned on here for the
        # purpose of testing that the code is not broken - will end up in
        # separate cluster collection
        self.applyUpDownstreamCorrections = False

        self.saveClusterCells = True

        return
def defineCaloClusterFlags(flags = None,
                           reconstructPi0s = True,
                           **kw):
    """Define configuration flags for calorimeter cluster reconstruction.

If a top-level flags object is given as the first argument,
flags will be added to it.  Otherwise, a new top-level flags
object will be created.  In any case, the top-level flags
are returned.

Additional options:

calibrateClusters: Apply MVA calibration to clusters
createClusterCellCollections: create new collection with clustered cells
   or just link from cluster to original input cell collections
reconstructPi0s: Search for cluster pairs consistent with the pi0 hypothesis
  (topo clusters only)
runPhotonID: Apply photon ID tool to clusters
"""
    # Create top-level object if not provided.
    if flags is None:
        flags = Flags()

    # Sliding window cluster flags.
    flags.CaloSW = ClusterFlags(**kw)
    flags.CaloSW.calibrationFile = 'lgbm_calibration-CaloClusters.onnx'
    flags.CaloSW.photonIDModelNameRoot = 'EMBCaloClusters'

    # Topological cluster flags.
    flags.CaloTopo = ClusterFlags(**kw)
    flags.CaloTopo.calibrationFile = 'lgbm_calibration-CaloTopoClusters.onnx'
    flags.CaloTopo.photonIDModelNameRoot = 'EMBCaloTopoClusters'

    # Pi0 reconstruction for topo clusters only.
    flags.CaloTopo.reconstructPi0s = reconstructPi0s

    # Neighbour files.
    flags.CaloTopo.EMBNeighbours = 'neighbours_map_ecalB_thetamodulemerged'
    flags.CaloTopo.EMECNeighbours = 'neighbours_map_ecalE_turbine'
    # note: links ecal and hcal barrels, and hcal barrel-endcap, but does not link (yet) the others
    flags.CaloTopo.AllNeighbours = 'neighbours_map_ecalB_thetamodulemerged_ecalE_turbine_hcalB_hcalEndcap_phitheta'

    # Cluster noise maps.
    flags.CaloTopo.EMBNoise = 'cellNoise_map_electronicsNoiseLevel_ecalB_thetamodulemerged'
    flags.CaloTopo.EMECNoise = 'cellNoise_map_endcapTurbine_electronicsNoiseLevel'
    flags.CaloTopo.AllNoise = 'cellNoise_map_electronicsNoiseLevel_ecalB_ECalBarrelModuleThetaMerged_ecalE_ECalEndcapTurbine_hcalB_HCalBarrelReadout_hcalE_HCalEndcapReadout'

    # Clustering parameters
    flags.CaloTopo.seedSigma = 6
    flags.CaloTopo.neighbourSigma = 2
    flags.CaloTopo.lastNeighbourSigma = 0

    # pi0 --- values determined from a dedicated study
    flags.CaloTopo.pi0MassPeak = 0.122201
    flags.CaloTopo.pi0MassLow  = 0.0754493
    flags.CaloTopo.pi0MassHigh = 0.153543

    return flags

    
