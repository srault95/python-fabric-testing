# coding: utf-8

import os
import unittest
import time

import delegator
import docker

class BaseFabricDockerTestCase(unittest.TestCase):
    """Test Base for functionals tests with Python Fabric. 
    """

    DOCKER_URL = os.environ.get('DOCKER_URL', 'unix://var/run/docker.sock')

    REBUILD_IMAGES = True
    REMOVE_CONTAINERS = True
    REMOVE_IMAGES = True

    FABRIC_MASTER_NAME = None

    # One record by container
    # Same parameters of run method - see https://docker-py.readthedocs.io/en/stable/containers.html
    CONTAINERS = [
        {
            #name="web1",
            #image="myimage:mytag", 
            #working_dir='/fixtures'
            #sleep=5 # time in seconds for sleep after run
        }
    ]

    CONTAINERS_RUNNING = {}

    # Same parameters of build method - see https://docker-py.readthedocs.io/en/stable/images.html
    IMAGES = [
        #{
        #    'base_path': PROJECT_PATH, 
        #    'dockerfile': 'tests/Dockerfile', 
        #    'tag': 'myimage:mytag'
        #}
    ]

    def setUp(self):
        super(BaseFabricDockerTestCase, self).setUp()

        if self.FABRIC_MASTER_NAME is None:
            self.fail("FABRIC_MASTER_NAME is required")

        self.get_client()
        
        if self.REBUILD_IMAGES:
            self.build_images()
        
        if self.REMOVE_CONTAINERS:
            self.remove_containers()
        
        self.run_containers()

    def tearDown(self):
        super(BaseFabricDockerTestCase, self).tearDown()
        
        if self.REMOVE_CONTAINERS:
            self.remove_containers()
        
        if self.REMOVE_IMAGES:
            self.remove_images()

    def get_client(self):
        if hasattr(self, 'client'):
            return self.client
        self.client = docker.DockerClient(base_url=self.DOCKER_URL)
        return self.client

    def get_ct(self, name):
        if not name in self.CONTAINERS_RUNNING:
            self.fail("container [%s] not found or not running" % name)
        return self.CONTAINERS_RUNNING.get(name)

    def run_in_master(self, cmd, **kwargs):
        exit_code, output = self.get_ct(self.FABRIC_MASTER_NAME).exec_run(cmd, **kwargs)  
        return exit_code, output  

    def docker_put_archive(self, ct_name=None, source_path=None, 
                            archive_path=None, target=None, 
                            exclude_vcs=True):
        
        c = delegator.run('rm -vf %s' % archive_path)
        self.assertEquals(c.return_code, 0, c.out)        
        
        cmd = ['tar']
        if exclude_vcs:
            cmd.append('--exclude-vcs --exclude-vcs-ignores')
        cmd.append('-cf %s .' % archive_path)
        
        c = delegator.run(" ".join(cmd), cwd=source_path)
        self.assertEquals(c.return_code, 0, c.out)               

        ct = self.get_ct(ct_name)
        with open(archive_path, 'rb') as fp:
            ct.put_archive(target, fp)
        
    def build_images(self):
        for img in self.IMAGES:
            self.get_client().images.build(path=img['base_path'], 
                                 dockerfile=img['dockerfile'], 
                                 tag=img['tag'])

    def remove_images(self):
        for img in self.IMAGES:
            self.get_client().images.remove(img['tag'], force=True)

    def is_running(self, ct_name):
        try:
            self.CONTAINERS_RUNNING[ct_name] = self.get_client().containers.get(ct_name)
            return True
        except docker.errors.NotFound:
            return False

    def run_containers(self):
        for config in self.CONTAINERS:            
            if config.get('name', None) is None:
                self.fail('name parameter is required for all containers')
            if config.get('image', None) is None:
                self.fail('image parameter is required for all containers')
            
            name = config['name']
            if self.is_running(name):
                print("bypass run because the container [%s] already running" % name)
                continue
            
            print('create container [%s]' % name)
            ct_config = config.copy()
            
            image = ct_config.pop('image')
            wait_sleep = ct_config.pop('sleep', 0)
            ct_config['detach'] = True
            ct_config['auto_remove'] = True
            ct = self.get_client().containers.run(image, **ct_config)
            self.CONTAINERS_RUNNING[name] = ct
            if wait_sleep > 0:
                time.sleep(wait_sleep)

    def remove_containers(self):
        for ct in self.CONTAINERS:
            ct_name = ct['name']
            try:
                ct = self.get_client().containers.get(ct_name)
                ct.kill()
            except: 
                pass

            try:
                ct = self.get_client().containers.get(ct_name)
                ct.remove(force=True)
            except: 
                pass

            