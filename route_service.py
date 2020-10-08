import requests
from abc import *
from qgis.core import *
from qgis.PyQt.QtCore import QVariant

LOG_TAG = 'MultiPointsRoute'
ORS_KEY = '5b3ce3597851110001cf6248825666083b1e45f79ea80b6d26f8b0a2'

def layer_name(mode: str, distance: float, duration: float) -> str:
  return 'Route  -{}-  ({:.2f} km, {:.0f} min)'.format(mode, distance/1000, duration/60)

def route_result_layer_from_features(features: [QgsFeature], mode: str, distance: float, duration: float) -> QgsVectorLayer:

  layer = QgsVectorLayer('LineString?crs=EPSG:4326', layer_name(mode, distance, duration), 'memory')
  data_provider = layer.dataProvider()
  data_provider.addAttributes([QgsField('distance', QVariant.Double), QgsField('duration',  QVariant.Double)])
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

class MultiPointsRouteService(RouteService):

  def __init__(self, host: str):
    self.host = host

  def modes(self) -> [str]:
    return ['cycling', 'driving', 'walking']

  def compute_route(self, points: [QgsPoint], mode: str) -> QgsVectorLayer:

    url = '{}/route/{}'.format(self.host, mode)
    payload = {'points': [[p.x(), p.y()] for p in points]}
    req = requests.post(url, json=payload)

    route = req.json()['route']
    distance = route['distance']
    duration = route['duration']
    res_points = [QgsPoint(p[0], p[1]) for p in route['points']]

    feature = QgsFeature()
    feature.setGeometry(QgsGeometry.fromPolyline(res_points))
    feature.setAttributes([distance, duration])

    return route_result_layer_from_features([feature], mode, distance, duration)

class OrsService(RouteService):

  def modes(self) -> [str]:
    return ['cycling-regular', 'driving-car', 'foot-walking']

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

    return route_result_layer_from_features([feature], mode, distance, duration)


class RouteServiceFactory:

  services = {
    'MPR local': MultiPointsRouteService('http://localhost:5000'),
    'MPR': MultiPointsRouteService('https://mpr.guilhemallaman.net'),
    'ORS': OrsService()
  }

  def available_services(self) -> [str]:
    return self.services.keys()
  
  def service(self, name: str) -> RouteService:
    return self.services.get(name)