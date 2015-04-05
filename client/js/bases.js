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

class Events {
    constructor (callbacks={}) {
        this.callbacks = callbacks;
    }
    
    on (name, callback) {
        if (this.callbacks[name] === undefined) {
            this.callbacks[name] = [];
        }
        
        this.callbacks[name].push(callback);
    }
    
    trigger (name, ...args) {
        if (this.callbacks[name] === undefined) {
            return;
        }
        
        for (let cb of this.callbacks[name]) {
            cb(...args);
        }
    }
}

export class View extends Events {
    constructor (model) {
        super();
        this.model = model;
    }
}

export class Model extends Events {}

export class DumbModel extends Model {
    constructor (data={}) {
        super();
        this.data = data;
    }
}
