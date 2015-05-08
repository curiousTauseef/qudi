# -*- coding: utf-8 -*-
"""
Created on Tue May 5 2015

Lachlan Rogers
"""

from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
import numpy as np

from collections import OrderedDict
from core.Base import Base
from gui.TrackpointManager.TrackpointManagerGuiUI import Ui_TrackpointManager
from gui.Confocal.ConfocalGui import ColorBar



class PointMarker(pg.CircleROI):
    """Creates a circle as a marker. 
        
        @param int[2] pos: (length-2 sequence) The position of the ROI’s origin.
        @param int[2] size: (length-2 sequence) The size of the ROI’s bounding rectangle.
        @param **args: All extra keyword arguments are passed to ROI()
        
        Have a look at: 
        http://www.pyqtgraph.org/documentation/graphicsItems/roi.html    
    """
    
    def __init__(self, pos, size, **args):
        pg.CircleROI.__init__(self, pos, size, **args)
#        handles=self.getHandles()
#        for handle in handles:
#            print(handle)
#            self.removeHandle(handle)


class CustomViewBox(pg.ViewBox):
    def __init__(self, *args, **kwds):
        pg.ViewBox.__init__(self, *args, **kwds)
        self.setMouseMode(self.RectMode)

    ## reimplement right-click to zoom out
    def mouseClickEvent(self, ev):
        if ev.button() == QtCore.Qt.RightButton:
            #self.autoRange()
            self.setXRange(0,5)
            self.setYRange(0,10)

    def mouseDragEvent(self, ev,axis=0):
        if (ev.button() == QtCore.Qt.LeftButton) and (ev.modifiers() & QtCore.Qt.ControlModifier):
            pg.ViewBox.mouseDragEvent(self, ev,axis)
        else:
            ev.ignore()
  
          
            
class TrackpointManagerMainWindow(QtGui.QMainWindow,Ui_TrackpointManager):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.setupUi(self)
        

            
               
            
class TrackpointManagerGui(Base,QtGui.QMainWindow,Ui_TrackpointManager):
    """
    This is the GUI Class for TrackpointManager
    """
    
    

    def __init__(self, manager, name, config, **kwargs):
        ## declare actions for state transitions
        c_dict = {'onactivate': self.initUI}
        Base.__init__(self,
                    manager,
                    name,
                    config,
                    c_dict)
        
        self._modclass = 'TrackpointManagerGui'
        self._modtype = 'gui'
        
        ## declare connectors
        self.connector['in']['trackerlogic1'] = OrderedDict()
        self.connector['in']['trackerlogic1']['class'] = 'TrackpointManagerLogic'
        self.connector['in']['trackerlogic1']['object'] = None

        self.connector['in']['confocallogic1'] = OrderedDict()
        self.connector['in']['confocallogic1']['class'] = 'ConfocalLogic'
        self.connector['in']['confocallogic1']['object'] = None

#        self.connector['in']['savelogic'] = OrderedDict()
#        self.connector['in']['savelogic']['class'] = 'SaveLogic'
#        self.connector['in']['savelogic']['object'] = None

        self.logMsg('The following configuration was found.', 
                    msgType='status')
                            
        # checking for the right configuration
        for key in config.keys():
            self.logMsg('{}: {}'.format(key,config[key]), 
                        msgType='status')  
                        
    def initUI(self, e=None):
        """ Definition, configuration and initialisation of the Trackpoint Manager GUI.
          
          @param class e: event class from Fysom


        This init connects all the graphic modules, which were created in the
        *.ui file and configures the event handling between the modules.
        
        """
        
        self._tp_manager_logic = self.connector['in']['trackerlogic1']['object']
        self._confocal_logic = self.connector['in']['confocallogic1']['object']
        print("Trackpoint Manager logic is", self._tp_manager_logic)
        print("Confocal logic is", self._confocal_logic)
        
