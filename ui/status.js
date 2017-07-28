/*global $*/
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


/*  Display the Epipylon device configuration, and report a DHCP conflict  */
function display_status(
    status
) {
    var device_url,
        log_size_str,
        space_free_str;

    if (status.network.dhcp_server) {
        $("#dhcp-interference").css("display", "block");
        $("#dhcp-device-address").text(status.network.dhcp_server);

        device_url = "http://" + status.network.dhcp_server + "/";
        $("#dhcp-device-link").attr("href", device_url);
    } else {
        $("#normal-operation").css("display", "block");
    }

    $("#network-addresses-text").css("display", "block");
    $("#network-addresses").css("display", "block");

    $("#router-address").text(status.network.router_address);
    $("#subnet-mask").text(status.network.subnet_mask);
    $("#dns-addresses").text(status.network.dns_addresses);
    $("#device-address").text(status.network.device_address);

    $("#disk-space-text").css("display", "block");
    $("#disk-space").css("display", "block");

    log_size_str = Math.round(status.disk.log_size / 1024 / 1024) + " MB";
    space_free_str = Math.round(status.disk.space_free / 1024 / 1024) + " MB";

    $("#log-size").text(log_size_str);
    $("#space-free").text(space_free_str);
}


/*  Retrieve the device network status, and display the results  */
function check_status() {
    $("body").css("cursor", "progress");

    /*jslint unparam: true */
    $.getJSON("/q/status").done(function (result) {
        $("body").css("cursor", "default");
        $("#checking-status").css("display", "none");

        display_status(result);
    }).fail(function (xhr, status, error) {
        var err_str;

        $("body").css("cursor", "default");
        $("#checking-status").css("display", "none");

        err_str = status + ": " + error;
        $("<div>").text(err_str).appendTo("#body-content");
    });
}
