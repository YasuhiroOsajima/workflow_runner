#!/usr/bin/env python3
"""
Runner for workflow.
"""

from datetime import datetime, timezone

from internal.workflow import parser as w_parser


class JobRecord:
    """ Data class for recording job result. """

    def __init__(self, job_id: int, job_template_name: str):
        self._start: datetime = datetime.now(timezone.utc)
        self._end: str = ''

        self._job_id: int = job_id
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
    def job_id(self) -> int:
        """ getter for job_template_name """
        return self._job_id

    @property
    def job_template_name(self) -> str:
        """ getter for job_template_name """
        return self._job_template_name

    @property
    def type(self) -> str:
        """ getter for job type """
        return self._type

    @property
    def status(self) -> str:
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

        current = self.workflow_node.current_node
        if self.workflow_node.current_node.success:
            for node in self.workflow_node.current_node.success:
                self.workflow_node.go_next_child(node)
                self.dry_run()
                self.workflow_node.go_back(current)

        if self.workflow_node.current_node.failed:
            for node in self.workflow_node.current_node.failed:
                self.workflow_node.go_next_child(node)
                self.dry_run()
                self.workflow_node.go_back(current)

        if self.workflow_node.current_node.always:
            for node in self.workflow_node.current_node.always:
                self.workflow_node.go_next_child(node)
                self.dry_run()
                self.workflow_node.go_back(current)

    def run(self, auth_extra_vars: str, work_dir: str,
            job_id: int = 1) -> list:
        """ Execute each Ansible playbook. """

        job_template_name: str = self.workflow_node.current_node.node_name

        print()
        print('-----')
        print("<< Execute job: '{}' >>".format(job_template_name))

        record = JobRecord(job_id, job_template_name)

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
        current = self.workflow_node.current_node
        if r_code == 0 and self.workflow_node.current_node.success:
            for node in self.workflow_node.current_node.success:
                job_id += 1
                self.workflow_node.go_next_child(node)
                self.run(auth_extra_vars, work_dir, job_id)
                self.workflow_node.go_back(current)

        elif r_code != 0 and self.workflow_node.current_node.failed:
            for node in self.workflow_node.current_node.failed:
                job_id += 1
                self.workflow_node.go_next_child(node)
                self.run(auth_extra_vars, work_dir, job_id)
                self.workflow_node.go_back(current)
        else:
            pass

        if self.workflow_node.current_node.always:
            for node in self.workflow_node.current_node.always:
                job_id += 1
                self.workflow_node.go_next_child(node)
                self.run(auth_extra_vars, work_dir, job_id)
                self.workflow_node.go_back(current)

        return self.executed
