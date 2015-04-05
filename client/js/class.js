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

var commonmark = require('commonmark');
import {Model, View, DumbModel} from './bases.js';
import {getCurrentClassID} from './classes.js';

function markdownify (text) {
    if (text === undefined || text === null || text === '') {
        return '';
    }

    var reader = new commonmark.Parser();
    var writer = new commonmark.HtmlRenderer();
    // Keep all `\n`s!!!
    var parsed = reader.parse(text.replace(/\n/g, '\n\n'));
    return writer.render(parsed);
}

export class ClassModel extends Model {
    constructor (auth) {
        super();

        this.auth = auth;
        this.list = [];
        this.id = null;
        this.loading = false;
        this.update();

        this.on('hashchange', () => { this.processURL() });
        this.processURL();
    }

    processURL () {
        if (getCurrentClassID() !== null) {
            this.viewClass(getCurrentClassID());
        } 
    }

    update () {
        if (this.id === null) {
            return;
        }
        this.list = [];

        var t = this.auth.token();
        if (t === null) {
            return;
        }

        this.loading = true;
        this.trigger('update');

        // Used to cancel load if user selects another thing
        var loadingID = this.id;

        var xhr = new XMLHttpRequest();
        xhr.open('GET', `${ window.server }/classes/${ loadingID }`);
        xhr.onload = (event) => {
            if (this.id !== loadingID) {
                return;  // REJECTED!
            }

            if (xhr.status === 200) {
                this.list = JSON.parse(xhr.responseText).items;
            } else if (xhr.status === 403) {
                this.auth.tokenIsStale();
            }

            this.loading = false;
            this.trigger('update');
        };
        xhr.setRequestHeader('X-Token', t);
        xhr.send();
    }

    viewClass (id) {
        this.id = id;
        this.update();
    }
}

export class ClassView extends View {
    constructor (model) {
        super(model);

        this.el = document.querySelector('#classView');
        this.itemCache = {};

        this.model.on('update', () => {
            this.render();
        });
        this.render();
    }

    render () {
        var ul = document.createElement('ul');

        if (this.model.loading) {
            var e = document.createElement('li');
            e.innerHTML = `
            <i class="fa fa-refresh fa-3 fa-spin"></i>
            Loading...`;
            ul.appendChild(e);
        }

        for (var item of this.model.list) {
            ul.appendChild(this.getItemElement(item));
        }

        this.el.innerHTML = '';
        this.el.appendChild(ul);
    }

    getItemElement (data) {
        var cacheKey = `${ data.__name__ }:${ data.id || data.url }`;
        if (this.itemCache[cacheKey] !== undefined) {
            return this.itemCache[cacheKey].render();
        }

        switch (data.__name__) {
            case 'Message':
                var m = new MessageModel(this.model.auth, data);
                var v = new MessageView(m);
                break;
            case 'Event':
                var m = new EventModel(data);
                var v = new EventView(m);
                break;
            case 'File':
                var m = new FileModel(data);
                var v = new FileView(m);
                break;
            case 'Folder':
                var m = new FolderModel(data);
                var v = new FolderView(m);
                break;
            default:
                var e = document.createElement('li');
                e.innerHTML = JSON.stringify(data);
                return e;
        }

        m.on('update', () => {
            this.render();
        });

        this.itemCache[cacheKey] = v;
        return v.render();
    }
}

class MessageModel extends DumbModel {
    constructor (auth, data) {
        super(data);
        this.auth = auth;
    }

    postComment (body) {
        var t = this.auth.token();
        var classID = getCurrentClassID();
        if (t === null || classID === null) {
            return;
        }

        var data = new FormData();
        data.append('body', body);

        var xhr = new XMLHttpRequest();
        xhr.open(
            'POST', `${ window.server }/classes/${ classID }/messages/` + 
            `${ this.data.id }/comments`, true);
        xhr.onload = (event) => {
            if (xhr.status === 200) {
                this.update();
            } else if (xhr.status === 403) {
                this.auth.tokenIsStale();
            }
        };
        xhr.setRequestHeader('X-Token', t);
        xhr.send(data);
    }

    update () {
        var t = this.auth.token();
        var classID = getCurrentClassID();
        if (t === null || classID === null) {
            return;
        }

        var xhr = new XMLHttpRequest();
        xhr.open(
            'GET', `${ window.server }/classes/${ classID }/messages/` + 
            `${ this.data.id }`, true);
        xhr.onload = (event) => {
            if (xhr.status === 200) {
                this.data = JSON.parse(xhr.responseText).message;
                this.trigger('update');
            } else if (xhr.status === 403) {
                this.auth.tokenIsStale();
            }
        };
        xhr.setRequestHeader('X-Token', t);
        xhr.send();
    }
}

class MessageView extends View {
    constructor (model) {
        super(model);
    }

