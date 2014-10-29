# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# Copyright (C) 2014 - Mathias Andre

from tmodels import Session

import ac
import acsys

import os
import sys
import traceback

app_size_x = 300
app_size_y = 200
session = None


class UI(object):
    '''
    Object that deals with everything related to the app's widget
    '''
    def __init__(self, session_):
        self.session = session_
        self.widget = None
        self.labels = {}
        self.chkboxes = {}
        self.buttons = {}

        self._create_widget()
        self._create_labels()

    def _create_widget(self):
        self.widget = ac.newApp('ACTracker')
        ac.setSize(self.widget, app_size_x, app_size_y)
        ac.setBackgroundOpacity(self.widget, 0.75)
        ac.addRenderCallback(self.widget, onFormRender)

    def _create_label(self, name, text, x, y):
        label = ac.addLabel(self.widget, name)
        ac.setText(label, text)
        ac.setPosition(label, x, y)
        self.labels[name] = label

    def _create_checkbox(self, name, text, x, y, size_x, size_y, callback):
        checkbox = ac.addCheckBox(self.widget, text)
        ac.setPosition(checkbox, x, y)
        ac.setSize(checkbox, size_x, size_y)
        ac.addOnCheckBoxChanged(checkbox, callback)
        self.chkboxes[name] = checkbox

    def _create_button(self, name, x, y, size_x, size_y, callback,
                       border=0, opacity=0, texture=None):
        button = ac.addButton(self.widget, '')
        ac.setPosition(button, x, y)
        ac.setSize(button, size_x, size_y)
        ac.addOnClickedListener(button, callback)
        ac.drawBorder(button, border)
        ac.setBackgroundOpacity(button, opacity)
        if texture:
            texture = os.path.join(session.app_path, 'img', texture)
            ac.setBackgroundTexture(button, texture)
        self.buttons[name] = button

    def _create_labels(self):
        y = 30
        y_space = 20

        for i in range(7):
            self._create_label('line_%d' % i, '', 10, y)
            self._create_label('line_%d_delta' % i, '', 250, y)
            y += y_space
#        self._create_label('line_0', '', 10, 30)
#        self._create_label('line_1', '', 10, 50)
#        self._create_label('line_2', '', 10, 70)
#        self._create_label('line_3', '', 10, 90)
#        self._create_label('line_4', '', 10, 110)
#        self._create_label('line_5', '', 10, 130)
#        self._create_label('line_6', '', 10, 150)
#        self._create_label('line_7', '', 10, 170)
#        self._create_label('line_8', '', 10, 190)
#        self._create_label('line_9', '', 10, 210)
        # self._create_label('current_speed', 'Speed', 10, 30)
        # self._create_label('best_speed', 'Best', 10, 50)
        # self._create_label('current_speed_val', '', 60, 30)
        # self._create_label('best_speed_val', '', 60, 50)
        # self._create_label('best_lap_time_val', '', 5, 175)


def acMain(ac_version):
    global session

    # Create session object
    session = Session(ac, acsys)
    session.app_size_x = app_size_x
    session.app_size_y = app_size_y

    # Initialise UI:
    ui = UI(session)
    session.ui = ui

    return "Tracker"


def acUpdate(deltaT):
    global session

    try:
        session.update_data(deltaT)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        session.ac.console('ACTracker Error (logged to file)')
        session.ac.log(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))


def onFormRender(deltaT):
    global session

    try:
        session.render()
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        session.ac.console('ACTracker Error (logged to file)')
        session.ac.log(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
