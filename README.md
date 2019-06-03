# Ansible Tower(AWX) workflow runner

## What is this.
Ansible workflow runner on local command line.  
This tool is to run workflow template without Ansible AWX server.  
And this can also check `extra_vars` dependency in each jobs in workflow by `dry_run` mode.  

Please use this command as follows:  
```
$ python3 workflow_runner.py `workflow file path` -i `inventory file path` (--ask-pass or --private-key `file path`) [-e '@extra-vars_file_path']
```

If you want to check `extra_vars` dependency correctness, you can use `dry_run` mode.  
```
$ python3 workflow_runner.py `workflow file path` -i `inventory file path` --dry_run [-e '@extra-vars_file_path']
```

**positional arguments:**
```
workflow_file         target workflow file path.
```

**optional arguments:**
```
-h, --help                                            show this help message and exit
-i INVENTORY_FILE, --inventory_file INVENTORY_FILE    Target inventory file path.
-u USER, --user USER                                  Ansible's `ansible_ssh_user` option. Default is current user.
--port PORT                                           Ansible's `ansible_port` option. Default is `22`.
--become-user BECOME_USER                             Ansible's `ansible_become_user` option. Default is `root`.
-K, --ask-become-pass                                 Ansible's `ansible_become_pass` option.
-e EXTRA_VARS, --extra-vars EXTRA_VARS                Ansible's extra_vars option. Default is `None`.
-k, --ask-pass                                        Password auth enable for ansible remote login.
                                                      Please specify this or `--private-key`.
--private-key PRIVATE_KEY                             Private key file path for ansible remote login.
                                                      Please specify this or `--ask-pass`.
--dry_run                                             Run with `dry_run` mode.
```

## Setup
```
$ pip3 install requirements.txt
$ pip3 install -e .
```
And if you use ssh login, you have to install sshpass by Ansible's dependency.  

Dry run sample workflow.
```
# python cmd/workflow_runner.py resource_files/workflow/sample_workflow.yml -i resource_files/inventory/sample_inventory.txt -e "@resource_files/extra_vars/extra-vars.yml" --dry_run

Check all variables are defined at running each job_template.
------
- OK. Variables in playbook '/vagrant/data/workflow_runner/resource_files/job_template/sample_job_template/sample_job1.yml' are available at running.

- OK. Variables in playbook '/vagrant/data/workflow_runner/resource_files/job_template/sample_job_template/sample_job2.yml' are available at running.

- OK. Variables in playbook '/vagrant/data/workflow_runner/resource_files/job_template/sample_job_template/sample_job3.yml' are available at running.

Dry run complete.
```

Run sample workflow.
```
# python cmd/workflow_runner.py resource_files/workflow/sample_workflow.yml -i resource_files/inventory/sample_inventory.txt -e "@resource_files/extra_vars/extra-vars.yml" -k
SSH password:
......................

------ Job results ------
==== ============= ============== ============ ============================ ===========
 id      name           type         status              created              elapsed
==== ============= ============== ============ ============================ ===========
 1    sample_job1   job_template   successful   2019-06-02T08:49:43.738865   06.343523
 2    sample_job2   job_template   successful   2019-06-02T08:49:50.082515   01.832642
 3    sample_job3   job_template   successful   2019-06-02T08:49:51.915217   01.879878
==== ============= ============== ============ ============================ ===========

------ Workflow process ended ------
======================= ============================ ============
 workflow_job_template            created               status
======================= ============================ ============
 sample_workflow.yml     2019-06-02T08:49:43.738723   successful
======================= ============================ ============
```

## Attention
- job_template names in workflow YAML file have to be same as job_template YAML file name which without '.yml'.
- YAML structure of workflow file have to be following Ansible AWX style:
  ```
  - job_template: sample_job1
    success:
      - job_template: sample_job2
        success:
          - job_template: sample_job4
    failure:
      - job_template: sample_job3
  ```
  
  You can not use other type style with `success_nodes`, `always_nodes`,`failure_nodes`,`inventory_source`,`project`.  
  ```
  - failure_nodes:
  - inventory_source: 42
  job_template: 45
  success_nodes:
  - always_nodes:
    - job_template: 55
      success_nodes:
      - job_template: 44
    project: 40
  ```
  
## Issue
- all style workflow support.
- not supported workflow in workflow yet.
- not supported cover roles in job_template yet.
- simultaneous multi job execution if parallel case wrote in workflow.
