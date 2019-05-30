#!/usr/bin/env python3
"""
Runner for workflow.
"""

from datetime import datetime, timezone

from internal.workflow import parser as w_parser


class JobRecord:
    """ Data class for recording job result. """

    def __init__(self, job_template_name: str):
        self._start: datetime = datetime.now(timezone.utc)
        self._end: str = ''

        self._job_template_name: str = job_template_name
        self._type: str = 'job_template'  # workflow_job is no supported yet.
        self._status: str = ''

    def set_result_successful(self):
        """ record job result """
        self._status = 'successful'

    def set_result_failed(self):
        """ record job result """
        self._status = 'failed'

    def set_end_time(self):
        """ record job finished time """
        self._end = datetime.now(timezone.utc)

    def get_created_time(self) -> str:
        """ get `created_time` for printing """
        return self._start.strftime("%Y-%m-%dT%H:%M:%S.%f")

    def get_elapsed(self) -> str:
        """ get `elapsed` for printing """
        return str(self._end - self._start).split(':')[-1]

    @property
    def job_template_name(self):
        """ getter for job_template_name """
        return self._job_template_name

    @property
    def type(self):
        """ getter for job type """
        return self._type

    @property
    def status(self):
        """ getter for job result """
        return self._status


class WorkflowRunner:
    """ Workflow runner. """

    def __init__(self, workflow_node: w_parser.WorkflowNode,
                 inventory_file: str):
        self.workflow_node = workflow_node
        self.inventory_file_path = inventory_file

        # record results of running job_templates.
        self.executed = []

    def dry_run(self):
        """
        Check each Ansible playbook's all of variables
        in each node's `before_extra_vars`.
        """

        self.workflow_node.dry_run()

        if self.workflow_node.current_node.success:
            for node in self.workflow_node.current_node.success:
                self.workflow_node.go_next_child(node)
                self.dry_run()

        if self.workflow_node.current_node.failed:
            for node in self.workflow_node.current_node.failed:
                self.workflow_node.go_next_child(node)
                self.dry_run()

        if self.workflow_node.current_node.always:
            for node in self.workflow_node.current_node.always:
                self.workflow_node.go_next_child(node)
                self.dry_run()

    def run(self, auth_extra_vars: str, work_dir: str) -> list:
        """ Execute each Ansible playbook. """

        job_template_name: str = self.workflow_node.current_node.node_name

        print()
        print('-----')
        print("<< Execute job: '{}' >>".format(job_template_name))

        record = JobRecord(job_template_name)

        r_code = self.workflow_node.run(self.inventory_file_path,
                                        auth_extra_vars,
                                        work_dir)
        record.set_end_time()

        if r_code == 0:
            record.set_result_successful()
        else:
            record.set_result_failed()

        self.executed.append(record)

        # Go next job
        if r_code == 0 and self.workflow_node.current_node.success:
            for node in self.workflow_node.current_node.success:
                self.workflow_node.go_next_child(node)
                self.run(auth_extra_vars, work_dir)

        elif r_code != 0 and self.workflow_node.current_node.failed:
            for node in self.workflow_node.current_node.failed:
                self.workflow_node.go_next_child(node)
                self.run(auth_extra_vars, work_dir)
        else:
            pass

        if self.workflow_node.current_node.always:
            for node in self.workflow_node.current_node.always:
                self.workflow_node.go_next_child(node)
                self.run(auth_extra_vars, work_dir)

        return self.executed
