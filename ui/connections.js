/*global $, get_query_argument, decode_query_argument, document, location*/
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


/*  Find the index of a substring, with case sensitivity  */
function case_insensitive_index(
    str,
    substr
) {
    return str.toUpperCase().indexOf(substr.toUpperCase());
}


/*
    Append a text value, highlighting a substring which matches the
    search text.
*/
function append_highlighted_value(
    element,
    search_value,
    value
) {
    var search_index,
        pre_text,
        found_text,
        post_text;

    if (search_value !== undefined) {
        search_index = case_insensitive_index(value, search_value);
    } else {
        search_index = -1;
    }

    if (search_index >= 0) {
        pre_text = value.substr(0, search_index);
        found_text = value.substr(search_index, search_value.length);
        post_text = value.substr(search_index + search_value.length);

        if (pre_text.length > 0) {
            element.append($("<span>", {
                "class": "connection-value-text"
            }).text(pre_text));
        }

        element.append($("<span>", {
            "class": "connection-value-text-highlight"
        }).text(found_text));

        if (post_text.length > 0) {
            element.append($("<span>", {
                "class": "connection-value-text"
            }).text(post_text));
        }
    } else {
        element.append($("<span>", {
            "class": "connection-value-text"
        }).text(value));
    }
}


/*  Convert an integer to a string with leading zeros  */
function zero_pad(
    value,
    digits
) {
    var str;

    str = String(value);
    while (str.length < digits) {
        str = '0' + str;
    }

    return str;
}


/*  Convert a UTC time string to a display string in the local timezone  */
function format_local_time(
    utc_time
) {
    var now,
        date,
        utc_time_regex,
        regex_match;

    now = new Date();
    utc_time_regex = /([0-9]+)-([0-9]+)-([0-9]+)T([0-9]+):([0-9]+):([0-9]+)/;
    regex_match = utc_time.match(utc_time_regex);
    date = new Date(
        regex_match[1],
        regex_match[2],
        regex_match[3],
        regex_match[4],
        regex_match[5] - now.getTimezoneOffset(),
        regex_match[6]
    );

    return String(date.getFullYear()) +
        '-' + zero_pad(date.getMonth(), 2) +
        '-' + zero_pad(date.getDate(), 2) +
        ' ' + zero_pad(date.getHours(), 2) +
        ':' + zero_pad(date.getMinutes(), 2) +
        ':' + zero_pad(date.getSeconds(), 2);
}


/*
    Create an object for managing retrieving additional connections
    in a connection group, either in response to a user clicking on 
    "more connections" or for retrieving search results automatically.
*/
function create_connection_retriever(
    connection_div,
    group_id,
    search_value
) {
    var self,
        full_expand = false,
        retrieve_in_progress = false;

    /*  Fill the expanded connection list from the JSON DNS query list  */
    function fill_expanded_connections(
        queries
    ) {
        var query,
            search_index,
            value_div,
            time,
            show_connection,
            skipped_connection_count,
            i;

        skipped_connection_count = 0;
        for (i = 0; i < queries.length; i += 1) {
            query = queries[i];
            show_connection = true;

            if (!full_expand) {
                search_index = case_insensitive_index(
                    query.value,
                    search_value
                );

                if (search_index === -1) {
                    show_connection = false;
                    skipped_connection_count += 1;
                }
            }

            if (show_connection) {
                value_div = $("<div>", {
                    "class": "additional-connection-value"
                });

                append_highlighted_value(
                    value_div,
                    search_value,
                    query.value
                );
                connection_div.append(value_div);

                time = format_local_time(query.time);
                connection_div.append($("<div>", {
                    "class": "additional-connection-time"
                }).text(time));
            }
        }

        if (skipped_connection_count > 0) {
            self.append_more_link(skipped_connection_count);
        }
    }

    /*  Retrieve the JSON with the additional connections in the group  */
    function get_connections() {
        var url,
            additional_queries;

        if (retrieve_in_progress) {
            return;
        }

        url = "/q/groupqueries?id=" + group_id;
        retrieve_in_progress = true;

        /*jslint unparam: true */
        $.getJSON(url).done(function (response) {
            retrieve_in_progress = false;

            connection_div.empty();

            additional_queries = response.queries.slice(1);
            fill_expanded_connections(additional_queries);
        }).fail(function (xhr, status, error) {
            var err_str;

            retrieve_in_progress = false;

            err_str = status + ": " + error;

            connection_div.empty();
            connection_div.text(err_str);
        });
    }

    /*  Expand a "X more connections" list by requesting the DNS queries  */
    function expand_connections() {
        full_expand = true;

        get_connections();
    }

    /*
        Highlight the search text in the additional connections, without
        a full expansion.
    */
    function highlight_search_text() {
        get_connections();
    }

    /*  Append the link with "X more connections" text  */
    function append_more_link(additional_count) {
        var text;

        text = additional_count + " more connections \u00bb";

        /*jslint unparam: true */
        connection_div.append($("<a>", {
            "class": "connection-count-link"
        }).text(text).click(function (e) {
            expand_connections();
        }));
    }

    self = {
        "append_more_link": append_more_link,
        "expand_connections": expand_connections,
        "highlight_search_text": highlight_search_text
    };

    return self;
}


