# coding: utf-8

import os
import unittest

import delegator

from fabric_testing.docker_base import BaseFabricDockerTestCase

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_PATH = os.path.abspath(os.path.join(CURRENT_DIR, '..'))
FIXTURES_PATH = os.path.abspath(os.path.join(CURRENT_DIR, 'fixtures'))

FABRIC_MASTER_NAME = 'master'
FABRIC_USER = 'fabric-user'

class RemoteTestCase(BaseFabricDockerTestCase):

    # nosetests -s -v tests.test_docker_base:RemoteTestCase

    FABRIC_MASTER_NAME = FABRIC_MASTER_NAME

    IMAGES = [
        {
            'base_path': PROJECT_PATH, 
            'dockerfile': 'tests/Dockerfile', 
            'tag': 'mytestimage:mytag'
        }
    ]

    CONTAINERS = [
        {
            'name': 'web1',
            'image': "mytestimage:mytag",
            'hostname': 'web1', 
            #'command': 'python -m http.server 8080', 
            #'working_dir': '/app'
        },
        {
            'name': 'web2',
            'image': "python:3.5-alpine", 
            'command': 'python -m http.server 8080', 
            'working_dir': '/app'
        },
        {
            'name': FABRIC_MASTER_NAME,
            'image': "mytestimage:mytag", 
            'hostname': FABRIC_MASTER_NAME, 
            'working_dir': '/fabfile',
            'links': {
                'web1': 'web1',
                'web2': 'web2'
            },
            'environment': {
                'TEST': "1",
            }                                      
        }
    ]

    #REMOVE_CONTAINERS = False
    #REMOVE_IMAGES = False

    def setUp(self):
        super(RemoteTestCase, self).setUp()

        self.master_env = {
            'PATH': '/opt/rh/python27/root/usr/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
            'LD_LIBRARY_PATH': '/opt/rh/python27/root/usr/lib64',
        }        
        self._prepare()

    def _prepare(self):
        
        cmds = [
            'pip install -U pip',
            'pip install Fabric3'
        ]
        for cmd in cmds:
            print("Run in master : %s" % cmd)
            exit_code, output = self.run_in_master(cmd,
                                                  tty=True,
                                                  environment=self.master_env)
            self.assertEquals(exit_code, 0, output)
        
        ## Put fixtures in fabric master container
        self.docker_put_archive(ct_name=self.FABRIC_MASTER_NAME, 
                                source_path=os.path.join(FIXTURES_PATH, 'fabfile'), 
                                archive_path='/tmp/fabfile.tar', 
                                target='/fabfile')
    def test_tasks_list(self):
        cmd = 'fab -f /fabfile --list'
        exit_code, output = self.run_in_master(cmd,
                                               environment=self.master_env)
        self.assertEquals(exit_code, 0, output)
        tasks = [
            'local_hostname',
            'local_ls',
            'run_hostname',
            'run_ls',
            'sudo_hostname',
            'sudo_ls',            
        ]
        for task in tasks:
            self.assertTrue(task in output)

    def test_hostname(self):
        cmd = 'fab -f /fabfile -H web1 utils.sudo_hostname'
        exit_code, output = self.run_in_master(cmd,
                                               environment=self.master_env,
                                               user=FABRIC_USER)
        self.assertEquals(exit_code, 0, output)
        self.assertTrue('sudo hostname for [web1]' in output, output)

        cmd = 'fab -f /fabfile -H web1 utils.run_hostname'
        exit_code, output = self.run_in_master(cmd,
                                               environment=self.master_env,
                                               user=FABRIC_USER)
        self.assertEquals(exit_code, 0, output)
        self.assertTrue('run hostname for [web1]' in output, output)

        cmd = 'fab -f /fabfile utils.local_hostname'
        exit_code, output = self.run_in_master(cmd,
                                               environment=self.master_env)
        self.assertEquals(exit_code, 0, output)
        self.assertTrue('local hostname in output', output)
