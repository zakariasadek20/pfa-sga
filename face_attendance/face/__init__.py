"""Sous-paquet de reconnaissance faciale."""

from .engine import FaceEngine, DetectedFace, identify

__all__ = ["FaceEngine", "DetectedFace", "identify"]
