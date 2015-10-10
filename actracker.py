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

import ac
import acsys

import os
import sys
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'DLLs'))
from sim_info import info

app_size_x = 300
app_size_y = 200
session = None

# colors:
RED = (1, 0, 0, 1)
DARK_RED = (0.5, 0, 0, 1)
GREEN = (0, 1, 0, 1)
DARK_GREEN = (0, 0.5, 0, 1)
BLUE = (0, 0, 1, 1)
WHITE = (1, 1, 1, 1)
GREY_30 = (0.3, 0.3, 0.3, 1)
GREY_60 = (0.6, 0.6, 0.6, 1)


class Car(object):
    '''
    Store information about car (position, player name, etc.)
    '''
    def __init__(self, name):
        self.spline_pos = 0
        self.position = 0
        # Position on the lap compared to current car, from -0.5 to 0.5:
        self.relative_position = 0
        self.lap = 0
        self.delta = 0  # Delta to player's car
        self.name = name
        self.in_pits = False

    def get_name(self):
        '''
        Returns the player name, up to 40 characters
        '''
        if len(self.name) > 40:
            return self.name[:40]
        else:
            return self.name

    def status(self, player):
        '''
        Returns the status of the car compared to the player's
        '''
        if self == player:
            return 'player'

        if self.delta < 0:
            # Car is behind player
            if (self.lap > player.lap) or (self.lap == player.lap and self.spline_pos > player.spline_pos):
                return 'lapping-behind'
            elif (self.lap < player.lap) and not ((self.lap == (player.lap - 1)) and (self.spline_pos > player.spline_pos)):
                return 'lapped-behind'
            else:
                return 'racing-behind'
        elif self.delta > 0:
            # Car is ahead of player
            if (self.lap < player.lap) or (self.lap == player.lap and self.spline_pos < player.spline_pos):
                return 'lapped-ahead'
            elif self.lap > player.lap and not self.spline_pos < player.spline_pos:
                return 'lapping-ahead'
            else:
                return 'racing-ahead'
        else:
            # This should only happen on the first lap, or when joining
            # mid-race without booking
            return 'none'


class Session(object):
    '''
    Represent a racing sessions.
    '''
    def __init__(self):
        '''
        '''
        self.app_path = os.path.dirname(os.path.realpath(__file__))
        self.ui = None
        self.app_size_x = 0
        self.app_size_y = 0
        self.cars = []
        self.player = None  # Record the player's car
        self.best_lap = 0

    def update_data(self, deltaT):
        '''
        Called by acUpdate, updates internal data
        '''
        self.best_lap = ac.getCarState(0, acsys.CS.BestLap)

        # Update cars
        for i in range(30):
            try:
                car = self.cars[i]
            except IndexError:
                name = ac.getDriverName(i)
                if name == -1:
                    # No such car
                    break
                car = Car(name)
                self.cars.append(car)

            # The name can change if in no-booking mode
            car.name = ac.getDriverName(i)

            car.spline_pos = ac.getCarState(i, acsys.CS.NormalizedSplinePosition)
            car.lap = ac.getCarState(i, acsys.CS.LapCount)
            # There is currently no way to know if another car is in the pit using the API
            # so we consider cars going slower than 20kph and close to start/finish line to
            # be in the pits
            car.in_pits = ac.getCarState(i, acsys.CS.SpeedKMH) < 20 and \
                (car.spline_pos < 0.1 or car.spline_pos > 0.9)

            if i == 0:
                self.player = car
            else:
                car.relative_position = car.spline_pos - self.player.spline_pos
                if car.relative_position > 0.5:
                    car.relative_position -= 1
                if car.relative_position < -0.5:
                    car.relative_position += 1
                car.delta = car.relative_position * self.best_lap

        # Update the cars' race position:
        for i, car in enumerate(sorted(self.cars, key=lambda car: (-car.lap, -car.spline_pos))):
            car.position = i + 1

    def _get_sorted_cars(self):
        '''
        Returns a list of sorted cars
        '''
        # TODO: handle different modes
        # Sort the cars by reverse relative position on the map
        cars = [ car for car in self.cars if not car.in_pits ]
        cars = sorted(cars, key=lambda car: car.relative_position, reverse=True)

        try:
            if len(cars) < 8:
                return cars
            else:
                i = cars.index(self.player)
                if i < 3:
                    return cars[:7]
                elif i > len(cars) - 3:
                    return cars[-7:]
                else:
                    return cars[i - 3:i + 4]
        except ValueError:
            # Player is not in the listed cars, this means that he is in the pits
            return None

    def update_ui(self):
        # Order cars
        cars = self._get_sorted_cars()

        # Clear labels
        for dummy, label in self.ui.labels.items():
            ac.setText(label, '')

        if cars is None:
            # In pits
            label = self.ui.labels['line_0']
            ac.setFontColor(label, *WHITE)
            ac.setText(label, 'In Pits')
            return

        for i, car in enumerate(cars):
            try:
                label = self.ui.labels['line_%d' % i]
                label_delta = self.ui.labels['line_%d_delta' % i]
            except KeyError:
                break

            text = '%2d (%d) %s' % (car.position, car.lap, car.get_name())
            text_delta = ''
            color = WHITE

            status = car.status(self.player)

            if status == 'player':
                color = GREY_60
            elif status == 'lapping-behind':
                text_delta = '%.1f' % (car.delta / 1000)
                color = RED
            elif status == 'lapped-behind':
                text_delta = '%.1f' % (car.delta / 1000)
                color = DARK_GREEN
            elif status == 'lapped-ahead':
                text_delta = '+%.1f' % (car.delta / 1000)
                color = GREEN
            elif status == 'lapping-ahead':
                text_delta = '+%.1f' % (car.delta / 1000)
                color = DARK_RED
            elif status == 'racing-behind':
                text_delta = '%.1f' % (car.delta / 1000)
            elif status == 'racing-ahead':
                text_delta = '+%.1f' % (car.delta / 1000)

            if info.graphics.session != 2 and color != GREY_60:
                # Only use colors in race mode
                color = WHITE

            ac.setFontColor(label, *color)
            ac.setFontColor(label_delta, *color)
            ac.setText(label, text)
            ac.setText(label_delta, text_delta)


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
    global session  # pylint: disable=W0603

    # Create session object
    session = Session()
    session.app_size_x = app_size_x
    session.app_size_y = app_size_y

    # Initialise UI:
    ui = UI(session)
    session.ui = ui

    return "Tracker"


def acUpdate(deltaT):
    global session  # pylint: disable=W0602

    try:
        session.update_data(deltaT)
        session.update_ui()
    except:  # pylint: disable=W0702
        exc_type, exc_value, exc_traceback = sys.exc_info()
        session.ac.console('ACTracker Error (logged to file)')
        session.ac.log(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
