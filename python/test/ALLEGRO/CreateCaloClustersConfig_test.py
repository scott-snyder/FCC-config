#!/usr/bin/env python
#
# File: python/test/ALLEGRO/CreateCaloClustersConfig_test.py
# Author: scott snyder <snyder@bnl.gov>
# Date: Jun, 2026
# Purpose: Unit tests for ALLEGRO CreateCaloClustersConfig 
#

import unittest
import os
from FCC_config.ALLEGRO import CreateCaloClustersConfig
from FCC_config.DetIDs import detIDs


compactFile = os.environ.get("K4GEO", "") + "/FCCee/ALLEGRO/compact/ALLEGRO_o1_v03/ALLEGRO_o1_v03.xml"


class Flags:
    pass

class TestCreateCaloClustersConfig (unittest.TestCase):
    def test_ClusterFlags (self):
        flags1 = CreateCaloClustersConfig.ClusterFlags()
        self.assertEqual (flags1.createClusterCellCollections, True)
        self.assertEqual (flags1.addShapeParameters, True)
        self.assertEqual (flags1.calibrateClusters, False)
        self.assertEqual (flags1.runPhotonID, False)
        self.assertEqual (flags1.logEWeightInPhotonID, False)
        self.assertEqual (flags1.reconstructPi0s, False)
        self.assertEqual (flags1.applyUpDownstreamCorrections, False)

        flags2 = CreateCaloClustersConfig.ClusterFlags(createClusterCellCollections = False,
                                                       calibrateClusters = True,
                                                       runPhotonID = True)
        self.assertEqual (flags2.createClusterCellCollections, False)
        self.assertEqual (flags2.addShapeParameters, True)
        self.assertEqual (flags2.calibrateClusters, True)
        self.assertEqual (flags2.runPhotonID, True)
        self.assertEqual (flags2.logEWeightInPhotonID, False)
        self.assertEqual (flags2.reconstructPi0s, False)
        return


    def test_defineCaloClusterFlags1 (self):
        flags = CreateCaloClustersConfig.defineCaloClusterFlags()
        self.assertEqual (flags.CaloSW.calibrateClusters, False)
        self.assertEqual (flags.CaloSW.reconstructPi0s, False)
        self.assertEqual (flags.CaloSW.photonIDModelNameRoot, 'EMBCaloClusters')

        self.assertEqual (flags.CaloTopo.calibrateClusters, False)
        self.assertEqual (flags.CaloTopo.reconstructPi0s, True)
        self.assertEqual (flags.CaloTopo.photonIDModelNameRoot, 'EMBCaloTopoClusters')
        self.assertEqual (flags.CaloTopo.seedSigma, 6)

        flags2  = Flags()
        CreateCaloClustersConfig.defineCaloClusterFlags(flags2,
                                                        calibrateClusters = True,
                                                        reconstructPi0s = False)
        self.assertEqual (flags2.CaloSW.calibrateClusters, True)
        self.assertEqual (flags2.CaloSW.reconstructPi0s, False)
        self.assertEqual (flags2.CaloSW.photonIDModelNameRoot, 'EMBCaloClusters')

        self.assertEqual (flags2.CaloTopo.calibrateClusters, True)
        self.assertEqual (flags2.CaloTopo.reconstructPi0s, False)
        self.assertEqual (flags2.CaloTopo.photonIDModelNameRoot, 'EMBCaloTopoClusters')
        self.assertEqual (flags2.CaloTopo.seedSigma, 6)

        return


    def test_CaloTowerTool(self):
        flags = CreateCaloClustersConfig.defineCaloClusterFlags()
        tool = CreateCaloClustersConfig.CaloTowerTool (flags, 'atool', ['cells1', 'cells2'], [2, 3])
        self.assertEqual (tool.getFullName(), 'CaloTowerToolFCCee/atool')
        self.assertEqual (tool.cells, ['cells1', 'cells2'])
        self.assertEqual (tool.calorimeterIDs, [2, 3])
        return
        

    def test_CreateCaloSWClustersCfg (self):
        flags = CreateCaloClustersConfig.defineCaloClusterFlags()
        flags.compactFile = compactFile
        flags.dataFiles = 'data/'
        ca1 = CreateCaloClustersConfig.CreateCaloSWClustersCfg (flags,
                                                                'clust1',
                                                                ['cells'],
                                                                detIDs(flags, ['ECAL_Barrel']),
                                                                1.5,
                                                                'StandardSize')
        assert len(ca1.svcs()) == 0
        assert len(ca1.algs()) == 1
        alg1 = ca1.algs()[0]
        self.assertEqual (alg1.getFullName(), 'CreateCaloClustersSlidingWindowFCCee/Createclust1')
        self.assertEqual (alg1.towerTool.getFullName(), 'CaloTowerToolFCCee/clust1TowerTool')
        self.assertEqual (alg1.energyThreshold, 1.5)
        self.assertEqual (alg1.clusters.Path, 'clust1')
        self.assertEqual (alg1.clusterCells.Path, 'clust1Cells')
        self.assertEqual (alg1.nThetaWindow, 9)
        return


    def test_CaloTopoNeighboursTool(self):
        flags = CreateCaloClustersConfig.defineCaloClusterFlags()
        flags.compactFile = compactFile
        flags.dataFiles = 'data/'
        tool1 = CreateCaloClustersConfig.CaloTopoNeighboursTool (
            flags, 'tool1', detIDs(flags, ['ECAL_Barrel']))
        self.assertEqual (tool1.getFullName(), 'TopoCaloNeighbours/tool1NeighboursMap')
        self.assertEqual (tool1.fileName, 'data/neighbours_map_ecalB_thetamodulemerged.root')

        tool2 = CreateCaloClustersConfig.CaloTopoNeighboursTool (
            flags, 'tool2', detIDs(flags, ['ECAL_Endcap']))
        self.assertEqual (tool2.getFullName(), 'TopoCaloNeighbours/tool2NeighboursMap')
        self.assertEqual (tool2.fileName, 'data/neighbours_map_ecalE_turbine.root')

        tool3 = CreateCaloClustersConfig.CaloTopoNeighboursTool (
            flags, 'tool3', detIDs(flags, ['ECAL_Barrel', 'ECAL_Endcap',
                                           'HCAL_Barrel', 'HCAL_Endcap']))
        self.assertEqual (tool3.getFullName(), 'TopoCaloNeighbours/tool3NeighboursMap')
        self.assertEqual (tool3.fileName, 'data/neighbours_map_ecalB_thetamodulemerged_ecalE_turbine_hcalB_hcalEndcap_phitheta.root')

        return


    def test_CaloTopoNoiseTool(self):
        flags = CreateCaloClustersConfig.defineCaloClusterFlags()
        flags.compactFile = compactFile
        flags.dataFiles = 'data/'
        tool1 = CreateCaloClustersConfig.CaloTopoNoiseTool (
            flags, 'tool1', detIDs(flags, ['ECAL_Barrel']))
        self.assertEqual (tool1.getFullName(), 'TopoCaloNoisyCells/tool1NoiseMap')
        self.assertEqual (tool1.fileName, 'data/cellNoise_map_electronicsNoiseLevel_ecalB_thetamodulemerged.root')

        tool2 = CreateCaloClustersConfig.CaloTopoNoiseTool (
            flags, 'tool2', detIDs(flags, ['ECAL_Endcap']))
        self.assertEqual (tool2.getFullName(), 'TopoCaloNoisyCells/tool2NoiseMap')
        self.assertEqual (tool2.fileName, 'data/cellNoise_map_endcapTurbine_electronicsNoiseLevel.root')

        tool3 = CreateCaloClustersConfig.CaloTopoNoiseTool (
            flags, 'tool3', detIDs(flags, ['ECAL_Barrel', 'ECAL_Endcap',
                                           'HCAL_Barrel', 'HCAL_Endcap']))
        self.assertEqual (tool3.getFullName(), 'TopoCaloNoisyCells/tool3NoiseMap')
        self.assertEqual (tool3.fileName, 'data/cellNoise_map_electronicsNoiseLevel_ecalB_ECalBarrelModuleThetaMerged_ecalE_ECalEndcapTurbine_hcalB_HCalBarrelReadout_hcalE_HCalEndcapReadout.root')

        return


    def test_CreateCaloTopoClustersCfg (self):
        flags = CreateCaloClustersConfig.defineCaloClusterFlags()
        flags.compactFile = compactFile
        flags.dataFiles = 'data/'
        ca1 = CreateCaloClustersConfig.CreateCaloTopoClustersCfg (flags,
                                                                  'clust2',
                                                                  ['cells'],
                                                                  detIDs(flags, ['ECAL_Barrel']),
                                                                  1.5)
        assert len(ca1.svcs()) == 0
        assert len(ca1.algs()) == 1
        alg1 = ca1.algs()[0]
        self.assertEqual (alg1.getFullName(), 'CaloTopoClusterFCCee/Createclust2')
        self.assertEqual (alg1.neigboursTool.getFullName(), 'TopoCaloNeighbours/clust2NeighboursMap')
        self.assertEqual (alg1.noiseTool.getFullName(), 'TopoCaloNoisyCells/clust2NoiseMap')
        self.assertEqual (alg1.minClusterEnergy, 1.5)
        self.assertEqual (alg1.clusters.Path, 'clust2')
        self.assertEqual (alg1.clusterCells.Path, 'clust2Cells')
        return


    def test_PairCaloClustersPi0Cfg (self):
        flags = CreateCaloClustersConfig.defineCaloClusterFlags()
        flags.compactFile = compactFile
        flags.dataFiles = 'data/'
        ca = CreateCaloClustersConfig.PairCaloClustersPi0Cfg (flags,
                                                              'clust1',
                                                              'clust2')
        assert len(ca.svcs()) == 0
        assert len(ca.algs()) == 1
        alg = ca.algs()[0]
        self.assertEqual (alg.getFullName(), 'PairCaloClustersPi0/resolvedPi0FromClusterPairclust2')
        self.assertEqual (alg.inClusters.Path, 'clust1')
        self.assertEqual (alg.unpairedClusters.Path, 'Unpairedclust1')
        self.assertEqual (alg.pairedClusters.Path, 'Pairedclust1')
        self.assertEqual (alg.reconstructedPi0.Path, 'ResolvedPi0Particleclust2')
        return


    def test_CorrectCaloClustersCfg (self):
        flags = CreateCaloClustersConfig.defineCaloClusterFlags()
        flags.compactFile = compactFile
        flags.dataFiles = 'data/'
        from FCC_config.ALLEGRO.CreateCaloCellsConfig import defineCaloCellFlags
        defineCaloCellFlags(flags)
        ca = CreateCaloClustersConfig.CorrectCaloClustersCfg (flags,
                                                              'clust1',
                                                              'clust2')
        assert len(ca.svcs()) == 0
        assert len(ca.algs()) == 1
        alg = ca.algs()[0]
        self.assertEqual (alg.getFullName(), 'CorrectCaloClusters/Correctclust2')
        self.assertEqual (alg.inClusters.Path, 'clust1')
        self.assertEqual (alg.outClusters.Path, 'Correctedclust2')
        self.assertEqual (alg.numLayers, [11])
        return


    def test_AugmentCaloClustersCfg (self):
        flags = CreateCaloClustersConfig.defineCaloClusterFlags()
        flags.compactFile = compactFile
        flags.dataFiles = 'data/'
        from FCC_config.ALLEGRO.CreateCaloCellsConfig import defineCaloCellFlags
        defineCaloCellFlags(flags)

        ca1 = CreateCaloClustersConfig.AugmentCaloClustersCfg (flags,
                                                               flags.CaloSW,
                                                               ['ECAL_Barrel'],
                                                               'clust1a',
                                                               'clust1b')
        assert len(ca1.svcs()) == 0
        assert len(ca1.algs()) == 1
        alg1 = ca1.algs()[0]
        self.assertEqual (alg1.getFullName(), 'AugmentClustersFCCee/Augmentclust1b')
        self.assertEqual (alg1.inClusters.Path, 'clust1a')
        self.assertEqual (alg1.outClusters.Path, 'Augmentedclust1b')
        self.assertEqual (alg1.systemIDs, [4])
        self.assertEqual (alg1.systemNames, ['EMB'])
        self.assertEqual (alg1.numLayers, [11])
        self.assertEqual (alg1.readoutNames, ['ECalBarrelModuleThetaMerged'])
        self.assertEqual (alg1.layerFieldNames, ['layer'])
        self.assertEqual (alg1.do_photon_shapeVar, True)
        self.assertEqual (alg1.do_widthTheta_logE_weights, False)

        ca2 = CreateCaloClustersConfig.AugmentCaloClustersCfg (flags,
                                                               flags.CaloTopo,
                                                               ['ECAL_Endcap'],
                                                               'clust2a',
                                                               'clust2b')
        assert len(ca2.svcs()) == 0
        assert len(ca2.algs()) == 1
        alg2 = ca2.algs()[0]
        self.assertEqual (alg2.getFullName(), 'AugmentClustersFCCee/Augmentclust2b')
        self.assertEqual (alg2.inClusters.Path, 'clust2a')
        self.assertEqual (alg2.outClusters.Path, 'Augmentedclust2b')
        self.assertEqual (alg2.systemIDs, [5])
        self.assertEqual (alg2.systemNames, ['EMEC'])
        self.assertEqual (alg2.numLayers, [98])
        self.assertEqual (alg2.readoutNames, ['ECalEndcapTurbine'])
        self.assertEqual (alg2.layerFieldNames, ['layer'])
        self.assertEqual (alg2.do_photon_shapeVar, False)
        self.assertEqual (alg2.do_widthTheta_logE_weights, False)

        ca3 = CreateCaloClustersConfig.AugmentCaloClustersCfg (flags,
                                                               flags.CaloTopo,
                                                               ['ECAL_Barrel',
                                                                'HCAL_Barrel'],
                                                               'clust3a',
                                                               'clust3b')
        assert len(ca3.svcs()) == 0
        assert len(ca3.algs()) == 1
        alg3 = ca3.algs()[0]
        self.assertEqual (alg3.getFullName(), 'AugmentClustersFCCee/Augmentclust3b')
        self.assertEqual (alg3.inClusters.Path, 'clust3a')
        self.assertEqual (alg3.outClusters.Path, 'Augmentedclust3b')
        self.assertEqual (alg3.systemIDs, [4, 8])
        self.assertEqual (alg3.systemNames, ['EMB', 'HCALB'])
        self.assertEqual (alg3.numLayers, [11, 13])
        self.assertEqual (alg3.readoutNames, ['ECalBarrelModuleThetaMerged',
                                              'HCalBarrelReadout'])
        self.assertEqual (alg3.layerFieldNames, ['layer', 'layer'])
        self.assertEqual (alg3.do_photon_shapeVar, False)
        self.assertEqual (alg3.do_widthTheta_logE_weights, False)
        return


    def test_CalibrateCaloClustersCfg (self):
        flags = CreateCaloClustersConfig.defineCaloClusterFlags()
        from FCC_config.ALLEGRO.CreateCaloCellsConfig import defineCaloCellFlags
        defineCaloCellFlags(flags)
        flags.compactFile = compactFile
        flags.dataFiles = 'data/'
        ca1 = CreateCaloClustersConfig.CalibrateCaloClustersCfg (flags,
                                                                 flags.CaloSW,
                                                                 'clust1',
                                                                'clust2')
        assert len(ca1.svcs()) == 0
        assert len(ca1.algs()) == 1
        alg1 = ca1.algs()[0]
        self.assertEqual (alg1.getFullName(), 'CalibrateCaloClusters/Calibrateclust2')
        self.assertEqual (alg1.inClusters.Path, 'clust1')
        self.assertEqual (alg1.outClusters.Path, 'Calibratedclust2')
        self.assertEqual (alg1.systemNames, ['EMB'])
        self.assertEqual (alg1.numLayers, [11])
        self.assertEqual (alg1.calibrationFile, 'data/lgbm_calibration-CaloClusters.onnx')

        ca2 = CreateCaloClustersConfig.CalibrateCaloClustersCfg (flags,
                                                                 flags.CaloTopo,
                                                                 'clust3',
                                                                 'clust4')
        alg2 = ca2.algs()[0]
        self.assertEqual (alg2.getFullName(), 'CalibrateCaloClusters/Calibrateclust4')
        self.assertEqual (alg2.calibrationFile, 'data/lgbm_calibration-CaloTopoClusters.onnx')
        return


    def test_CaloPhotonIDCfg (self):
        flags = CreateCaloClustersConfig.defineCaloClusterFlags()
        flags.compactFile = compactFile
        flags.dataFiles = 'data/'
        ca = CreateCaloClustersConfig.CaloPhotonIDCfg (flags,
                                                       'clust1',
                                                       'clust2',
                                                       'model')
        assert len(ca.svcs()) == 0
        assert len(ca.algs()) == 1
        alg = ca.algs()[0]
        self.assertEqual (alg.getFullName(), 'PhotonIDTool/PhotonIDclust2')
        self.assertEqual (alg.inClusters.Path, 'clust1')
        self.assertEqual (alg.outClusters.Path, 'PhotonIDclust1')
        self.assertEqual (alg.mvaModelFile, 'data/bdt-photonid-weights-model.onnx')
        self.assertEqual (alg.mvaInputsFile, 'data/bdt-photonid-settings-model.json')
        return


    def test_CaloClusterCfg (self):
        flags = CreateCaloClustersConfig.defineCaloClusterFlags()
        flags.compactFile = compactFile
        flags.dataFiles = 'data/'
        from FCC_config.ALLEGRO.CreateCaloCellsConfig import defineCaloCellFlags
        defineCaloCellFlags(flags)

        osc1 = []
        ca1 = CreateCaloClustersConfig.CaloClusterCfg (flags,
                                                       flags.CaloSW,
                                                       {'ECAL_Barrel' : 'embcells'},
                                                       'EMBCaloClusters1',
                                                       osc1,
                                                       CreateCaloClustersConfig.CreateCaloSWClustersCfg,
                                                       {'threshold' : 0.1,
                                                        'clusterType' : 'StandardSize'},
                                                       calibrateClusters = True,
                                                       runPhotonID = True,
                                                       applyUpDownstreamCorrections = True,
                                                       )
        assert len(ca1.svcs()) == 0
        assert len(ca1.algs()) == 5
        self.assertEqual (osc1, ['AugmentedEMBCaloClusters1'])
        alg1a = ca1.algs()[0]
        self.assertEqual (alg1a.getFullName(), 'CreateCaloClustersSlidingWindowFCCee/CreateEMBCaloClusters1')
        self.assertEqual (alg1a.clusterCells.Path, 'EMBCaloCluster1Cells')
        self.assertEqual (alg1a.clusters.Path, 'EMBCaloClusters1')

        alg1b = ca1.algs()[1]
        self.assertEqual (alg1b.getFullName(), 'CorrectCaloClusters/CorrectEMBCaloClusters1')
        self.assertEqual (alg1b.inClusters.Path, 'EMBCaloClusters1')
        self.assertEqual (alg1b.outClusters.Path, 'CorrectedEMBCaloClusters1')
        self.assertEqual (alg1b.systemIDs, [4])

        alg1c = ca1.algs()[2]
        self.assertEqual (alg1c.getFullName(), 'AugmentClustersFCCee/AugmentEMBCaloClusters1')
        self.assertEqual (alg1c.inClusters.Path, 'EMBCaloClusters1')
        self.assertEqual (alg1c.outClusters.Path, 'AugmentedEMBCaloClusters1')
        self.assertEqual (alg1c.systemIDs, [4])

        alg1d = ca1.algs()[3]
        self.assertEqual (alg1d.getFullName(), 'CalibrateCaloClusters/CalibrateEMBCaloClusters1')
        self.assertEqual (alg1d.inClusters.Path, 'AugmentedEMBCaloClusters1')
        self.assertEqual (alg1d.outClusters.Path, 'CalibratedEMBCaloClusters1')
        self.assertEqual (alg1d.systemIDs, [4])

        alg1e = ca1.algs()[4]
        self.assertEqual (alg1e.getFullName(), 'PhotonIDTool/PhotonIDEMBCaloClusters1')
        self.assertEqual (alg1e.inClusters.Path, 'CalibratedEMBCaloClusters1')
        self.assertEqual (alg1e.outClusters.Path, 'PhotonIDCalibratedEMBCaloClusters1')

        osc2 = []
        ca2 = CreateCaloClustersConfig.CaloClusterCfg (flags,
                                                       flags.CaloTopo,
                                                       {'ECAL_Barrel' : 'embcells',
                                                        'HCAL_Barrel' : 'hcalbcells'},
                                                       'CaloTopoClusters2',
                                                       osc2,
                                                       CreateCaloClustersConfig.CreateCaloTopoClustersCfg,
                                                       {'threshold' : 0.1},
                                                       calibrateClusters = False,
                                                       runPhotonID = True,
                                                       )
        assert len(ca2.svcs()) == 0
        assert len(ca2.algs()) == 4
        self.assertEqual (osc2, ['AugmentedCaloTopoClusters2'])
        alg2a = ca2.algs()[0]
        self.assertEqual (alg2a.getFullName(), 'CaloTopoClusterFCCee/CreateCaloTopoClusters2')
        self.assertEqual (alg2a.clusterCells.Path, 'CaloTopoCluster2Cells')
        self.assertEqual (alg2a.clusters.Path, 'CaloTopoClusters2')

        alg2b = ca2.algs()[1]
        self.assertEqual (alg2b.getFullName(), 'AugmentClustersFCCee/AugmentCaloTopoClusters2')
        self.assertEqual (alg2b.inClusters.Path, 'CaloTopoClusters2')
        self.assertEqual (alg2b.outClusters.Path, 'AugmentedCaloTopoClusters2')
        self.assertEqual (alg2b.systemIDs, [4, 8])

        alg2c = ca2.algs()[2]
        self.assertEqual (alg2c.getFullName(), 'PairCaloClustersPi0/resolvedPi0FromClusterPairCaloTopoClusters2')
        self.assertEqual (alg2c.inClusters.Path, 'AugmentedCaloTopoClusters2')
        self.assertEqual (alg2c.reconstructedPi0.Path, 'ResolvedPi0ParticleCaloTopoClusters2')

        alg2d = ca2.algs()[3]
        self.assertEqual (alg2d.getFullName(), 'PhotonIDTool/PhotonIDCaloTopoClusters2')
        self.assertEqual (alg2d.inClusters.Path, 'AugmentedCaloTopoClusters2')
        self.assertEqual (alg2d.outClusters.Path, 'PhotonIDAugmentedCaloTopoClusters2')
        return


    def test_CaloSWClusterCfg (self):
        flags = CreateCaloClustersConfig.defineCaloClusterFlags()
        flags.compactFile = compactFile
        flags.dataFiles = 'data/'
        from FCC_config.ALLEGRO.CreateCaloCellsConfig import defineCaloCellFlags
        defineCaloCellFlags(flags)

        osc3 = []
        ca3 = CreateCaloClustersConfig.CaloSWClusterCfg (flags,
                                                         {'ECAL_Endcap' : 'emeccells'},
                                                         'EMECCaloClusters3',
                                                         2.5,
                                                         'ReducedSize',
                                                         osc3)
        assert len(ca3.svcs()) == 0
        assert len(ca3.algs()) == 2
        self.assertEqual (osc3, ['AugmentedEMECCaloClusters3'])
        alg3a = ca3.algs()[0]
        self.assertEqual (alg3a.getFullName(), 'CreateCaloClustersSlidingWindowFCCee/CreateEMECCaloClusters3')
        self.assertEqual (alg3a.clusterCells.Path, 'EMECCaloCluster3Cells')
        self.assertEqual (alg3a.clusters.Path, 'EMECCaloClusters3')

        alg3b = ca3.algs()[1]
        self.assertEqual (alg3b.getFullName(), 'AugmentClustersFCCee/AugmentEMECCaloClusters3')
        self.assertEqual (alg3b.inClusters.Path, 'EMECCaloClusters3')
        self.assertEqual (alg3b.outClusters.Path, 'AugmentedEMECCaloClusters3')
        self.assertEqual (alg3b.systemIDs, [5])
        return


    def test_CaloTopoClusterCfg (self):
        flags = CreateCaloClustersConfig.defineCaloClusterFlags()
        flags.compactFile = compactFile
        flags.dataFiles = 'data/'
        from FCC_config.ALLEGRO.CreateCaloCellsConfig import defineCaloCellFlags
        defineCaloCellFlags(flags)

        osc4 = []
        ca4 = CreateCaloClustersConfig.CaloTopoClusterCfg (flags,
                                                           {'ECAL_Endcap' : 'emeccells'},
                                                           'CaloTopoClusters4',
                                                           2.5,
                                                           osc4)
        assert len(ca4.svcs()) == 0
        assert len(ca4.algs()) == 3
        self.assertEqual (osc4, ['AugmentedCaloTopoClusters4'])
        alg4a = ca4.algs()[0]
        self.assertEqual (alg4a.getFullName(), 'CaloTopoClusterFCCee/CreateCaloTopoClusters4')
        self.assertEqual (alg4a.clusterCells.Path, 'CaloTopoCluster4Cells')
        self.assertEqual (alg4a.clusters.Path, 'CaloTopoClusters4')

        alg4b = ca4.algs()[1]
        self.assertEqual (alg4b.getFullName(), 'AugmentClustersFCCee/AugmentCaloTopoClusters4')
        self.assertEqual (alg4b.inClusters.Path, 'CaloTopoClusters4')
        self.assertEqual (alg4b.outClusters.Path, 'AugmentedCaloTopoClusters4')
        self.assertEqual (alg4b.systemIDs, [4, 8])

        alg4c = ca4.algs()[2]
        self.assertEqual (alg4c.getFullName(), 'PairCaloClustersPi0/resolvedPi0FromClusterPairCaloTopoClusters4')
        self.assertEqual (alg4c.inClusters.Path, 'AugmentedCaloTopoClusters4')
        self.assertEqual (alg4c.reconstructedPi0.Path, 'ResolvedPi0ParticleCaloTopoClusters4')
        return


if __name__ == '__main__':
    unittest.main()
