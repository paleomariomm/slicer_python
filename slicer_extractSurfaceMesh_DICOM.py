import os
from DICOMLib import DICOMUtils

yourpath = r"C:/Users/mario.modesto/Desktop/DICOM"
# yourpath = r"//clscidat.cenieh.local/TIED2-TEETH/AIM_1_QuantGen/Baboons/CT Scans/W101-W200"

# walk through DICOM directory
# https://stackoverflow.com/questions/77865010/run-python-script-in-each-subfolder-automatically
for dir in os.scandir(yourpath):
    # Load DICOM files
    dicomDataDir = dir.path  # path to input folder with DICOM files
    baboon_skull  = dir.name
    loadedNodeIDs = []  # this list will contain the list of all loaded node IDs

    # Load DICOM files
    # https://slicer.readthedocs.io/en/latest/developer_guide/script_repository.html#dicom
    with DICOMUtils.TemporaryDICOMDatabase() as db:
        DICOMUtils.importDicom(dicomDataDir, db)
        patientUIDs = db.patients()
        for patientUID in patientUIDs:
            loadedNodeIDs.extend(DICOMUtils.loadPatientByUID(patientUID))
    
    # load volume
    # https://slicer.readthedocs.io/en/latest/developer_guide/script_repository.html#display-volume-using-volume-rendering
    logic = slicer.modules.volumerendering.logic()
    volumeNode = slicer.mrmlScene.GetNodeByID('vtkMRMLScalarVolumeNode1')

    # Resample the volume
    # https://discourse.slicer.org/t/segment-a-resampled-volume/11938/4
    # parameters = {"outputPixelSpacing":"1,1,1", "InputVolume":volumeNode,"interpolationType":'bspline',"OutputVolume":volumeNode}
    # slicer.cli.runSync(slicer.modules.resamplescalarvolume, None, parameters)
 
    # Create segmentation
    # https://gist.github.com/lassoan/1673b25d8e7913cbc245b4f09ed853f9
    segmentationNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")
    segmentationNode.CreateDefaultDisplayNodes() # only needed for display
    segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(volumeNode)
    addedSegmentID = segmentationNode.GetSegmentation().AddEmptySegment(baboon_skull)
    
    # Create segment editor to get access to effects
    segmentEditorWidget = slicer.qMRMLSegmentEditorWidget()
    segmentEditorWidget.setMRMLScene(slicer.mrmlScene)
    segmentEditorNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentEditorNode")
    segmentEditorWidget.setMRMLSegmentEditorNode(segmentEditorNode)
    segmentEditorWidget.setSegmentationNode(segmentationNode) # (yourOutputSegmentation)
    segmentEditorWidget.setMasterVolumeNode(volumeNode)       # (yourVolume)
    
    # Segmentation: Thresholding
    segmentEditorWidget.setActiveEffectByName("Threshold")
    effect = segmentEditorWidget.activeEffect()
    effect.setParameter("MinimumThreshold","100")
    effect.setParameter("MaximumThreshold","3071")
    effect.self().onApply()

    # Segmentation: Systematically remove small islands
    # https://discourse.slicer.org/t/islands-segmentation-via-python-script/21021
    segmentEditorWidget.setActiveEffectByName("Islands")
    effect = segmentEditorWidget.activeEffect()
    effect.setParameter("MinimumSize","100000")
    effect.setParameter("Operation","REMOVE_SMALL_ISLANDS") #  KEEP_LARGEST_ISLAND
    effect.self().onApply()

    # Segmentation: Smoothing
    # https://discourse.slicer.org/t/how-to-use-segment-editor-effects-from-python-script/20815
    # segmentEditorWidget.setActiveEffectByName("Smoothing")
    # effect = segmentEditorWidget.activeEffect()
    # effect.setParameter("SmoothingMethod", "MEDIAN") #"CLOSING"
    # effect.setParameter("KernelSizeVx", 3)
    # effect.self().onApply()
    
    # Clean up
    segmentEditorWidget = None
    slicer.mrmlScene.RemoveNode(segmentEditorNode)
    
    # Make segmentation results visible in 3D
    segmentationNode.CreateClosedSurfaceRepresentation()
    
    # SURFACE MESH CREATION
    # https://discourse.slicer.org/t/load-segmentation-and-export-surface-mesh-as-model-ply/2646/10?u=paleomariomm
    surfaceMesh = segmentationNode.GetClosedSurfaceInternalRepresentation(addedSegmentID)
    writer = vtk.vtkPLYWriter()
    writer.SetInputData(surfaceMesh)
    writer.SetFileName(fr"{dicomDataDir}_surfaceMesh.ply")
    writer.Update()
    slicer.mrmlScene.Clear(0)