#        self._save_logic = self.connector['in']['savelogic']['object']
#        print("Save logic is", self._save_logic)  
        
        # Use the inherited class 'Ui_TrackpointManagerGuiTemplate' to create now the 
        # GUI element:
        self._mw = TrackpointManagerMainWindow()

                
        #####################
        # Setting up display of ROI map xy image
        #####################

        # Get the image for the display from the logic: 
        roi_map_data = self._confocal_logic.xy_image[:,:,3].transpose()
             
        # Load the image in the display:
        self.roi_map_image = pg.ImageItem(roi_map_data)
        self.roi_map_image.setRect(QtCore.QRectF(self._confocal_logic.image_x_range[0], self._confocal_logic.image_y_range[0], self._confocal_logic.image_x_range[1]-self._confocal_logic.image_x_range[0], self._confocal_logic.image_y_range[1]-self._confocal_logic.image_y_range[0]))
        
        # Add the display item to the roi map ViewWidget defined in the UI file
        self._mw.roi_map_ViewWidget.addItem(self.roi_map_image)
        
        # create a color map that goes from dark red to dark blue:

        # Absolute scale relative to the expected data not important. This 
        # should have the same amount of entries (num parameter) as the number
        # of values given in color. 
        pos = np.linspace(0.0, 1.0, num=10)
        color = np.array([[127,  0,  0,255], [255, 26,  0,255], [255,129,  0,255],
                          [254,237,  0,255], [160,255, 86,255], [ 66,255,149,255],
                          [  0,204,255,255], [  0, 88,255,255], [  0,  0,241,255],
                          [  0,  0,132,255]], dtype=np.ubyte)
                      
        color_inv = np.array([ [  0,  0,132,255], [  0,  0,241,255], [  0, 88,255,255],
                               [  0,204,255,255], [ 66,255,149,255], [160,255, 86,255],
                               [254,237,  0,255], [255,129,  0,255], [255, 26,  0,255],
                               [127,  0,  0,255] ], dtype=np.ubyte)
        colmap = pg.ColorMap(pos, color_inv)
        
        self.colmap_norm = pg.ColorMap(pos, color/255)

        # get the LookUpTable (LUT), first two params should match the position
        # scale extremes passed to ColorMap(). 
        # I believe last one just has to be >= the difference between the min and max level set later
        lut = colmap.getLookupTable(0, 1, 2000)

            
        self.roi_map_image.setLookupTable(lut)

        #####################
        # Setting up display of sample shift plot
        #####################

        # Load image in the display
        self.x_shift_plot = pg.ScatterPlotItem([0],[0],symbol='o')
        self.y_shift_plot = pg.ScatterPlotItem([0],[0],symbol='s')
        self.z_shift_plot = pg.ScatterPlotItem([0],[0],symbol='t')

        # Add the plot to the ViewWidget defined in the UI file
        self._mw.sample_shift_ViewWidget.addItem(self.x_shift_plot)
        self._mw.sample_shift_ViewWidget.addItem(self.y_shift_plot)
        self._mw.sample_shift_ViewWidget.addItem(self.z_shift_plot)


        #####################        
        # Connect signals
        #####################        

        self._mw.get_confocal_image_Button.clicked.connect(self.get_confocal_image)
        self._mw.set_tp_Button.clicked.connect(self.set_new_trackpoint)
        self._mw.goto_tp_Button.clicked.connect(self.goto_trackpoint)
        self._mw.delete_last_pos_Button.clicked.connect(self.delete_last_point)
        self._mw.manual_update_tp_Button.clicked.connect(self.manual_update_trackpoint)
        self._mw.tp_name_Input.returnPressed.connect(self.change_tp_name)
        self._mw.delete_tp_Button.clicked.connect(self.delete_trackpoint)

        self._mw.update_tp_Button.clicked.connect(self.update_tp_pos)

        self._mw.periodic_update_Button.toggled.connect(self.toggle_periodic_update)
        
        self._markers=[]
        
        #Signal at end of refocus
        self._tp_manager_logic.signal_refocus_finished.connect(self._refocus_finished, QtCore.Qt.QueuedConnection)
        self._tp_manager_logic.signal_timer_updated.connect(self._update_timer, QtCore.Qt.QueuedConnection)
 