    render () {
        var el = document.createElement('li');
        el.classList.add('message-view');

        var d = this.model.data;
        // TODO: Post Comments Model
        var h = `
        <div class="post original-post">
            <div class="post-split">
                <img class="avatar" src="${ d.avatar }" />
                <div>
                    <h1>${ d.title }</h1>
                    <p class="subtitle">By ${ d.by } at ${ d.time }</p>
                </div>
            </div>
            <div class="post-contents">
                ${ markdownify(d.text) }
            </div>
        </div>
        <div class="comments">`;
        for (var c of d.comments) {
            h += `
            <div class="post">
                <div class="post-split">
                    <img class="avatar" src="${ c.avatar }" />
                    <div>
                        <p class="subtitle">
                            Reply by ${ c.by } at ${ c.time }</p>
                        <div class="post-contents">
                            ${ markdownify(c.text) }
                        </div>
                    </div>
                </div>
            </div>`;
        }
        h += `
            <div class="post-new">
                <textarea id="contents"
                          placeholder="Reply to the topic..."></textarea>
                <button id="submit" class="primary">Post</button>
            </div>
        </div>`;
        el.innerHTML = h;

        el.querySelector('#submit').addEventListener('click', () => {
            el.classList.add('loading');
            this.model.postComment(el.querySelector('textarea').value);
        });

        return el;
    }
}

class EventModel extends DumbModel {}

const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
                'August', 'September', 'October', 'November', 'December'];

class EventView extends View {
    render () {
        var el = document.createElement('li');
        el.classList.add('events-view');

        var d = this.model.data;
        var time = new Date(d.time);
        // TODO: End
        el.innerHTML = `
        <div class="time-date-col">
            <div class="bg-colored"
                 style="background: ${ d.bg_color }; color: ${ d.fg_color };">
                <p class="date">
                    <i class="fa fa-calendar-o
                              cal-number cal-number-${ time.getDate() }"></i>
                <p class="month">${ MONTHS[time.getMonth()] }</p>
                <p class="category"><b>${ d.category }</b></p>
            </div>
        </div>
        <div class="info-col">
            <h1>${ d.title }</h1>
            <p class="subtitle">${ d.time } at ${ d.where }</p>
            ${ markdownify(d.description) }
        </div>`;

        return el;
    }
}

const FILE_ICONS = {
    'file-pdf-o': ['pdf'],
    'file-text-o': ['txt', 'text', 'md', 'markdown'],
    'file-code-o': ['html', 'htm', 'py', 'js', 'css', 'c', 'go'],
    'file-word-o': ['doc', 'docx', 'odt', 'abiword'],
    'file-excel-o': ['xls', 'xlsx', 'gnumric', 'ods'],
    'file-powerpoint-o': ['ppt', 'pptx', 'odp'],
    'file-image-o': ['png', 'jpg', 'jpeg', 'gif', 'svg', 'xcf', 'psd'],
    'file-archive-o': ['tar', 'bz2', 'bz', 'gz', 'zip'],
    'file-audio-o': ['mp3', 'wav', 'oga'],
    'file-video-o': ['ogg', 'ogv', 'mpeg', 'webm', 'mp4', '3gp']
}

function getFileIconFromName (name) {
    var parts = name.split('.');
    var ext = parts[parts.length-1].toLowerCase();

    for (var icon in FILE_ICONS) {
        if (FILE_ICONS[icon].indexOf(ext) !== -1) {
            return icon;
        }
    }

    return 'file-o';
}

class FileModel extends DumbModel {}

class FileView extends View {
    render () {
        var el = document.createElement('li');
        el.classList.add('file-view');

        var d = this.model.data;
        el.innerHTML = `
        <h1>
            <i class="fa fa-${ getFileIconFromName(d.name) }"></i>
            <a href="${ d.url }">${ d.name }</a>
        </h1>
        <p class="subtitle">${ d.size } file, by ${ d.by } at ${ d.time }</p>`;

        return el;
    }
}

class FolderModel extends DumbModel {}

class FolderView extends View {
    render () {
        var el = document.createElement('li');
        el.classList.add('folder-view');

        var d = this.model.data;
        var h = `
        <h1><i class="fa fa-folder-open-o"></i>${ d.name }</h1>
        <p class="subtitle">Last modified at ${ d.time }</p>
        <ul class="fa-ul">`

        for (var f of d.files) {
            h += `
            <li>
                <i class="fa fa-${ getFileIconFromName(f.name) } fa-li"></i>
                <a href="${ f.url }">${ f.name }</a>
                <span class="subtitle">
                    ${ f.size } file, by ${ f.by } at ${ f.time }
                </span>
            </li>`;
        }
        h += `
        </ul>`;

        el.innerHTML = h;
        return el;
    }
}
