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


class Car(object):
    '''
    Store information about car (position, player name, etc.)
    '''
    def __init__(self, name):
        self.position = 0
        self.relative_position = 0  # Position on the lap compared to current
                                    # car, from -0.5 to 0.5
        self.name = name


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

    def update_data(self, deltaT):
        '''
        Called by acUpdate, updates internal data
        '''
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

            car.position = self.ac.getCarState(i, self.acsys.CS.NormalizedSplinePosition)
            if i > 0:
                car.relative_position = car.position - self.cars[0].position

    def _get_sorted_cars(self):
        '''
        Returns a list of sorted cars and the index of the player's car
        '''
        # TODO: handle different modes
        # Sort the cars by reverse relative position on the map
        cars = sorted(self.cars, key=lambda car: car.relative_position, reverse=True)

        if len(cars) < 8:
            return cars, cars.index(self.cars[0])
        else:
            i = cars.index(self.cars[0])
            if i < 3:
                return cars[:7], i
            elif i > len(cars) - 3:
                return cars[-7:], i - len(cars) + 7
            else:
                return cars[i - 3:i + 3], 3

    def render(self):
        # Order cars
        cars, j = self._get_sorted_cars()
        for i, car in enumerate(cars):
            try:
                label = self.ui.labels['line_%d' % i]
            except KeyError:
                break
            text = '%.3f %s' % (car.position, car.name)
            if i == j:
                text += ' *'
            self.ac.setText(label, text)
