#!/usr/bin/env python3
"""
Ansible auth env variables for remote login.
"""

import getpass
import json
import os
import sys


class AuthInfo:
    """
    Data class for Ansible auth env variables.
    """

    def __init__(self, ask_pass: bool, private_key: str, user: str, port: int,
                 become_user: str, ask_become_pass: bool):
        self._check_private_key(private_key)

        self._ask_pass: bool = ask_pass
        self._private_key: str = private_key
        self._user: str = user
        self._port: int = port
        self._become_user: str = become_user
        self._ask_become_pass: bool = ask_become_pass

    @staticmethod
    def _check_private_key(private_key: str):
        if private_key and not os.path.isfile(private_key):
            print()
            print('<< Invalid argument. >>')
            print('Specified private key not found.')
            sys.exit(2)

    def generate_auth_extra_vars(self) -> str:
        """
        Generate Ansible extra_vars json for remote login auth.
        """

        auth_extra_vars = {}

        # necessary auth vars
        if self._ask_pass:
            ask_pass: str = getpass.getpass('SSH password: ')

            auth_extra_vars['ansible_ssh_pass']: str = ask_pass
        else:
            auth_extra_vars['ansible_ssh_private_key_file']: str = \
                self._private_key

        # other options
        if self._user:
            auth_extra_vars['ansible_ssh_user']: str = self._user

        if self._port:
            auth_extra_vars['ansible_port']: str = self._port

        if self._become_user:
            auth_extra_vars['ansible_become_user']: str = self._become_user

        if self._ask_become_pass:
            become_pass: str = getpass.getpass('SUDO password: ')

            auth_extra_vars['ansible_become_user']: str = become_pass

        auth_extra_vars_json: str = json.dumps(auth_extra_vars)

        return auth_extra_vars_json
