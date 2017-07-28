/*global $, location*/
/*
    epipyweb - Epipylon web user interface
    Copyright (C) 2017  Matt Kimball

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
*/

'use strict';


/*  Get argument from the query in the page URL  */
function get_query_argument(
    name
) {
    var query = location.search.substr(1),
        args = query.split("&"),
        key_value,
        i;

    for (i = 0; i < args.length; i += 1) {
        key_value = args[i].split("=");

        if (key_value[0] === name) {
            return key_value[1];
        }
    }
}


/*  Search for a query argument and decode the URI escaped characters  */
function decode_query_argument(
    name
) {
    var value;

    value = get_query_argument(name);
    if (value !== undefined) {
        return decodeURIComponent(value);
    }
}


/*jslint unparam: true */
function on_search(
    event
) {
    var new_search_value;

    new_search_value = $("#search-input").get(0).value;

    if (new_search_value.length) {
        location.href = "/connections.html?search=" + new_search_value;
    } else {
        location.href = "/connections.html";
    }
}


/*  Attach event handlers to UI elements, such as the search bar  */
function attach_ui_events() {
    var search_value;

    search_value = decode_query_argument("search");
    if (search_value !== undefined) {
        $("#search-input").get(0).value = search_value;
    }

    $("#search-input").keydown(function (event) {
        if (event.keyCode === '\r'.charCodeAt(0)) {
            on_search();
        }
    }).focus();

    $("#search-button").click(on_search);
}

/*  Don't cache JSON queries  */
$.ajaxSetup({ cache: false });
