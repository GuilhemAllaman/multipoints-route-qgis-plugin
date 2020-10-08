# -*- coding: utf-8 -*-
"""
/***************************************************************************
 MultiPointsRoute
                                 A QGIS plugin
 Compute route with multiple middle points using Webservices
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2020-10-05
        git sha              : $Format:%H$
        copyright            : (C) 2020 by Guilhem Allaman
        email                : dev@guilhemallaman.net
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon, QColor
from qgis.PyQt.QtWidgets import QAction, QMessageBox

from qgis.core import *
from qgis.gui import *

from .route_service import RouteServiceFactory, RouteService

# Initialize Qt resources from file resources.py
from .resources import *

# Import the code for the dialog
from .multi_points_route_dialog import MultiPointsRouteDialog
import os.path

PLUGIN_NAME = 'Multi Points Route'

class MultiPointsRoute:

    # constructor
    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(self.plugin_dir, 'i18n', 'MultiPointsRoute_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(PLUGIN_NAME)
        self.toolbar = self.iface.addToolBar(PLUGIN_NAME)
        self.toolbar.setObjectName(PLUGIN_NAME)

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        return QCoreApplication.translate('MultiPointsRoute', message)

    def add_action(self, icon_path, text, callback, enabled_flag=True,
        add_to_menu=True, add_to_toolbar=True, status_tip=None, whats_this=None, parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.iface.addToolBarIcon(action)
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(self.menu, action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        icon_path = ':/plugins/multi_points_route/icon.png'
        self.add_action(icon_path, text=self.tr(PLUGIN_NAME),
            callback=self.run, parent=self.iface.mainWindow())

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(self.tr(PLUGIN_NAME),action)
            self.iface.removeToolBarIcon(action)
        del self.toolbar

    # returns a coordinates transformer using Qgis project's coordinates
    def transformer(self) -> QgsCoordinateTransform:
        crs_project = self.canvas.mapSettings().destinationCrs()
        crs_wgs84 = QgsCoordinateReferenceSystem(4326)
        return QgsCoordinateTransform(crs_wgs84, crs_project, QgsProject.instance())


    # when service combobox changes
    def service_selected_change(self):
        self.service = self.service_factory.service(self.dlg.combo_box_web_service.currentText())
        self.dlg.combo_box_transport_mode.clear()
        self.dlg.combo_box_transport_mode.addItems(self.service.modes())

    # creates or reassign rubber bands
    def init_rubber_bands(self):
        self.point_rubber_band = QgsRubberBand(self.canvas, QgsWkbTypes.PointGeometry)
        self.point_rubber_band.setColor(QColor('#FF0000'))
        self.line_rubber_band = QgsRubberBand(self.canvas, QgsWkbTypes.LineGeometry)
        self.line_rubber_band.setColor(QColor('#0000FF'))


    # when select points button is clicked
    def select_points(self):
        self.init_rubber_bands()
        self.canvas.setMapTool(self.click_tool)
        self.dlg.showMinimized()
    

    # when clear selection button is clicked
    def clear_selection(self):
        self.clear()
        self.dlg.label_points_count.setText('{} points selected'.format(len(self.middle_points)))
    

    # when a point on the map is clicked
    def map_point_click(self, point: QgsPointXY):

        # transform points coordinates to WGS84
        transformed = self.transformer().transform(point, QgsCoordinateTransform.ReverseTransform)

        # add transformed point to list and rubberbands
        self.middle_points.append(QgsPoint(transformed.x(), transformed.y()))
        self.point_rubber_band.addPoint(point)
        self.line_rubber_band.addPoint(point)
        self.dlg.label_points_count.setText('{} points selected'.format(len(self.middle_points)))

    # clear and remove elements
    def clear(self):
        if self.point_rubber_band:
            self.point_rubber_band.reset()
        if self.line_rubber_band:
            self.line_rubber_band.reset()
        self.canvas.unsetMapTool(self.click_tool)
        self.middle_points.clear()

    # compute a route between selected points using a webservice
    def compute_route(self):
        try:
            layer = self.service.compute_route(self.middle_points, self.dlg.combo_box_transport_mode.currentText())
            layer.loadNamedStyle(self.plugin_dir + os.sep + 'styles' + os.sep + 'line-default.qml')
            QgsProject.instance().addMapLayer(layer)
        except:
            msg = QMessageBox()
            msg.setWindowTitle("Error")
            msg.setIcon(QMessageBox.Warning)
            msg.setText('Error while computing route with webservice "{}"'.format(self.dlg.combo_box_web_service.currentText()))
            msg.exec_()            

    # run plugin
    def run(self):
        
        self.middle_points = []
        self.service_factory = RouteServiceFactory()
        self.canvas = self.iface.mapCanvas()
        self.init_rubber_bands()
        self.click_tool = QgsMapToolEmitPoint(self.canvas)
        self.click_tool.canvasClicked.connect(self.map_point_click)
        self.dlg = MultiPointsRouteDialog()

        self.dlg.button_select_points.clicked.connect(self.select_points)
        self.dlg.button_compute_route.clicked.connect(self.compute_route)
        self.dlg.button_clear_selection.clicked.connect(self.clear_selection)
        self.dlg.combo_box_web_service.clear()
        self.dlg.combo_box_web_service.addItems(self.service_factory.available_services())
        self.dlg.combo_box_web_service.currentIndexChanged.connect(self.service_selected_change)
        self.service_selected_change()
        self.dlg.finished.connect(self.clear)
        self.dlg.show()
