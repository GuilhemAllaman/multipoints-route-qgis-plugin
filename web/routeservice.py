from qgis.core import *
from abc import *
import requests

LOG_TAG = 'MultiPointsRoute'
ORS_KEY = '5b3ce3597851110001cf6248825666083b1e45f79ea80b6d26f8b0a2'
LAYER_NAME = 'Route Result'

def route_result_layer_from_features(features: [QgsFeature]) -> QgsVectorLayer:
  layer = QgsVectorLayer('LineString?crs=EPSG:4326', LAYER_NAME, 'memory')
  layer.startEditing()
  layer.addFeatures(features)
  layer.commitChanges()
  layer.updateExtents()
  return layer

class RouteService:
  
  @abstractmethod
  def modes(self) -> [str]:
    pass

  @abstractmethod
  def compute_route(self, points: [QgsPoint], mode: str) -> QgsVectorLayer:
    pass

class TestService(RouteService):
  
  def modes(self) -> [str]:
    return ['transform']

  def compute_route(self, points: [QgsPoint], mode: str) -> QgsVectorLayer:
    f = QgsFeature()
    f.setGeometry(QgsGeometry.fromPolyline(points))
    return route_result_layer_from_features([f])

class ORSService(RouteService):

  def modes(self) -> [str]:
    return ['driving-car', 'cycling-regular', 'foot-walking']

  def compute_route(self, points: [QgsPoint], mode: str) -> QgsVectorLayer:
    url = 'https://api.openrouteservice.org/v2/directions/{}/geojson'.format(mode)
    QgsMessageLog.logMessage(url, LOG_TAG, Qgis.Info)
    headers = {
      'Accept': 'application/json, text/plain, */*',
      'Accept-Encoding': 'gzip, deflate, br',
      'Authorization': '5b3ce3597851110001cf6248825666083b1e45f79ea80b6d26f8b0a2',
      'Content-Type':	'application/json',
      'User-Agent': 'Mozilla'
    }
    payload = {'coordinates': [[p.x(), p.y()] for p in points]}
    QgsMessageLog.logMessage(str(payload), LOG_TAG, Qgis.Info)
    req = requests.post(url, headers=headers, data=payload)
    QgsMessageLog.logMessage(req.text, LOG_TAG, Qgis.Info)
    return route_result_layer_from_features([])

class ORSBasicService(RouteService):

  def modes(self) -> [str]:
    return ['driving-car', 'cycling-regular', 'foot-walking']

  def compute_route(self, points: [QgsPoint], mode: str) -> QgsVectorLayer:
    start = points[0]
    end = points[-1]
    url = 'https://api.openrouteservice.org/v2/directions/{}?api_key={}&start={},{}&end={},{}'.format(mode, ORS_KEY, start.x(), start.y(), end.x(), end.y())
    headers = {
      'Accept': 'application/json, text/plain, */*',
      'Accept-Encoding': 'gzip, deflate, br',
      'Content-Type':	'application/json',
      'User-Agent': 'Mozilla'
    }
    request = requests.get(url, headers=headers)
    res_points = [QgsPoint(a[0], a[1]) for a in request.json()['features'][0]['geometry']['coordinates']]
    feature = QgsFeature()
    feature.setGeometry(QgsGeometry.fromPolyline(res_points))
    return route_result_layer_from_features([feature])

class CustomService(RouteService):

  def modes(self) -> [str]:
    return ['custom', 'car', 'bike']

  def compute_route(self, points: [QgsPoint], mode: str) -> QgsVectorLayer:
    return route_result_layer_from_features([])

class RouteServiceFactory:

  services = {
    'ORS basic (no middle points)': ORSBasicService(),
    'ORS complex (with middle points)': ORSService(),
    'Custom': CustomService(),
    'test': TestService()
  }

  def available_services(self) -> [str]:
    return self.services.keys()
  
  def service(self, name: str) -> RouteService:
    return self.services.get(name)