from FCC_config.ComponentAccumulator import ComponentAccumulator
import Configurables as C
from math import pi
from FCC_config.ALLEGRO.DetIDs import detIDs


############################################################################
# Parameters
#

# ECAL barrel parameters for digitisation
from .CreateCaloCells import ecalBarrelLayers

# to be recalculated for V03, separately for topo and calo clusters...
ecalBarrelThetaWeights = [-1, 3.0, 3.0, 3.0, 4.25, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0]


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
    return C.CaloTowerToolFCCee(name,
                                deltaThetaTower=4 * 0.009817477 / 4,
                                deltaPhiTower=2 * 2 * pi / 1536.,
                                thetaMin=0.0, thetaMax=pi,
                                phiMin=-pi, phiMax=pi,
                                cells=cells,
                                calorimeterIDs=caloIDs,
                                nSubDetectors=3)


def CreateCaloSWClustersCfg (flags,
                             clusterNameRoot,
                             cells,
                             caloIDs,
                             threshold,
                             clusterType,
                             **kw):
    cfg = ComponentAccumulator()

    towerTool = CaloTowerTool(flags,
                              clusterNameRoot + "TowerTool",
                              cells,
                              caloIDs)

    kw.update (swClustertypes[clusterType])
    alg = C.CreateCaloClustersSlidingWindowFCCee("Create" + clusterNameRoot,
                                                 towerTool=towerTool,
                                                 energyThreshold=threshold,
                                                 energySharingCorrection=False,
                                                 createClusterCellCollection=flags.CaloSW.createClusterCellCollection,
                                                 clusters = clusterNameRoot,
                                                 clusterCells = clusterNameRoot.replace('Clusters', 'Cluster') + 'Cells',
                                                 **kw
                                                 )
    cfg.addAlg(alg)
    return cfg


############################################################################
# Topo cluster creation.
#


def CaloTopoNeighboursTool (flags, clusterNameRoot, caloIDs):
    if caloIDs == ['ECAL_Barrel']:
        neighboursMap = flags.CaloTopo.EMBNeighbours
    elif caloIDs == ['ECAL_Endcap']:
        neighboursMap = flags.CaloTopo.EMECNeighbours
    else:
        neighboursMap = flags.CaloTopo.AllNeighbours
    return C.TopoCaloNeighbours(clusterNameRoot + 'NeighboursMap',
                                fileName = flags.dataFiles + neighboursMap + '.root')


def CaloTopoNoiseTool (flags, clusterNameRoot, caloIDs):
    if caloIDs == ['ECAL_Barrel']:
        noiseMap = flags.CaloTopo.EMBNoise
    elif caloIDs == ['ECAL_Endcap']:
        noiseMap = flags.CaloTopo.EMECNoise
    else:
        noiseMap = flags.CaloTopo.AllNoise
    return C.TopoCaloNoisyCells(clusterNameRoot + 'NoiseMap',
                                fileName = flags.dataFiles + noiseMap + '.root')



def CreateCaloTopoClustersCfg (flags,
                               clusterNameRoot,
                               cells,
                               caloIDs,
                               threshold):
    cfg = ComponentAccumulator()
    alg = C.CaloTopoClusterFCCee('Create' + clusterNameRoot,
                                 cells=cells,
                                 clusters=clusterNameRoot,
                                 clusterCells=clusterNameRoot.replace("Clusters", "Cluster") + "Cells",
                                 neigboursTool = CaloTopoNeighboursTool(flags,
                                                                        clusterNameRoot,
                                                                        caloIDs),
                                 noiseTool = CaloTopoNoiseTool(flags,
                                                               clusterNameRoot,
                                                               caloIDs),
                                 seedSigma = flags.CaloTopo.seedSigma,
                                 neighbourSigma = flags.CaloTopo.neighbourSigma,
                                 lastNeighbourSigma = flags.CaloTopo.lastNeighbourSigma,
                                 minClusterEnergy = threshold,
                                 calorimeterIDs = caloIDs,
                                 createClusterCellCollection = flags.CaloTopo.createClusterCellCollection)

    cfg.addAlg(alg)
    return cfg



def PairCaloClustersPi0Cfg (flags, inputClusters, clusterNameRoot):
    cfg = ComponentAccumulator()
    alg = C.PairCaloClustersPi0('resolvedPi0FromClusterPair' + clusterNameRoot,
                                inClusters = inputClusters,
                                unpairedClusters = 'Unpaired' + inputClusters,
                                pairedClusters  = 'pairedClusters' + inputClusters,
                                reconstructedPi0 = 'ResolvedPi0Particle' + clusterNameRoot,
                                massPeak = flags.CaloTopo.pi0MassPeak,
                                massLow  = flags.CaloTopo.pi0MassLow,
                                massHigh = flags.CaloTopo.pi0MassHigh)
    cfg.addAlg(alg)
    return cfg
    

