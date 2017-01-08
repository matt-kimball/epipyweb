/*global $, document, location*/

'use strict';


/*  Get argument from the query in the page URL  */
function get_query_argument(name) {
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


/*  Fill the expanded connection list from the JSON DNS query list  */
function fill_expanded_connections(more_div, queries) {
    var query,
        connection_div,
        time,
        i;

    for (i = 0; i < queries.length; i += 1) {
        query = queries[i];

        more_div.append($("<div>", {
            "class": "additional-connection-value"
        }).text(query.value));

        time = query.time.replace('T', ' ');
        more_div.append($("<div>", {
            "class": "additional-connection-time"
        }).text(time));
    }
}


/*  Expand a "X more connections" list by requesting the DNS queries  */
function expand_connections(more_div, id) {
    var url,
        additional_queries;

    url = "/q/groupqueries?id=" + id;

    /*jslint unparam: true */
    $.getJSON(url).done(function (response) {
        more_div.children().remove();

        additional_queries = response.queries.slice(1);
        fill_expanded_connections(more_div, additional_queries);
    }).fail(function (xhr, status, error) {
        var err_str;

        err_str = status + ": " + error;

        more_div.children().remove();
        more_div.text(err_str);
    });
}


/*  Append a row of connection info to the connections list  */
function append_connection_row(id, value, time, host, query_count) {
    var info_div,
        more_div,
        text;

    $("<div>", {
        "class": "connection-value",
    }).text(value).appendTo("#connections");

    info_div = $("<div>", {
        "class": "connection-query-info",
    }).appendTo("#connections");

    info_div.append($("<span>", {
        "class": "connection-time",
    }).text(time));

    info_div.append($("<span>", {
        "class": "connection-host",
    }).text("from " + host));

    if (query_count > 1) {
        text = (query_count - 1) + " more connections \u00bb";

        more_div = $("<div>", {
            "class": "more-connections",
        }).appendTo("#connections");

        /*jslint unparam: true */
        more_div.append($("<a>", {
            "class": "connection-count-link",
        }).text(text).click(function (e) {
            expand_connections(more_div, id);
        }));
    }

    $("<div>", {
        "class": "connection-separator",
    }).appendTo("#connections");
}


/*  Append the "Previous Page" and "Next Page" links  */
function append_page_links(first_id, last_id) {
    $("<a>", {
        "class": "previous-page-link",
        "href": "/?after=" + first_id,
    }).text("\u00ab Previous Page").appendTo("#page-links");

    $("<a>", {
        "class": "next-page-link",
        "href": "/?before=" + last_id,
    }).text("Next Page \u00bb").appendTo("#page-links");
}


/*  Fill the connections list from the JSON list of querygroups  */
function fill_connections(groups) {
    var group,
        time,
        first_id,
        last_id,
        i;

    for (i = 0; i < groups.length; i += 1) {
        group = groups[i];

        time = group.time;
        if (time !== undefined) {
            time = time.replace('T', ' ');
        }

        append_connection_row(
            group.id,
            group.value,
            time,
            group.host,
            group.query_count
        );
    }

    if (groups.length > 0) {
        first_id = groups[0].id;
        last_id = groups[groups.length - 1].id;

        if (first_id !== undefined && last_id !== undefined) {
            append_page_links(first_id, last_id);
        }
    }
}


/*  Request JSON with the connections and fill the page with the results  */
function fill_connections_from_url(url) {
    /*jslint unparam: true */
    $.getJSON(url).done(function (response) {
        fill_connections(response.groups);
    }).fail(function (xhr, status, error) {
        var err_str;

        err_str = status + ": " + error;
        $("<div>").text(err_str).appendTo("#connections");
    });
}


/*  Construct the dynamic page content  */
function on_ready() {
    var before_id,
        after_id,
        dnsquery_url;

    dnsquery_url = "/q/dnsquerygroup?count=25";

    before_id = get_query_argument('before');
    after_id = get_query_argument('after');

    if (before_id !== undefined) {
        dnsquery_url += "&before=" + before_id;
    } else if (after_id !== undefined) {
        dnsquery_url += "&after=" + after_id;
    }

    fill_connections_from_url(dnsquery_url);
}


$(document).ready(on_ready);
