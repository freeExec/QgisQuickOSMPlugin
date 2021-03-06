# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QuickOSM
                                 A QGIS plugin
 OSM's Overpass API frontend
                             -------------------
        begin                : 2014-06-11
        copyright            : (C) 2014 by 3Liz
        email                : info at 3liz dot com
        contributor          : Etienne Trimaille
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

from QuickOSM import *

from PyQt4.QtWebKit import QWebView
from PyQt4.QtNetwork import *
from qgis.utils import iface

class Actions:
    '''
    Manage actions available on layers
    '''

    @staticmethod
    def run(field,value):
        '''
        Run an action with only one value as parameter
        
        @param field:Type of the action
        @type field:str
        @param value:Value of the field for one entity
        @type value:str
        '''
        
        if value == '':
            iface.messageBar().pushMessage(QApplication.translate("QuickOSM", u"Sorry man, this field is empty for this entity."), level=QgsMessageBar.WARNING , duration=7)
        else:
            field = unicode(field, "UTF-8")
            value = unicode(value, "UTF-8")
            
            if field in ["url","website","wikipedia"]:
                var = QDesktopServices()
                url = None
                
                if field == "url" or field =="website":
                    url = value
                    
                if field == "ref_UAI":
                    url = "http://www.education.gouv.fr/pid24302/annuaire-resultat-recherche.html?lycee_name="+value
                    
                if field == "wikipedia":
                    url = "http://en.wikipedia.org/wiki/" + value
                    
                var.openUrl(QUrl(url))
            
            elif field == "josm":
                import urllib2
                try:
                    url = "http://localhost:8111/load_object?objects="+value
                    data = urllib2.urlopen(url).read()
                except urllib2.URLError:
                    iface.messageBar().pushMessage(QApplication.translate("QuickOSM", u"The JOSM remote seems to be disabled."), level=QgsMessageBar.CRITICAL , duration=7)
            
            #NOT USED 
            elif field == "rawedit":
                url = QUrl("http://rawedit.openstreetmap.fr/edit/"+value)
                webBrowser = QWebView(None)
                webBrowser.load(url)
                webBrowser.show()
                
    @staticmethod
    def runSketchLine(network,ref):
        '''
        Run an action with two values for sketchline
        
        @param network:network of the bus
        @type network:str
        @param ref:ref of the bus
        @type ref:str
        '''
        
        network = unicode(network, "UTF-8")
        ref = unicode(ref, "UTF-8")
        
        if network == '' or ref == '':
            iface.messageBar().pushMessage(QApplication.translate("QuickOSM", u"Sorry man, this field is empty for this entity."), level=QgsMessageBar.WARNING , duration=7)
        else:
            var = QDesktopServices()
            url = "http://www.overpass-api.de/api/sketch-line?network="+network+"&ref="+ref
            var.openUrl(QUrl(url))