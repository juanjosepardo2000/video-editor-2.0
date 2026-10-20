import unittest

from src.nle_bridge.qc_geometry import audit_layout, contrast_ratio


class GeometryQcTests(unittest.TestCase):
    def setUp(self):
        self.faces = {"frames": [{"t": 1.0, "boxes": [{"x": .3, "y": .2, "w": .3, "h": .3}]}]}

    def layout(self, box):
        return {"fps": 30, "layers": [{"beat": 1, "kind": "graphic", "startFrame": 0, "endFrame": 60, "box": box, "textColor": "#111111", "backgroundColor": "#FFFFFF", "occludesSpeaker": False}]}

    def test_detects_card_over_face(self):
        checks = audit_layout(self.layout({"x": .25, "y": .15, "w": .5, "h": .3}), self.faces)
        self.assertEqual(next(item for item in checks if item["id"] == "face_overlap")["status"], "fail")

    def test_accepts_face_safe_card(self):
        checks = audit_layout(self.layout({"x": .1, "y": .65, "w": .7, "h": .1}), self.faces)
        self.assertEqual(next(item for item in checks if item["id"] == "face_overlap")["status"], "pass")

    def test_contrast_ratio(self):
        self.assertGreaterEqual(contrast_ratio("#111111", "#FFFFFF"), 4.5)
        self.assertLess(contrast_ratio("#777777", "#888888"), 4.5)


if __name__ == "__main__":
    unittest.main()
