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

import {Model, View} from './bases.js';

export function getCurrentClassID () {
    var match = (/\/classes\/([0-9]+)/).exec(window.location.hash);
    if (match !== null) {
        return parseInt(match[1]);
    }
    return null;
}

export class ClassesModel extends Model {
    constructor (auth) {
        super();

        this.on('hashchange', () => { this.hashChange() });
        this.auth = auth;
        this.list = [];
        this.update();
    }

    update () {
        this.list = [];

        var t = this.auth.token();
        if (t === null) {
            return;
        }

        var xhr = new XMLHttpRequest();
        xhr.open('GET', window.server + '/classes');
        xhr.onload = (event) => {
            if (xhr.status === 200) {
                this.list = JSON.parse(xhr.responseText).classes;
                this.hashChange();
                this.trigger('update');
            } else if (xhr.status === 403) {
                this.auth.tokenIsStale();
            }
        };
        xhr.setRequestHeader('X-Token', t);
        xhr.send();
    }

    hashChange () {
        var current = getCurrentClassID();
        for (var class_ of this.list) {
            class_.active = current === class_.id;
        }
        this.trigger('update');
    }
}

export class ClassesView extends View {
    constructor (model) {
        super(model);

        this.el = document.querySelector('#classesView');

        this.model.on('update', () => {
            this.render();
        });
    }

    render () {
        var html = `
        <ul class="classes">
            <h1>My Classes</h1>`;

        for (var class_ of this.model.list) {
            html += `
            <li class="${ class_.active? 'active' : ''}"
                data-id="${ class_.id }">
                <a href="#!/classes/${ class_.id }">
                    ${ class_.name }
                </a>
            </li>`;
        }

        html += `</ul>`;
        this.el.innerHTML = html;
    }
}
