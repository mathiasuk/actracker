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

import os

# colors:
RED = (1, 0, 0, 1)
GREEN = (0, 1, 0, 1)
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
        self.relative_position = 0  # Position on the lap compared to current
                                    # car, from -0.5 to 0.5
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


class Session(object):
    '''
    Represent a racing sessions.
    '''
    def __init__(self, ac=None, acsys=None):
        '''
        We pass ac and acsys so we don't have to import them here,
        that way we can test the code without AC modules
        '''
        self.ac = ac
        self.acsys = acsys
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
        self.best_lap = self.ac.getCarState(0, self.acsys.CS.BestLap)

        # Update cars
        for i in range(30):
            try:
                car = self.cars[i]
            except IndexError:
                name = self.ac.getDriverName(i)
                if name == -1:
                    # No such car
                    break
                car = Car(name)
                self.cars.append(car)

            car.spline_pos = self.ac.getCarState(i, self.acsys.CS.NormalizedSplinePosition)
            car.lap = self.ac.getCarState(i, self.acsys.CS.LapCount)
            # There is currently no way to know if another car is in the pit using the API
            # so we consider cars going slower than 20kph and close to start/finish line to
            # be in the pits
            car.in_pits = self.ac.getCarState(i, self.acsys.CS.SpeedKMH) < 20 and \
                (car.spline_pos < 0.05 or car.spline_pos > 0.95)

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
        Returns a list of sorted cars and the index of the player's car
        '''
        # TODO: handle different modes
        # Sort the cars by reverse relative position on the map
        cars = [ car for car in self.cars if not car.in_pits ]
        cars = sorted(cars, key=lambda car: car.relative_position, reverse=True)

        if len(cars) < 8:
            return cars, cars.index(self.player)
        else:
            i = cars.index(self.player)
            if i < 3:
                return cars[:7], i
            elif i > len(cars) - 3:
                return cars[-7:], i - len(cars) + 7
            else:
                return cars[i - 3:i + 4], 3

    def render(self):
        # Order cars
        cars, j = self._get_sorted_cars()
        for i, car in enumerate(cars):
            try:
                label = self.ui.labels['line_%d' % i]
                label_delta = self.ui.labels['line_%d_delta' % i]
            except KeyError:
                break

            text = '%2d %s' % (car.position, car.get_name())
            text_delta = ''
            color = WHITE

            if i == j:
                color = GREY_60
            elif car.delta < 0:
                text_delta = '%.1f' % (car.delta / 1000)
                if car.lap > self.player.lap:
                    color = RED
            elif car.delta > 0:
                if car.lap < self.player.lap:
                    color = GREEN
                text_delta = '+%.1f' % (car.delta / 1000)

            self.ac.setFontColor(label, *color)
            self.ac.setFontColor(label_delta, *color)
            self.ac.setText(label, text)
            self.ac.setText(label_delta, text_delta)
