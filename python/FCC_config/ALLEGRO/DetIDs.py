import xml.etree.ElementTree as ET
import os

_allDicts = {}

def _makeIdDict (flags):
    xmlfile = os.path.join (flags.pathToDetector, 'DectDimensions.xml')
    tree = ET.parse (xmlfile)
    root = tree.getroot()
    d = {}
    for constant in root.find('define').findall('constant'):
        name = constant.get('name')
        if name.startswith('DetID'):
            val = int(constant.get('value'))
            d[name[6:]] = val
            if name == 'DetID_Muon_Endcap_1':
                d[name[6:-2]] = val
    return d
                

def _detIdDict (flags):
    compactFile = flags.compactFile
    if compactFile not in _allDicts:
        _allDicts[compactFile] = _makeIdDict (flags)
    return _allDicts[compactFile]


def detIDs (flags, ids):
    d = _detIdDict (flags)
    if isinstance(ids, list):
        return [d[x] for x in ids]
    return d[ids]
