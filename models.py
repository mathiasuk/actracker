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


class Car(object):
    '''
    Store information about car (position, player name, etc.)
    '''
    def __init__(self, name):
        self.position = 0
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

            car.position = self.ac.getCarState(0, self.acsys.CS.NormalizedSplinePosition)
        self.ac.console('%s' % ' '.join([c.position for c in self.cars]))
