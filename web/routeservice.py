from qgis.core import QgsPoint, QgsPointXY, QgsFeature, QgsGeometry, QgsMessageLog
from abc import ABCMeta, abstractmethod

LOG_TAG = 'MultiPointsRoute'

class RouteService:
  
  @abstractmethod
  def modes(self) -> [str]:
    pass

  @abstractmethod
  def compute_route(self, points: [QgsPointXY], mode: str) -> [QgsFeature]:
    pass

class TestService(RouteService):
  
  def modes(self) -> [str]:
    return ['transform']

  def compute_route(self, points: [QgsPointXY], mode: str) -> [QgsFeature]:
    f = QgsFeature()
    # f.setGeometry(QgsGeometry.fromPolyline([QgsPoint(p.x(), p.y()) for p in points]))
    # f.setGeometry(QgsGeometry.fromPolylineXY(points))
    f.setGeometry(QgsGeometry.fromPolyline([QgsPoint(-5, 45), QgsPoint(5, 45)]))
    return [f]

class ORSService(RouteService):

  def modes(self) -> [str]:
    return ['car', 'bike']

  def compute_route(self, points: [QgsPointXY], mode: str) -> [QgsFeature]:
    return []

class CustomService(RouteService):

  def modes(self) -> [str]:
    return ['custom', 'car', 'bike']

  def compute_route(self, points: [QgsPointXY], mode: str) -> [QgsFeature]:
    return []

class RouteServiceFactory:

  services = {
    'test': TestService(),
    'ORS': ORSService(),
    'Custom': CustomService()
  }

  def available_services(self) -> [str]:
    return self.services.keys()
  
  def service(self, name: str) -> RouteService:
    return self.services.get(name)