/*  Append a row of connection info to the connections list  */
function append_connection_row(
    search_value,
    id,
    value,
    time,
    host,
    query_count
) {
    var connection_retriever,
        value_div,
        info_div,
        more_div;

    value_div = $("<div>", {
        "class": "connection-value"
    }).appendTo("#connections");

    append_highlighted_value(value_div, search_value, value);

    info_div = $("<div>", {
        "class": "connection-query-info"
    }).appendTo("#connections");

    info_div.append($("<span>", {
        "class": "connection-time"
    }).text(time));

    info_div.append($("<span>", {
        "class": "connection-host"
    }).text(" from " + host));

    if (query_count > 1) {
        more_div = $("<div>", {
            "class": "more-connections"
        }).appendTo("#connections");

        connection_retriever = create_connection_retriever(
            more_div,
            id,
            search_value
        );

        connection_retriever.append_more_link(query_count - 1);

        if (search_value !== undefined) {
            connection_retriever.highlight_search_text();
        }
    }

    $("<div>", {
        "class": "connection-separator"
    }).appendTo("#connections");
}


/*  Append the "Previous Page" and "Next Page" links  */
function append_page_links(
    previous_page_present,
    next_page_present,
    first_id,
    last_id
) {
    var search_value,
        href;

    search_value = get_query_argument("search");
    if (search_value !== undefined) {
        href = '/connections.html?search=' + search_value + '&';
    } else {
        href = '/connections.html?';
    }

    if (previous_page_present) {
        $("<a>", {
            "class": "content-page-link",
            "href": href + "after=" + first_id
        }).text("\u00ab Previous Page").appendTo("#page-links");
    }

    if (previous_page_present && next_page_present) {
        $("<span>", {
            "class": "page-link-gap"
        }).appendTo("#page-links");
    }

    if (next_page_present) {
        $("<a>", {
            "class": "content-page-link",
            "href": href + "before=" + last_id
        }).text("Next Page \u00bb").appendTo("#page-links");
    }
}


/*  Fill the connections list from the JSON list of querygroups  */
function fill_connections(
    response
) {
    var groups,
        group,
        search_value,
        time,
        first_id,
        last_id,
        i;

    groups = response.groups;

    if (groups.length === 0) {
        $("#page-links").text("No connections found");
        return;
    }

    search_value = decode_query_argument("search");

    for (i = 0; i < groups.length; i += 1) {
        group = groups[i];

        time = group.time;
        if (time !== undefined) {
            time = format_local_time(time);
        }

        append_connection_row(
            search_value,
            group.id,
            group.value,
            time,
            group.host,
            group.query_count
        );
    }

    first_id = groups[0].id;
    last_id = groups[groups.length - 1].id;

    if (first_id !== undefined && last_id !== undefined) {
        append_page_links(
            response.previous_page_present,
            response.next_page_present,
            first_id,
            last_id
        );
    }
}


/*  Request JSON with the connections and fill the page with the results  */
function fill_connections_from_url(
    url
) {
    $("#connections").text("Looking up connections...");

    /*jslint unparam: true */
    $.getJSON(url).done(function (response) {
        $("#connections").empty();

        if (response.error !== undefined) {
            $("#connections").text(response.error);
        } else if (response.groups !== undefined) {
            fill_connections(response);
        }
    }).fail(function (xhr, status, error) {
        var err_str;

        $("#connections").empty();

        err_str = status + ": " + error;
        $("<div>").text(err_str).appendTo("#connections");
    });
}


/*  When the document loads, retrieve and display DNS connections  */
function show_connections() {
    $(document).ready(function () {
        var dnsquery_url;

        dnsquery_url = "/q/dnsquerygroup?count=25";
        if (location.search.length > 0) {
            dnsquery_url += '&' + location.search.substr(1);
        }

        fill_connections_from_url(dnsquery_url);
    });
}
