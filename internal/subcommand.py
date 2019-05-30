#!/usr/bin/env python3
"""
routing sub command process.
"""

import os

import texttable as ttb

from internal.workflow import parser as w_parser
from internal.workflow import runner as w_run

DEFAULT_DIR = '/tmp/workflow_runner'


def _prepare_work_directory(dir_path='') -> str:
    if not dir_path:
        dir_path = DEFAULT_DIR

    if not os.path.exists(dir_path):
        os.mkdir(dir_path)

    return dir_path


def _print_result(workflow_file_path: str, result: [w_run.JobRecord]):
    table = ttb.Texttable()
    table.set_deco(ttb.Texttable.HEADER | ttb.Texttable.VLINES | ttb.Texttable.BORDER)
    table.set_cols_dtype(['t',  # name(text)
                          't',  # type(text)
                          't',  # status(text)
                          't',  # created(text)
                          't'])  # elapsed(text)
    table.set_cols_align(['l', 'l', 'l', 'l', 'l'])
    table.header(["name", "type", "status", "created", "elapsed"])

    print("workflow: {}".format(workflow_file_path))
    print('-----')

    for res in result:
        recored = [res.job_template_name,
                   res.type,
                   res.status,
                   res.get_created_time(),
                   res.get_elapsed()]
        table.add_row(recored)

    print(table.draw())


def execute(dry_run: bool, workflow_file: str, inventory_file: str,
            auth_extra_vars: str):
    """
    Run sub command with switching 'dry_run' option.
    """

    work_dir: str = _prepare_work_directory()

    workflow_node: w_parser.WorkflowNode = w_parser.parse(workflow_file,
                                                          dry_run)

    workflow = w_run.WorkflowRunner(workflow_node, inventory_file)

    if dry_run:
        print('Check all variables are defined at running each job_template.')
        print('------')

        workflow.dry_run()

        print("Dry run complete.")
    else:
        result: [w_run.JobRecord] = workflow.run(auth_extra_vars, work_dir)
        _print_result(workflow_file, result)
