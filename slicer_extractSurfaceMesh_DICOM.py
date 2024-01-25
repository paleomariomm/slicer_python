# FOR LOOP
# https://stackoverflow.com/questions/77865010/run-python-script-in-each-subfolder-automatically

# For (I in volumes) 
#                 Vol = read.volume (this will change everytime)
#                 Roi = read.ROI (this is a fixed ROI)
#                 Do the cropping and assign a new volume node (or even overwrite it)
#                 Start the segmentation subroutine (threshold + island tools + smoothing and morphological closing)
#                 Export the segmentation as a 3D object and save it as PLY/OBJ file 
#                 Optionally save the cropped volume
#                 Reset the scene


import os
from DICOMLib import DICOMUtils

yourpath = r"C:/Users/mario.modesto/Desktop/DICOM"
# yourpath = r"//clscidat.cenieh.local/TIED2-TEETH/AIM_1_QuantGen/Baboons/CT Scans/W101-W200"

#walk through DICOM directory
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
    
    # CROPPING
      #create a blank Markup ROI
    roiNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsROINode")
      # https://discourse.slicer.org/t/fix-size-in-cropped-volume/21114/3
    roiNode.SetName("R")
      # this gets the ROI node and assigns it to a variable
    roiNode = slicer.util.getNode('R')
      # Set the sizes you want the ROI here. Change the numbers to suit your application
    radius = [100,350,155] #ancho,largo,altura
      # This sets the ROI size to the dimensions specified above
    roiNode.SetRadiusXYZ(radius)
    
    # Set parameters
    cropVolumeLogic = slicer.modules.cropvolume.logic()
    cropVolumeParameterNode = slicer.vtkMRMLCropVolumeParametersNode()
    cropVolumeParameterNode.SetROINodeID(roiNode.GetID())
    cropVolumeParameterNode.SetInputVolumeNodeID(volumeNode.GetID())
    cropVolumeParameterNode.SetIsotropicResampling(True)
    
    # Apply cropping
    cropVolumeLogic.Apply(cropVolumeParameterNode)
    croppedVolume = slicer.mrmlScene.GetNodeByID(cropVolumeParameterNode.GetOutputVolumeNodeID())
    
    # SEGMENTATION THRESHOLDING
    # https://gist.github.com/lassoan/1673b25d8e7913cbc245b4f09ed853f9
    
      # Create segmentation
    segmentationNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")
    segmentationNode.CreateDefaultDisplayNodes() # only needed for display
    segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(croppedVolume)
    addedSegmentID = segmentationNode.GetSegmentation().AddEmptySegment(baboon_skull)
    
      # Create segment editor to get access to effects
    segmentEditorWidget = slicer.qMRMLSegmentEditorWidget()
    segmentEditorWidget.setMRMLScene(slicer.mrmlScene)
    segmentEditorNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentEditorNode")
    segmentEditorWidget.setMRMLSegmentEditorNode(segmentEditorNode)
    segmentEditorWidget.setSegmentationNode(segmentationNode)
    segmentEditorWidget.setMasterVolumeNode(croppedVolume)
    
      # Thresholding
    segmentEditorWidget.setActiveEffectByName("Threshold")
    effect = segmentEditorWidget.activeEffect()
    effect.setParameter("MinimumThreshold","60")
    effect.setParameter("MaximumThreshold","3071")
    effect.self().onApply()
    
    # Systematically remove small islands
    # https://discourse.slicer.org/t/islands-segmentation-via-python-script/21021
    # segmentEditorNode.SetSelectedSegmentID("segmentationNode")
    # segmentEditorWidget.setActiveEffectByName("Islands")
    # effect = segmentEditorWidget.activeEffect()
    # effect.setParameter("MinimumSize","1000")
    # effect.setParameter("Operation","KEEP_LARGEST_ISLAND")
    # segmentEditorNode.SetOverwriteMode(slicer.vtkMRMLSegmentEditorNode.OverwriteNone) 
    # segmentEditorNode.SetMaskMode(slicer.vtkMRMLSegmentEditorNode.PaintAllowedEverywhere)  
    # effect.self().onApply()
    
    # Clean up
    segmentEditorWidget = None
    slicer.mrmlScene.RemoveNode(segmentEditorNode)
    
    # Make segmentation results visible in 3D
    segmentationNode.CreateClosedSurfaceRepresentation()
    
    # Crear surface mesh y exportar en PLY
    # https://discourse.slicer.org/t/load-segmentation-and-export-surface-mesh-as-model-ply/2646/10?u=paleomariomm
    
    surfaceMesh = segmentationNode.GetClosedSurfaceInternalRepresentation(addedSegmentID)
    writer = vtk.vtkPLYWriter()
    writer.SetInputData(surfaceMesh)
    writer.SetFileName(fr"{dicomDataDir}_surfaceMesh.ply")
    # writer.SetFileName("C:/Users/mario.modesto/Desktop/DICOM/"+baboon_skull+"_surfaceMesh.ply")
    writer.Update()
    slicer.mrmlScene.Clear(0)
