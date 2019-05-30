#!/usr/bin/env python3
"""
Runner class for playbook.
"""

import shutil

from ansible.cli import playbook
import ansible.constants as conf_param


def run_playbook(playbook_path: str, inventory_path: str,
                 auth_extra_vars: str, extra_vars_json: str = None):
    """ Execute ansible-playbook. """

    ansible_path: str = shutil.which('ansible-playbook')
    args = [ansible_path, '-i', inventory_path, '-e', auth_extra_vars]

    if extra_vars_json:
        args.append('-e')
        args.append(extra_vars_json)

    args.append(playbook_path)

    cli = playbook.PlaybookCLI(args)
    cli.parse()
    exit_code: int = cli.run()

    shutil.rmtree(conf_param.DEFAULT_LOCAL_TMP, True)
    return exit_code
