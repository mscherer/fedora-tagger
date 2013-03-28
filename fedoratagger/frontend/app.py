# This file is a part of Fedora Tagger
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA  02110-1301  USA
#
# Refer to the README.rst and LICENSE files for full details of the license
# -*- coding: utf-8 -*-
"""The flask frontend app"""

import flask

import fedoratagger as ft
import fedoratagger.lib
from fedoratagger.lib import model as m
from fedoratagger.frontend.widgets.card import CardWidget


FRONTEND = flask.Blueprint(
    'frontend', __name__,
    url_prefix='/app',
    template_folder='templates',
    static_folder='static',
)

# TODO - yumdb
# TODO - notification toggling
# TODO - force _update from pkgdb and koji

# Some template strings for the 'details' view.
icon_template = "images/favicons/16_{serv}.png"
item_template = "<li><img src='{icon}'/>" + \
    "<a href='{url}' target='_blank'>{text}</a></li>"
services = [
    ('beefy', 'Community', "/packages/{name}"),
    ('pkgdb', 'Downloads', "https://admin.fedoraproject.org/community/" +
        "?package={name}#package_maintenance/details/downloads"),
    ('koji', 'Builds', "http://koji.fedoraproject.org/koji/search" +
        "?terms={name}&type=package&match=exact"),
    ('bodhi', 'Updates', "https://admin.fedoraproject.org/updates/{name}"),
    ('bugs', 'Bugs', "https://admin.fedoraproject.org/pkgdb/acls/bugs/{name}"),
    ('sources', 'Source', "http://pkgs.fedoraproject.org/gitweb/" +
        "?p={name}.git"),
]


@FRONTEND.route('/_heartbeat')
def heartbeat():
    """Fast heartbeat monitor so haproxy knows if we are runnining"""
    return "Lub-Dub"


# TODO -- determine wtf this is used for.. :/
@FRONTEND.route('/raw/<name>')
def raw(name):
    package = m.Package.by_name(ft.SESSION, name)

    html = "<html><body>"
    html += "<h1>" + package.name + "</h1>"
    html += "<h3>Tags/Votes/Voters</h3>"
    html += "<ul>"

    for tag in package.tags:
        html += "<li>"
        html += tag.label + "  " + str(tag.like - tag.dislike)
        html += "<ul>"
        for vote in tag.votes:
            html += "<li>" + vote.user.username + "</li>"
        html += "</ul>"
        html += "</li>"

    html += "</ul>"
    html += "</body></html>"
    return html


@FRONTEND.route('/card', defaults=dict(name=None))
@FRONTEND.route('/card/<name>')
def card(name):
    """ Handles the /card path.  Return a rendered CardWidget in HTML.

    If no name is specified, produce a widget for a package selected at
    random.

    If a name is specified, try to search for that package and render the
    associated CardWidget.
    """

    package = None
    if name and name != "undefined":
        package = m.Package.by_name(ft.SESSION, name)
    else:
        package = m.Package.random(ft.SESSION)

    w = CardWidget(package=package)
    return w.display()


@FRONTEND.route('/details', defaults=dict(name=None))
@FRONTEND.route('/details/<name>')
def details(name):
    """ Handles the /details path.

    Return a list of details for a package.
    """

    items = [
        item_template.format(
            icon=icon_template.format(serv=serv),
            url=url.format(name=name),
            text=text
        ) for serv, text, url in services
    ]
    return "<ul>" + "\n".join(items) + "</ul>"


@FRONTEND.route('/leaderboard', defaults=dict(N=10))
@FRONTEND.route('/leaderboard/<int:N>')
def leaderboard(N):
    """ Handles the /leaderboard path.

    Returns an HTML table of the top N users.
    """

    # TODO -- 'N' is unused here.  need to dig a tunnel through the .lib api
    users = fedoratagger.lib.leaderboard(ft.SESSION)
    import pprint
    pprint.pprint(users)

    keys = ['gravatar', 'name', 'score']
    row = "<tr>" + ''.join(["<td>{%s}</td>" % k for k in keys]) + "</tr>"
    rows = [
        row.format(**users[i+1]) for i in range(N)
    ]
    template = """
    <table class="leaderboard">
    <tr>
        <th colspan="2">User</th>
        <th>Score</th>
    </tr>
    {rows}
    </table>"""
    return template.format(rows="".join(rows))
