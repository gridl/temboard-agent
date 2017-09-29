# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from sys import stdout, stderr
from getpass import getpass
from optparse import OptionParser

from ..usermgmt import hash_password
from ..errors import ConfigurationError, HTTPError
from ..usermgmt import get_user
from ..configuration import Configuration
from ..types import T_PASSWORD, T_USERNAME
from ..tools import validate_parameters


class CLIOptions(OptionParser):
    """
    Command line interface options parser.
    """
    def __init__(self, *args, **kwargs):
        OptionParser.__init__(self, *args, **kwargs)
        self.add_option("-c",
                        "--config",
                        dest="configfile",
                        help="Configuration file. Default: %default",
                        default="/etc/temboard-agent/temboard-agent.conf")


def ask_password():
    raw_pass1 = getpass("Password: ")
    raw_pass2 = getpass("Retype password: ")
    if raw_pass1 != raw_pass2:
        stdout.write("Sorry, passwords do not match.\n")
        return ask_password()
    try:
        password = raw_pass1
        validate_parameters({'password': password},
                            [('password', T_PASSWORD, False)])
    except HTTPError:
        stdout.write("Invalid password.\n")
        return ask_password()
    return password


def ask_username(config):
    stdout.write("Username: ".encode('utf-8'))
    raw_username = raw_input()
    try:
        get_user(config.temboard['users'], raw_username)
    except HTTPError:
        pass
    except ConfigurationError:
        pass
    else:
        stdout.write("User already exists.\n")
        return ask_username(config)
    try:
        username = raw_username
        validate_parameters({'username': username},
                            [('username', T_USERNAME, False)])
    except HTTPError:
        stdout.write("Invalid username.\n")
        return ask_username(config)
    return username


def main():
    """
    Main function.
    """
    # Instanciate a new CLI options parser.
    optparser = CLIOptions(description="Add a new temboard-agent user.")
    (options, _) = optparser.parse_args()

    # Load configuration from the configuration file.
    try:
        config = Configuration(options.configfile)
        username = ask_username(config)
        password = ask_password()
        with open(config.temboard['users'], 'a') as fd:
            fd.write("%s:%s\n" % (
                username,
                hash_password(username, password).decode('utf-8')
                )
            )
            stdout.write("Done.\n")
    except (ConfigurationError, ImportError, IOError) as e:
        stderr.write("FATAL: %s\n" % str(e))
        exit(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt as e:
        stdout.write("\nExit..\n")