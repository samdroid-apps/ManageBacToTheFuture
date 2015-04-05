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

export class AuthModel extends Model {
    constructor () {
        super();

        if (localStorage.token !== undefined) {
            this._token = localStorage.token;
        }
    }

    token () {
        if (this._token !== undefined) {
            return this._token;
        } else {
            this.trigger('need-login');
            return null;
        }
    }
    
    tryLogin (username, password) {
        var data = new FormData();
        data.append('username', username);
        data.append('password', password);

        var xhr = new XMLHttpRequest();
        xhr.open('POST', window.server + '/login', true);
        xhr.onload = (event) => {
            if (xhr.status === 200) {
                this._token = JSON.parse(xhr.responseText).token;
                localStorage.token = this._token;
                this.trigger('new-auth-token');
            } else if (xhr.status === 403) {
                this.trigger('username-password-rejected');
            }
        };
        xhr.send(data);
    }

    tokenIsStale () {
        this._token = undefined;
        localStorage.token = undefined;
        this.trigger('need-login');
    }
}

export class AuthView extends View {
    constructor (model) {
        super(model);

        this.visible = false;
        this.el = document.querySelector('#authView');

        this.model.on('need-login', () => {
            this.visible = true;
            this.render();
        });

        this.model.on('username-password-rejected', () => {
            this.visible = true;
            this.render({rejected: true});
        });

        this.model.on('new-auth-token', () => {
            this.visible = false;
            this.render();
        });
    }
    
    render (opts={}) {
        if (!this.visible) {
            this.el.innerHTML = '';
            return;
        }
        
        this.el.innerHTML = `
        <div class="${ opts.loading ? 'loading' : '' }">
            <div class="header">
                <p><i class="fa fa-5x fa-lock"></i><p>
                <p><b>Sign in with ManageBac</b></p>
            </div>
            ${ opts.rejected ? `<p class="error-banner">
               Username or password rejected</p>` : '' }
            <input id="email" type="email" placeholder="Email">
            <input id="password" type="password" placeholder="Password">
            <button id="submit" class="primary">Login</button>
        </div>`;

        this.el.querySelector('#submit').addEventListener('click', () => {
            this.model.tryLogin(
                this.el.querySelector('#email').value,
                this.el.querySelector('#password').value);
            this.render({loading: true});
        });
    }
}
