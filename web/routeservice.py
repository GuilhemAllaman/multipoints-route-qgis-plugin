from qgis.core import *
from abc import *

LOG_TAG = 'MultiPointsRoute'

class RouteService:
  
  @abstractmethod
  def modes(self) -> [str]:
    pass

  @abstractmethod
  def compute_route(self, points: [QgsPoint], mode: str) -> [QgsFeature]:
    pass

class TestService(RouteService):
  
  def modes(self) -> [str]:
    return ['transform']

  def compute_route(self, points: [QgsPoint], mode: str) -> [QgsFeature]:
    f = QgsFeature()
    f.setGeometry(QgsGeometry.fromPolyline(points))
    return [f]

class ORSService(RouteService):

  def modes(self) -> [str]:
    return ['car', 'bike']

  def compute_route(self, points: [QgsPoint], mode: str) -> [QgsFeature]:
    return []

class CustomService(RouteService):

  def modes(self) -> [str]:
    return ['custom', 'car', 'bike']

  def compute_route(self, points: [QgsPoint], mode: str) -> [QgsFeature]:
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