############################################################################
# Common algorithms.
#

def AugmentCaloClustersCfg (flags, clusterFlags, inputClusters, clusterNameRoot):
    cfg = ComponentAccumulator()
    # note that this only works for ecal barrel given various hardcoded quantities
    alg = C.AugmentClustersFCCee('Augment' + clusterNameRoot,
                                 inClusters=inputClusters,
                                 outClusters='Augmented' + clusterNameRoot,
                                 systemIDs=[detIDs(flags, "ECAL_Barrel")],
                                 systemNames=["EMB"],
                                 numLayers=[ecalBarrelLayers],
                                 readoutNames=[flags.ECal.Barrel.readoutName],
                                 layerFieldNames=["layer"],
                                 thetaRecalcWeights=[ecalBarrelThetaWeights],
                                 do_photon_shapeVar=True,  # we want these variables to train the photon ID BDT
                                 do_widthTheta_logE_weights=clusterFlags.logEWeightInPhotonID,
                                 )
    
    cfg.addAlg(alg)
    return cfg


def CalibrateCaloClustersCfg (flags, clusterFlags, inputClusters, clusterNameRoot):
    cfg = ComponentAccumulator()

    # note that this only works for ecal barrel given various
    # hardcoded quantities
    alg = C.CalibrateCaloClusters('Calibrate' + clusterNameRoot,
                                  inClusters = inputClusters,
                                  outClusters = 'Calibrated' + clusterNameRoot,
                                  systemIDs = [detIDs(flags, 'ECAL_Barrel')],
                                  systemNames = ['EMB'],
                                  numLayers = [ecalBarrelLayers],
                                  firstLayerIDs = [0],
                                  readoutNames = [flags.ECal.Barrel.readoutName],
                                  layerFieldNames = ['layer'],
                                  calibrationFile = flags.dataFiles + clusterFlags.calibrationFile,
                                  )
    cfg.addAlg(alg)
    return cfg



def CaloPhotonIDCfg (flags, inputClusters, clusterNameRoot, modelNameRoot):
    cfg = ComponentAccumulator()
    alg = C.PhotonIDTool("PhotonID" + clusterNameRoot,
                         inClusters=inputClusters,
                         outClusters="PhotonID" + inputClusters,
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
                    clusterNameRoot,
                    outputSaveClusters,
                    creatorCfg,
                    creatorCfgArgs,
                    io_svc,
                    applyMVAClusterEnergyCalibration = None,
                    addShapeParameters = None,
                    doPhotonID = None):
    cfg = ComponentAccumulator()

    if applyMVAClusterEnergyCalibration is None:
        applyMVAClusterEnergyCalibration = clusterFlags.applyMVAClusterEnergyCalibration
    if addShapeParameters is None:
        addShapeParameters = clusterFlags.addShapeParameters
    if doPhotonID is None:
        doPhotonID = clusterFlags.doPhotonID

    cells = []
    caloIDs = []
    for (k, v) in inputCells.items():
        cells.append(v)
        caloIDs.append(detIDs(flags, k))

    cfg.merge (creatorCfg (flags,
                           clusterNameRoot,
                           cells,
                           caloIDs,
                           **creatorCfgArgs))
    clustersName = cfg.algs()[-1].clusters.Path
    outputSaveClusters.append (clustersName)

    if not addShapeParameters:
        io_svc.outputCommands += [f'keep {clustersName}']
    if clusterFlags.saveClusterCells:
        io_svc.outputCommands += [f'keep {cfg.algs()[-1].clusterCells.Path}']

    if addShapeParameters and 'ECAL_Barrel' in inputCells:
        # note that this only works for ecal barrel given various hardcoded quantities
        cfg.merge (AugmentCaloClustersCfg (flags, clusterFlags, clustersName, clusterNameRoot))
        clustersName = cfg.algs()[-1].outClusters.Path
        # since the non-decorated version of the clusters will be dropped,
        # we update the list of clusters for which we store the truth links
        outputSaveClusters[-1] = clustersName

        # tool to identify resolved pi0->two photon cluster candidates
        # see: https://indico.cern.ch/event/1483299/contributions/6488594/attachments/3056315/5403634/ALLEGRO_photon_pi0_20250424.pdf
        if clusterFlags.addPi0RecoTool:
            from FCC_config.ALLEGRO.CreateCaloClusters import PairCaloClustersPi0Cfg
            cfg.merge(PairCaloClustersPi0Cfg(flags, clustersName, clusterNameRoot))
            io_svc.outputCommands += [f'keep Unpaired{clustersName}',
                                      f'keep pairedClusters{clustersName}',
                                      f'keep ResolvedPi0Particle{clusterNameRoot}',
                                      ]
    io_svc.outputCommands += [f'keep {clustersName}']

    if applyMVAClusterEnergyCalibration  and 'ECAL_Barrel' in inputCells:
        # note that this only works for ecal barrel given various
        # hardcoded quantities
        cfg.merge (CalibrateCaloClustersCfg (flags, clusterFlags, clustersName, clusterNameRoot))
        clustersName = cfg.algs()[-1].outClusters.Path
        io_svc.outputCommands += [f'keep {clustersName}']

    if (doPhotonID and addShapeParameters and 'ECAL_Barrel' in inputCells):
        cfg.merge (CaloPhotonIDCfg (flags, clustersName, clusterNameRoot,
                                    clusterFlags.photonIDModelNameRoot))
        clustersName = cfg.algs()[-1].outClusters.Path
        io_svc.outputCommands += [f'keep {clustersName}']

    return cfg



