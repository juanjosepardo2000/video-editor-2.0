import type { GeneratedLayout } from "./types";

export const generatedLayout = {
  "fps": 30,
  "width": 1080,
  "height": 1920,
  "profile": "viral-dinamico",
  "faceSource": "pipeline/examples/face_boxes.fixture.json",
  "usedFixture": true,
  "warnings": [],
  "layers": [
    {
      "beat": 1,
      "kind": "caption",
      "scene": "CAPTIONS",
      "startFrame": 0,
      "endFrame": 96,
      "box": {
        "x": 0.0822,
        "y": 0.6,
        "w": 0.78,
        "h": 0.1
      },
      "textColor": "#1D1D1F",
      "backgroundColor": "#F5F8F6",
      "occludesSpeaker": false,
      "keyframes": []
    },
    {
      "beat": 2,
      "kind": "graphic",
      "scene": "CAPTION_UI",
      "startFrame": 96,
      "endFrame": 249,
      "box": {
        "x": 0.2797,
        "y": 0.7086,
        "w": 0.385,
        "h": 0.0935
      },
      "textColor": "#1D1D1F",
      "backgroundColor": "#F5FCF9",
      "occludesSpeaker": false,
      "keyframes": []
    },
    {
      "beat": 2,
      "kind": "caption",
      "scene": "CAPTION_UI",
      "startFrame": 96,
      "endFrame": 249,
      "box": {
        "x": 0.0822,
        "y": 0.6,
        "w": 0.78,
        "h": 0.1
      },
      "textColor": "#1D1D1F",
      "backgroundColor": "#F5F8F6",
      "occludesSpeaker": false,
      "keyframes": []
    },
    {
      "beat": 3,
      "kind": "graphic",
      "scene": "FULLSCREEN",
      "startFrame": 249,
      "endFrame": 351,
      "box": {
        "x": 0,
        "y": 0,
        "w": 1,
        "h": 1
      },
      "textColor": "#1D1D1F",
      "backgroundColor": "#F5FCF9",
      "occludesSpeaker": true,
      "keyframes": []
    },
    {
      "beat": 4,
      "kind": "graphic",
      "scene": "SPLIT",
      "startFrame": 351,
      "endFrame": 447,
      "box": {
        "x": 0,
        "y": 0,
        "w": 1,
        "h": 0.5
      },
      "textColor": "#1D1D1F",
      "backgroundColor": "#F5FCF9",
      "occludesSpeaker": true,
      "keyframes": []
    },
    {
      "beat": 4,
      "kind": "speaker",
      "scene": "SPLIT",
      "startFrame": 351,
      "endFrame": 447,
      "box": {
        "x": 0,
        "y": 0.5,
        "w": 1,
        "h": 0.5
      },
      "textColor": "#1D1D1F",
      "backgroundColor": "transparent",
      "occludesSpeaker": false,
      "keyframes": []
    },
    {
      "beat": 4,
      "kind": "caption",
      "scene": "SPLIT",
      "startFrame": 351,
      "endFrame": 447,
      "box": {
        "x": 0.0822,
        "y": 0.6,
        "w": 0.78,
        "h": 0.1
      },
      "textColor": "#1D1D1F",
      "backgroundColor": "#F5F8F6",
      "occludesSpeaker": false,
      "keyframes": []
    },
    {
      "beat": 5,
      "kind": "caption",
      "scene": "CAPTIONS",
      "startFrame": 447,
      "endFrame": 483,
      "box": {
        "x": 0.0822,
        "y": 0.6,
        "w": 0.78,
        "h": 0.1
      },
      "textColor": "#1D1D1F",
      "backgroundColor": "#F5F8F6",
      "occludesSpeaker": false,
      "keyframes": []
    }
  ]
} as const satisfies GeneratedLayout;
