#!/usr/bin/env python3
"""
Parse workflow structure.
"""

from datetime import datetime
import json

import yaml

from internal.workflow import tree
from internal.playbook import runner, parser


class DryRunFailed(Exception):
    """
    Dry run failed by defined variables not enough.
    """

    def __init__(self, message):
        super(DryRunFailed, self).__init__()
        self.message = message

    def __str__(self):
        return repr(self.message)


class WorkflowNode:
    """
    workflow tree object.
    """

    def __init__(self, top_node: tree.Node):
        self.current_node: tree.Node = top_node
        self.parent_node: tree.Node = tree.Node(0, 'None', '')

    def check_var_defined(self, var_name: str):
        """ Check target extra_vars already defined. """

        return var_name in self.parent_node.before_extra_vars

    def go_next_child(self, next_node):
        """ Move forward current job_template node. """
        self.parent_node = self.current_node
        self.current_node = next_node

    def _prepare_playbook(self, work_dir: str) -> (str, list):
        """ Generate copy playbook file with dump `set_stats` value. """

        set_stats_file_list = []

        if self.current_node.define_stats:
            # Create copy playbook and replace playbook to use.

            node_id = str(self.current_node.node_id)
            time_stamp = datetime.now().strftime("%Y%m%d%H%M%S")
            copy_playbook_path = "{}/tmp_playbook_{}_{}.yml".format(
                work_dir, node_id, time_stamp)

            with open(self.current_node.playbook_path, 'r') as pbf:
                playbook: dict = yaml.load(stream=pbf, Loader=yaml.SafeLoader)
                tasks = playbook[0]['tasks']

                for idx, task in enumerate(tasks):
                    if 'set_stats' in task:
                        for v_name, v_val in task['set_stats']['data'].items():
                            stats_var_path = "{}/{}-{}-{}.txt".format(
                                work_dir, node_id, v_name, time_stamp)
                            set_stats_file_list.append(stats_var_path)
                            debug_job = [{'copy': {'dest': stats_var_path,
                                                   'content': v_val}}]
                            tasks = \
                                tasks[:idx + 1] + debug_job + tasks[idx + 1:]

            playbook[0]['tasks'] = tasks
            with open(copy_playbook_path, 'w') as tpf:
                tpf.write(yaml.dump(playbook))

            playbook_path = copy_playbook_path
        else:
            playbook_path = self.current_node.playbook_path

        return playbook_path, set_stats_file_list

    def _set_after_extra_vars(self, set_stats_files: [str]):
        after_extra_vars = {}
        after_extra_vars.update(self.current_node.before_extra_vars)

        if set_stats_files:
            for stats_file in set_stats_files:
                with open(stats_file, "r") as stf:
                    stats_value: str = stf.read()
                    stats_key: str = stats_file.split('-')[1]
                    after_extra_vars.update({stats_key: stats_value})

        self.current_node.set_after_extra_vars(after_extra_vars)

    def run(self, inventory_file: str, auth_extra_vars: str,
            work_dir: str) -> int:
        """ Execute each playbook. """

        playbook, set_stats_list = self._prepare_playbook(work_dir)

        if self.parent_node.node_id != 0:
            self.current_node.set_before_extra_vars(
                self.parent_node.after_extra_vars)

        extra_vars_json: str = json.dumps(self.current_node.before_extra_vars)

        r_code = runner.run_playbook(playbook, inventory_file,
                                     auth_extra_vars, extra_vars_json)

        self._set_after_extra_vars(set_stats_list)
        return r_code

    @staticmethod
    def _check_vars_covered(necessary: set, defined: set, playbook_path: str):
        if not necessary <= defined:
            undefined: set = necessary - defined
            message = "Necessary variables not defined. """ \
                      "playbook: '{}', variable: {}".format(playbook_path,
                                                            undefined)
            raise DryRunFailed(message)

    def dry_run(self):
        """ Exec dry run check each playbook. """

        playbook_path: str = self.current_node.playbook_path
        result: tuple = parser.get_necessary_variable_keys(playbook_path)
        necessary_at_started: set = result[0]
        necessary_in_tasks: dict = result[1]

        defined_at_started: set = set(self.current_node.before_extra_vars.keys())
        set_fact_in_tasks: dict = self.current_node.define_fact
        defined_on_vars_header: set = self.current_node.define_vars_header

        # Check variables defined for playbook header.
        self._check_vars_covered(necessary_at_started, defined_at_started,
                                 playbook_path)

        # Check variables defined for playbook tasks.
        defined: set = defined_at_started | defined_on_vars_header
        for task_idx, necessary_key in necessary_in_tasks.items():
            if set_fact_in_tasks:
                defined = defined | set_fact_in_tasks[task_idx]

            self._check_vars_covered(necessary_key, defined, playbook_path)

        print("- OK. Variables in playbook '{}' are available at running."
              .format(playbook_path))
        print()


def parse(workflow_file_path: str, dry_run: bool,
          extra_vars_arg: dict) -> WorkflowNode:
    """
    parse workflow file and return tree object.
    """

    with open(workflow_file_path, "r") as wfp:
        workflow_dict = yaml.load(stream=wfp, Loader=yaml.SafeLoader)

    top_node: tree.Node = tree.generate_workflow_tree(workflow_dict, dry_run,
                                                      extra_vars_arg)
    workflow = WorkflowNode(top_node)
    return workflow
