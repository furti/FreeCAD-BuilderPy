import FreeCAD


class AbstractFeature:
    def append(self, obj, context):
        pass


class AbstractBuilder:
    def __init__(self, object_type):
        self.object_type = object_type
        self.features = []

    def addFeature(self, feature):
        self.features.append(feature)

        return feature

    def build(self, name):
        candidates = self.find_candidates(name)
        obj = None

        if len(candidates) == 1:
            obj = candidates[0]
            self.cleanup_object(obj)
        else:
            obj = FreeCAD.ActiveDocument.addObject(self.object_type, name)

        context = self.build_context()

        for feature in self.features:
            feature.append(obj, context)

        FreeCAD.ActiveDocument.recompute()

        return obj

    def find_candidates(self, name):
        return FreeCAD.ActiveDocument.findObjects(self.object_type, name)

    def build_context(self):
        return None

    def cleanup_object(self, obj):
        pass