def CaloSWClusterCfg (flags,
                      inputCells,
                      clusterNameRoot,
                      threshold,
                      clusterType,
                      outputSaveClusters,
                      io_svc,
                      **kw):

    return CaloClusterCfg (flags, flags.CaloSW,
                           inputCells, clusterNameRoot, outputSaveClusters,
                           CreateCaloSWClustersCfg,
                           {'threshold' : threshold,
                            'clusterType' : clusterType},
                           io_svc,
                           **kw)



def CaloTopoClusterCfg (flags,
                        inputCells,
                        clusterNameRoot,
                        threshold,
                        outputSaveClusters,
                        io_svc,
                        **kw):
    return CaloClusterCfg (flags, flags.CaloTopo,
                           inputCells, clusterNameRoot, outputSaveClusters,
                           CreateCaloTopoClustersCfg,
                           {'threshold' : threshold},
                           io_svc,
                           **kw)


class ClusterFlags:
    def __init__ (self,
                  calibrateClusters,
                  doPhotonID):
        # create new collection with clustered cells or just link from cluster
        # to original input cell collections
        self.createClusterCellCollection = True

        # calculate cluster energy and barycenter per layer and save it
        # as extra parameters
        self.addShapeParameters = True

        # BDT regression from total cluster energy and fraction of energy
        # in each layer (after correction for sampling fraction)
        # not to be applied (yet) for ECAL+HCAL clustering (MVA trained
        # only on ECAL so far)
        self.applyMVAClusterEnergyCalibration = calibrateClusters

        # run photon ID algorithm
        self.doPhotonID = doPhotonID

        self.logEWeightInPhotonID = False

        # resolved pi0 reconstruction by cluster pairing
        self.addPi0RecoTool = False

        self.saveClusterCells = True

        return
def defineCaloClusterFlags(flags,
                           calibrateClusters,
                           doPhotonID):
    flags.CaloSW = ClusterFlags(calibrateClusters,
                                doPhotonID)
    flags.CaloSW.calibrationFile = 'lgbm_calibration-CaloClusters.onnx'
    flags.CaloSW.photonIDModelNameRoot = 'EMBCaloClusters'

    flags.CaloTopo = ClusterFlags(calibrateClusters,
                                  doPhotonID)
    flags.CaloTopo.addPi0RecoTool = True
    flags.CaloTopo.photonIDModelNameRoot = 'EMBCaloTopoClusters'

    flags.CaloTopo.EMBNeighbours = 'neighbours_map_ecalB_thetamodulemerged'
    flags.CaloTopo.EMECNeighbours = 'neighbours_map_ecalE_turbine'
    # note: links ecal and hcal barrels, and hcal barrel-endcap, but does not link (yet) the others
    flags.CaloTopo.AllNeighbours = 'neighbours_map_ecalB_thetamodulemerged_ecalE_turbine_hcalB_hcalEndcap_phitheta'

    flags.CaloTopo.EMBNoise = 'cellNoise_map_electronicsNoiseLevel_ecalB_thetamodulemerged'
    flags.CaloTopo.EMECNoise = 'cellNoise_map_endcapTurbine_electronicsNoiseLevel'
    flags.CaloTopo.AllNoise = 'cellNoise_map_electronicsNoiseLevel_ecalB_ECalBarrelModuleThetaMerged_ecalE_ECalEndcapTurbine_hcalB_HCalBarrelReadout_hcalE_HCalEndcapReadout'
    flags.CaloTopo.calibrationFile = 'lgbm_calibration-CaloTopoClusters.onnx'

    # Clustering parameters
    flags.CaloTopo.seedSigma = 6
    flags.CaloTopo.neighbourSigma = 2
    flags.CaloTopo.lastNeighbourSigma = 0

    # pi0 --- values determined from a dedicated study
    flags.CaloTopo.pi0MassPeak = 0.122201
    flags.CaloTopo.pi0MassLow  = 0.0754493
    flags.CaloTopo.pi0MassHigh = 0.153543

    return

    
