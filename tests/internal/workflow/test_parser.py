#!/usr/bin/env python3
""" Unit test for workflow parser """

import unittest

import yaml

from internal.workflow import tree


class TestWorkFlowParser(unittest.TestCase):
    """ Unit test for workflow parser """

    def test_generate_workflow_dict(self):
        """ Test case for YAML file convert to dict """

        workflow_yml = """
---
- job_template: sample_job1
  success:
    - job_template: sample_job2
  always:
    - job_template: sample_job3"""

        result = yaml.load(workflow_yml, Loader=yaml.SafeLoader)

        correct = [{'job_template': 'sample_job1',
                    'success': [{'job_template': 'sample_job2'}],
                    'always': [{'job_template': 'sample_job3'}]}]

        self.assertEqual(result, correct)

    def test_workflow_parse(self):
        """ Test case dict convert to workflow Node obj """

        workflow = [{'job_template': 'sample_job1',
                     'success': [{'job_template': 'sample_job2'}],
                     'always': [{'job_template': 'sample_job3'}]}]
        dry_run = True
        extra_vars_arg = {'sample_vars': 'sample'}

        top_node = tree.generate_workflow_tree(workflow, dry_run,
                                               extra_vars_arg)
        correct = 1
        self.assertEqual(top_node.node_id, correct)


if __name__ == '__main__':
    unittest.main()
