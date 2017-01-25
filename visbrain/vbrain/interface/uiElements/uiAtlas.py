"""Top level class for managing the MNI (rotation, structure...)
Make the bridge between GUI and deep functions. Add some usefull
commands for the user
"""

import numpy as np

import vispy.scene.cameras as viscam

from ...utils import slider2opacity, uiSpinValue

__all__ = ['uiAtlas']


class uiAtlas(object):

    """Link graphical interface with atlas functions
    """

    def __init__(self,):

        # Brain control :
        self.show_MNI.clicked.connect(self.brain_control)
        self.Both_only.clicked.connect(self.brain_control)
        self.Lhemi_only.clicked.connect(self.brain_control)
        self.Rhemi_only.clicked.connect(self.brain_control)

        # Rotation :
        self.q_coronal.clicked.connect(self._fcn_coronal)
        self.q_axial.clicked.connect(self._fcn_axial)
        self.q_sagittal.clicked.connect(self._fcn_sagittal)

        self.uiSwitchTemplate.currentIndexChanged.connect(self.brain_control)
        self.uiSwitchTemplate.setCurrentIndex(int(self.atlas.template[-1]) - 1)

        # Structure :
        eval('self.q_' + self.atlas.projection + '.setChecked(True)')
        self.q_internal.clicked.connect(self.brain_structure)
        self.q_external.clicked.connect(self.brain_structure)

        self.struct_color_edit.setPlaceholderText(
            "Ex: 'red', #ab4642, (1,0,0...)")


    def brain_control(self, *args, template=None, show=True, hemisphere=None):
        """Control the type of brain to use.

        Kargs:
            template: string, optional, (def: None)
                Template to use for the MNI brain. Use either 'B1',
                'B2' or 'B3'.

            show: bool, optional, (def: True)
                Show (True) or hide (False) the MNI brain.

            hemisphere: string, optional, (def: None)
                Define if you want to see only 'left' or 'right'
                hemisphere. Otherwise use 'both'.

        Example:
            >>> # Define a vbrain instance :
            >>> vb = vbrain()
            >>> # Display the right hemisphere of 'B3' template :
            >>> vb.brain_control(template='B3', hemisphere='right')
        """
        # Template :
        if template is not None:
            if template not in ['B1', 'B2', 'B3']:
                raise ValueError("""The template parameter must be either 'B1', 
                                 'B2 or 'B3'""")
            else:
                self.uiSwitchTemplate.setCurrentIndex(int(template[-1]) - 1)
        else:
            self.atlas.template = self.uiSwitchTemplate.currentText()

        # Show / hide MNI :
        self.show_MNI.setChecked(show)
        self.atlas.mesh.visible = self.show_MNI.isChecked()

        # Hemisphere :
        if hemisphere is not None:
            if hemisphere not in ['both', 'left', 'right']:
                raise ValueError("""The hemisphere parameter must be either 
                                 'both', 'left' or 'right'""")
            else:
                order = (['both', 'left', 'right'],
                         ['Both_only', 'Lhemi_only', 'Rhemi_only'])
                self.atlas.reload(hemisphere=hemisphere)
                eval('self.' + order[1][order[0].index(hemisphere)] + '.setChecked(True)')
        else:
            if self.Both_only.isChecked():
                self.atlas.reload(hemisphere='both')
            elif self.Lhemi_only.isChecked():
                self.atlas.reload(hemisphere='left')
            elif self.Rhemi_only.isChecked():
                self.atlas.reload(hemisphere='right')


    def rotate(self, fixed=None, custom=None):
        """Rotate the scene with all elements using either a
        predefined or custom rotation.

        Kargs:
            fixed: string, optional, (def: 'axial')
                Predefined rotation. Use either 'axial', 'coronal' or
                'sagittal'. As a complement, use the suffixe '_0' or
                '_1' to switch between possible views.

                * 'axial_0/1': switch between top/bottom view 
                * 'coronal_0/1': switch between front/back view 
                * 'sagittal_0/1': switch between left/right view 

            custom: tuple, optional, (def: None)
                Custom rotation. The custom parameter must be a
                tuple of two float respectively for azimuth and
                elevation.

        Example:
            >>> # Define a vbrain instance :
            >>> vb = vbrain()
            >>> # Predefined rotation :
            >>> vb.rotate(fixed='sagittal_1')
            >>> # Custom rotation :
            >>> vb.rotate(custom=(90.0, 0.0))
        """
        if fixed is not None:
            if not isinstance(fixed, str) or not any([bool(fixed.find(k)+1) for k in [
                                                     'axial', 'sagittal', 'coronal']]):
                raise ValueError("fixed must contain 'axial', 'coronal' or 'sagittal")
            else:
                if bool(fixed.find('_')+1):
                    view, side = tuple(fixed.split('_'))
                    exec('self.atlas.' + view + ' = ' + side)
                else:
                    view, side = fixed, None
        else:
            view, side = None, None
        if custom is not None:
            if not isinstance(custom, (tuple, list)) or len(custom) is not 2:
                raise ValueError("""The custom parameter must be a tuple of 
                                 two floats (azimuth, elevation)""")

        azimuth, elevation = 0, 90
        if view is not None:
            # Sagittal (left, right)
            if view == 'sagittal':
                if self.atlas.sagittal == 0:  # Left
                    azimuth, elevation = -90, 0
                    self.atlas.sagittal = 1
                elif self.atlas.sagittal == 1:  # Right
                    azimuth, elevation = 90, 0
                    self.atlas.sagittal = 0
                self.atlas.coronal, self.atlas.axial = 0, 0
            # Coronal (front, back)
            elif view == 'coronal':
                if self.atlas.coronal == 0:  # Front
                    azimuth, elevation = 180, 0
                    self.atlas.coronal = 1
                elif self.atlas.coronal == 1:  # Back
                    azimuth, elevation = 0, 0
                    self.atlas.coronal = 0
                self.atlas.sagittal, self.atlas.axial = 0, 0
            # Axial (top, bottom)
            elif view == 'axial':
                if self.atlas.axial == 0:  # Top
                    azimuth, elevation = 0, 90
                    self.atlas.axial = 1
                elif self.atlas.axial == 1:  # Bottom
                    azimuth, elevation = 0, -90
                    self.atlas.axial = 0
                self.atlas.sagittal, self.atlas.coronal = 0, 0
        elif custom is not None:
            azimuth, elevation = custom[0], custom[1]

        # Set camera and range :
        self.view.wc.camera.azimuth = azimuth
        self.view.wc.camera.elevation = elevation
        self.view.wc.camera.set_range(x=(-50, 50), y=(-50, 50), z=(-85, 85))


    def brain_structure(self, *args, structure=None):
        """Change to see either the surface only (external) or
        deep voxels inside the brain (internal).

        Kargs:
            structure: string, optional, (def: None)
                Choose either between 'internal' or 'external'.
                Inside the graphical interface, this can be done
                using the shortcut 3.

        Example:
            >>> # Define a vbrain instance :
            >>> vb = vbrain()
            >>> # Display the external surface :
            >>> vb.brain_structure(structure='external')
        """
        if structure is not None:
            if structure not in ['internal', 'external']:
                raise ValueError("""The structure parameter must be either 
                                 'internal' or 'external'""")
            else:
                eval('self.q_' + structure + '.setChecked(True)')

        if self.q_internal.isChecked():
            self.atlas.mesh.projection('internal')
        elif self.q_external.isChecked():
            self.atlas.mesh.projection('external')
        self.atlas.mesh.update()


    def _fcn_coronal(self):
        """GUI to deep function for a fixed coronal view
        """
        self.rotate(fixed='coronal')


    def _fcn_axial(self):
        """GUI to deep function for a fixed axial view
        """
        self.rotate(fixed='axial')


    def _fcn_sagittal(self):
        """GUI to deep function for a fixed sagittal view
        """
        self.rotate(fixed='sagittal')
