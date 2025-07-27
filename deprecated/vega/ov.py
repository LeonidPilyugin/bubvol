from ovito.modifiers import *
from ovito.io import import_file
from ovito import pipeline as pln
import sys

def get_true_nvac(file, ref):
    pipeline = import_file(file)
    ws = WignerSeitzAnalysisModifier()
    ws.affine_mapping = pln.ReferenceConfigurationModifier.AffineMapping.ToReference
    ws.reference = pln.FileSource()
    ws.reference.load(ref)
    pipeline.modifiers.extend([
        ExpressionSelectionModifier(expression="ParticleType==2"),
        DeleteSelectedModifier(),
        WrapPeriodicImagesModifier(),
        ws,
    ])
    data = pipeline.compute()

    return data.attributes["WignerSeitz.vacancy_count"]
    
