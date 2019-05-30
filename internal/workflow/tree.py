#!/usr/bin/env python3
"""
Tree structure generator for workflow parser.
"""

import glob
import pathlib

import yaml


class ParseFailed(Exception):
    """
    Parsing workflow structure failed.
    """

    def __init__(self, message):
        super(ParseFailed, self).__init__()
        self.message = message

    def __str__(self):
        return repr(self.message)


class Node:
    """
    workflow job_template node in workflow tree.
    """

    def __init__(self, node_id: int, node_name: str, playbook_path: str):
        self.node_id = node_id
        self.node_name = node_name
        self.playbook_path = playbook_path

        # child job_template list.
        self.success = []
        self.failed = []
        self.always = []

        # extra_vars at this job_template stage.
        self.before_extra_vars = {}
        self.define_stats = {}
        self.after_extra_vars = {}

    @staticmethod
    def _set_top_job_extra_vars() -> dict:
        top_dir: pathlib.PosixPath = \
            pathlib.Path(__file__).resolve().parent.parent.parent
        extra_vars_dir = 'resource_files/extra_vars'
        # extra_vars_file is 'extra-vars.yml' only.
        extra_vars_file = \
            str(top_dir / "{}/extra-vars.yml".format(extra_vars_dir))
        match: list = glob.glob(extra_vars_file, recursive=True)
        extra_vars_file_path: str = match[0]

        with open(extra_vars_file_path, "r") as evfp:
            extra_vars_dict = yaml.load(stream=evfp, Loader=yaml.SafeLoader)

        return extra_vars_dict

    def _set_job_extra_vars(self, parent=None):
        extra_vars_dict = {}

        if parent:
            extra_vars_dict.update(parent.after_extra_vars)
        else:
            extra_vars_dict.update(self._set_top_job_extra_vars())

        self.before_extra_vars = extra_vars_dict

    def _set_define_stats(self):
        with open(self.playbook_path, "r") as ppf:
            job_template: dict = yaml.load(stream=ppf, Loader=yaml.SafeLoader)

        job_template_dict = job_template[0]
        stats: list = [value['data'].keys()[0]
                       for key, value in job_template_dict.items()
                       if 'set_stats' in key]
        if stats:
            self.define_stats = {key: None for key in stats}

    def _set_dry_run_after_extra_vars(self):
        self.after_extra_vars.update(self.before_extra_vars)
        self.after_extra_vars.update(self.define_stats)

    def prepare_job_node(self, parent_node=None):
        """ This method is always called for top job_template """

        self._set_job_extra_vars(parent_node)
        self._set_define_stats()
        # Non top job_template node's `self.before_extra_vars`
        # will be replaced in ahead of job running process.
        # And `self.after_extra_vars` will be set at after job running process.

    def prepare_job_node_dry_run(self, parent_node=None):
        """ Set job_template node's all of data for dry run. """

        self._set_job_extra_vars(parent_node)
        self._set_define_stats()
        self._set_dry_run_after_extra_vars()

    def set_before_extra_vars(self, parent_after_extra_vars: dict):
        """ setter for Node's `before_extra_vars` """
        self.before_extra_vars = parent_after_extra_vars

    def set_after_extra_vars(self, after_extra_vars: dict):
        """ setter for Node's `after_extra_vars` """
        self.after_extra_vars = after_extra_vars

    def add_parent_success(self, parent):
        """ Add target Node to parent Node's `success` child list. """
        parent.success.append(self)

    def add_parent_failed(self, parent):
        """ Add target Node to parent Node's `failed` child list. """
        parent.failed.append(self)

    def add_parent_always(self, parent):
        """ Add target Node to parent Node's `always` child list. """
        parent.always.append(self)


def generate_workflow_tree(workflow: list, dry_run: bool) -> Node:
    """
    arg 'workflow' ->
    [
        {
            "job_template": "sample_job1",
            "success": [
                {
                    "job_template": "sample_job2",
                    "success": [
                        {
                            "job_template": "sample_job3"
                        }
                    ]
                }
            ]
        }
    ]
    """

    stack = []
    node_id = 0
    initial_job_template: dict = workflow[0]

    top_node: Node = parse_job_dict(initial_job_template, stack, node_id,
                                    None, dry_run)
    if not top_node:
        raise ParseFailed("top job_template not found")

    return top_node


def parse_job_dict(job_dict: dict, stack: list, node_id: int, child_type=None,
                   dry_run=False):
    """
    Create each job's Node and chain to it's parent Node.
    """

    # nested workflow yaml is an future issue.
    ## execute_available = {'job_template', 'workflow'}
    execute_available = {'job_template'}
    success_keyword = {'success'}
    failed_keyword = {'failed'}
    always_keyword = {'always'}

    top_node = None
    node_id += 1

    # Get this stage's executable keyword. Maybe `job_template`.
    executable_keywords = execute_available & set(job_dict.keys())
    if len(executable_keywords) != 1:
        raise ParseFailed("Invalid executable_keywords: {}"
                          .format(executable_keywords))

    keyword: str = list(executable_keywords)[0]

    # Get this stage's job_template name.
    # Currently, nested workflow is not supported.
    job_template_name: str = \
        job_dict[keyword]  # Target stage's `job_template` playbook name.

    top_dir: pathlib.PosixPath = \
        pathlib.Path(__file__).resolve().parent.parent.parent
    job_template_dir = 'resource_files/job_template'
    job_template_dir_path = \
        str(top_dir / "{}/**/{}.y*".format(job_template_dir,
                                           job_template_name))
    match: list = glob.glob(job_template_dir_path, recursive=True)
    playbook_path: str = match[0]

    # Parse and prepare job_template.
    # And go to next stage by Depth first search.
    node = Node(node_id, job_template_name, playbook_path)
    if node_id == 1:
        top_node = node

        if dry_run:
            node.prepare_job_node_dry_run()
        else:
            node.prepare_job_node()
    else:
        parent_node: Node = stack[-1]

        if dry_run:
            node.prepare_job_node_dry_run(parent_node)
        else:
            node.prepare_job_node(parent_node)

        if child_type in success_keyword:
            node.add_parent_success(parent_node)
        elif child_type in failed_keyword:
            node.add_parent_failed(parent_node)
        elif child_type in always_keyword:
            node.add_parent_failed(parent_node)
        else:
            raise ParseFailed("Invalid keyword specified: {}"
                              .format(child_type))

    stack.append(node)
    for state, child_list in job_dict.items():
        if state in success_keyword | failed_keyword | always_keyword:
            for child_dict in child_list:
                parse_job_dict(child_dict, stack, node_id, state)

    stack.pop()

    return top_node
