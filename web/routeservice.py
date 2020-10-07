import requests
from abc import *
from qgis.core import *
from qgis.PyQt.QtCore import QVariant

LOG_TAG = 'MultiPointsRoute'
ORS_KEY = '5b3ce3597851110001cf6248825666083b1e45f79ea80b6d26f8b0a2'
LAYER_NAME = 'Route Result'
LAYER_ATTRIBUTES = [QgsField('distance', QVariant.Double), QgsField('duration',  QVariant.Double)]

def layer_name(mode: str, service: str) -> str:
  return 'Route result -{}- (service: {})'.format(mode, service)

def route_result_layer_from_features(features: [QgsFeature], mode: str, service: str) -> QgsVectorLayer:

  layer = QgsVectorLayer('LineString?crs=EPSG:4326', layer_name(mode, service), 'memory')
  data_provider = layer.dataProvider()
  data_provider.addAttributes(LAYER_ATTRIBUTES)
  layer.updateFields()
  data_provider.addFeatures(features)
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
    return route_result_layer_from_features([f], mode, 'TEST')

class ORSService(RouteService):

  def modes(self) -> [str]:
    return ['driving-car', 'cycling-regular', 'foot-walking']

  def compute_route(self, points: [QgsPoint], mode: str) -> QgsVectorLayer:
    url = 'https://api.openrouteservice.org/v2/directions/{}/geojson'.format(mode)
    headers = {
      'Accept': 'application/json, text/plain, */*',
      'Accept-Encoding': 'gzip, deflate, br',
      'Authorization': ORS_KEY,
      'Content-Type':	'application/json',
      'User-Agent': 'QGIS'
    }
    payload = {'coordinates': [[p.x(), p.y()] for p in points]}

    req = requests.post(url, headers=headers, json=payload)
    feature = req.json()['features'][0]
    distance = feature['properties']['summary']['distance']
    duration = feature['properties']['summary']['duration']
    res_points = [QgsPoint(p[0], p[1]) for p in feature['geometry']['coordinates']]

    feature = QgsFeature()
    feature.setGeometry(QgsGeometry.fromPolyline(res_points))
    feature.setAttributes([distance, duration])

    return route_result_layer_from_features([feature], mode, 'ORS')


class CustomService(RouteService):

  def modes(self) -> [str]:
    return ['driving', 'cycling', 'walking']

  def compute_route(self, points: [QgsPoint], mode: str) -> QgsVectorLayer:
    return route_result_layer_from_features([], mode, 'CUSTOM')

class RouteServiceFactory:

  services = {
    'ORS': ORSService(),
    'Custom': CustomService(),
    'test': TestService()
  }

  def available_services(self) -> [str]:
    return self.services.keys()
  
  def service(self, name: str) -> RouteService:
    return self.services.get(name)