/*
ManageBacToTheFuture: ManageBac for Humans
Copyright (C) 2015 Sam Parkinson

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

require('babelify/polyfill');

window.server = 'http://0.0.0.0:5000'

import {AuthModel, AuthView} from './auth.js';
import {ClassesModel, ClassesView} from './classes.js';
import {ClassModel, ClassView} from './class.js';

var authM = new AuthModel();
var authV = new AuthView(authM);

var classesM = new ClassesModel(authM);
var classesV = new ClassesView(classesM);

var classM = new ClassModel(authM);
var classV = new ClassView(classM);

authM.on('new-auth-token', () => {
    classesM.update();
    classM.update();
});

window.onhashchange = () => {
    classM.trigger('hashchange');
    classesM.trigger('hashchange');
}
