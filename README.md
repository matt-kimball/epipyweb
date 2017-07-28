# Overview

epipyweb is part of Epipylon -- http://www.epipylon.com/

epipyweb provied the web user interface to Epipylon devices.

As a foundation, epipyweb uses nginx as a web service and uWSGI
for dynamic interaction.  In order to gather DNS queries, syslog
entries for DNSmasq are recorded to a SQLite database.  Queries
on that database are made available through the uWSGI back-end.

# Contents

epipyweb contains the following components:

* `bin/epipyweb-database-rotate` - Removal of old queries from the database
* `debian/` - Scripts related to package installation
* `etc/` - Configuration for nginx, rsyslogd and uWSGI
* `record/` - Scripts for recording syslog entires to the database
* `serve/` - uWSGI back-end for database queries
* `systemd/` - Systemd configuration for startup and database rotation
* `test/` - Automated tests
* `ui/` - HTML and Javascript implementing the web UI

# Development

The first step in development is installing the Epipylon development
image on your Raspberry Pi.

See http://www.epipylon.com/index.html#development for the development
image.

After installation, log in to your Raspberry Pi and clone the epibase
repository.

    ssh epipylon@epipylon.local  # password is 'epipylon'
    git clone https://github.com/matt-kimball/epipyweb.git
    cd epipyweb

You'll need a few more tools for development:

    sudo pip3 install mypy pep8
    sudo npm install --global jslint

After making changes, use mypy to check for correctness and run the
automated tests:

    ./lint.sh
    sudo ./test.sh

If everything looks good, you can generate a new package and install it
locally:

    sudo ./package.sh
    sudo dpkg -i epipyweb_0.1-XXXX.deb  # where XXXX is the package timestamp

The `clean.sh` script can be used to remove all built packages.

Before submitting pull requests, please ensure that changed Python code has
mypy type annotations.

# License

epipyweb is licensed under the GNU General Public License 2.0.