#        print('Main Trackpoint Manager Window shown:')
        self._mw.show()
    
    def get_confocal_image(self):
        self.roi_map_image.getViewBox().enableAutoRange()
        self.roi_map_image.setRect(QtCore.QRectF(self._confocal_logic.image_x_range[0], self._confocal_logic.image_y_range[0], self._confocal_logic.image_x_range[1]-self._confocal_logic.image_x_range[0], self._confocal_logic.image_y_range[1]-self._confocal_logic.image_y_range[0]))
        self.roi_map_image.setImage(image=self._confocal_logic.xy_image[:,:,3].transpose(),autoLevels=True)

    
    def set_new_trackpoint(self):
        ''' This method sets a new trackpoint from the current crosshair position

        '''
        key=self._tp_manager_logic.add_trackpoint()

        print('new trackpoint '+key)
        print(self._tp_manager_logic.get_all_trackpoints())
        print(self._tp_manager_logic.get_last_point(trackpointkey=key))

        self.population_tp_list()

        # Set the newly added trackpoint as the selected tp to manage.
        self._mw.manage_tp_Input.setCurrentIndex(self._mw.manage_tp_Input.findData(key))
        
    def delete_last_point(self):
        ''' This method deletes the last track position of a chosen trackpoint
        '''
        
        key=self._mw.manage_tp_Input.itemData(self._mw.manage_tp_Input.currentIndex())
        self._tp_manager_logic.delete_last_point(trackpointkey=key)

    def delete_trackpoint(self):
        '''This method deletes a trackpoint from the list of managed points
        '''
        key=self._mw.manage_tp_Input.itemData(self._mw.manage_tp_Input.currentIndex())
        self._tp_manager_logic.delete_trackpoint(trackpointname=key)
    
        self.population_tp_list()

    def manual_update_trackpoint(self):
        pass

    def toggle_periodic_update(self):
        if self._tp_manager_logic.timer ==  None:
            key=self._mw.active_tp_Input.itemData(self._mw.active_tp_Input.currentIndex())
            period = self._mw.update_period_Input.value()

            self._tp_manager_logic.start_periodic_refocus(duration=period, trackpointkey = key)

        else:
            self._tp_manager_logic.stop_periodic_refocus()

    def goto_trackpoint(self, key):
        ''' Go to the last known position of trackpoint <key>
        '''
        
        key=self._mw.active_tp_Input.itemData(self._mw.active_tp_Input.currentIndex())

        self._tp_manager_logic.go_to_trackpoint(trackpointkey=key)

        print(self._tp_manager_logic.get_last_point(trackpointkey=key))


    def population_tp_list(self):
        ''' Populate the dropdown box for selecting a trackpoint
        '''
        self._mw.active_tp_Input.clear()
        self._mw.active_tp_Input.setInsertPolicy(QtGui.QComboBox.InsertAlphabetically)

        self._mw.manage_tp_Input.clear()
        self._mw.manage_tp_Input.setInsertPolicy(QtGui.QComboBox.InsertAlphabetically)
        
        for marker in self._markers:
            self._mw.roi_map_ViewWidget.removeItem(marker)
            del marker
            
        self._markers=[]
        
        for key in self._tp_manager_logic.get_all_trackpoints():
            #self._tp_manager_logic.track_point_list[key].set_name('Kay_'+key[6:])
            if key is not 'crosshair' and key is not 'sample':
                self._mw.active_tp_Input.addItem(self._tp_manager_logic.get_name(trackpointkey=key), key)
                self._mw.manage_tp_Input.addItem(self._tp_manager_logic.get_name(trackpointkey=key), key)
                
                # Create Region of Interest as marker:
                position=self._tp_manager_logic.get_last_point(trackpointkey=key)
                position=position[:2]-[2.5,2.5]
                self._markers.append(\
                    PointMarker(position, 
                                [5, 5], 
                                pen={'color': "F0F", 'width': 2}, 
                                movable=False, 
                                scaleSnap=True, 
                                snapSize=1.0))
                # Add to the Map Widget
                self._mw.roi_map_ViewWidget.addItem(self._markers[-1])

    def change_tp_name(self):
        '''Change the name of a trackpoint
        '''

        key=self._mw.manage_tp_Input.itemData(self._mw.manage_tp_Input.currentIndex())

        newname=self._mw.tp_name_Input.text()


        self._tp_manager_logic.set_name(trackpointkey=key, name=newname)

        self.population_tp_list()

        # Keep the renamed trackpoint as the selected tp to manage.
        self._mw.manage_tp_Input.setCurrentIndex(self._mw.manage_tp_Input.findData(key))

        #TODO: WHen manage trackpoint is changed, empty name field
        self._mw.tp_name_Input.setText('')

    def update_tp_pos(self):

        key=self._mw.active_tp_Input.itemData(self._mw.active_tp_Input.currentIndex())

        self._tp_manager_logic.optimise_trackpoint(trackpointkey=key)

    def _update_timer(self):
        #placeholder=QtGui.QLineEdit()
        #placeholder.setText('{0:.1f}'.format(self._tp_manager_logic.time_left))
        
#        print(self._tp_manager_logic.time_left)
        self._mw.time_till_next_update_Display.display( self._tp_manager_logic.time_left )

    def _refocus_finished(self):
        
        # Get trace data and calculate shifts in x,y,z
        tp_trace=self._tp_manager_logic.get_trace(trackpointkey='sample')

        time_shift_data = tp_trace[:,0] - tp_trace[0,0]
        x_shift_data  = tp_trace[:,1] - tp_trace[0,1] 
        y_shift_data  = tp_trace[:,2] - tp_trace[0,2] 
        z_shift_data  = tp_trace[:,3] - tp_trace[0,3] 
        self.x_shift_plot.setData(time_shift_data, x_shift_data)
        self.y_shift_plot.setData(time_shift_data, y_shift_data)
        self.z_shift_plot.setData(time_shift_data, z_shift_data)
        
#        print (self._tp_manager_logic.get_trace(trackpointkey='sample'))