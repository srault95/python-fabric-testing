# Environnement de Test Python pour Fabric

Ce projet utilise Docker pour simuler des machine virtuelles auxquelles se connecte Fabric par SSH.

Voir la documentation ci-dessous ou le répertoire **tests** pour l'utilisation.

## Utilisation dans un test python-fabric

L'exemple suivant est une simple tâche fabric qui va créer un répertoire sur plusieurs serveurs.

Le fabric est lancé à partir d'un serveur d'admin (master)

Le SSH est pré-configuré pour que le serveur d'admin communique avec les autres serveurs.

Le test fonctionnel va lancer à distance (par docker exec), l'appel à la commande fabric.

```
pip install git+https://github.com/srault95/python-fabric-testing#egg=python-fabric-testing
pip install nose
```

```
# fabfile

from fabric.api import task, sudo, puts
from fabric.state import env
from fabric.contrib.files import exists

@task
def create_directory(directory):
    puts("create_directory [%s] for host [%s]" % (directory, env['host_string']))
    if not exists(directory):
        sudo('mkdir -vp %s' % directory)

```

```
# tests/test_task1.py

import os
import unittest

from fabric_testing.docker_base import BaseFabricDockerTestCase

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_PATH = os.path.abspath(os.path.join(CURRENT_DIR, '..'))

INSTALL_PROJECT = '/usr/local/myfabric'
FABRIC_MASTER_NAME = 'deploy'
FABRIC_USER = 'admin-user'

class RemoteTestCase(BaseFabricDockerTestCase):
    
    FABRIC_MASTER_NAME = FABRIC_MASTER_NAME
    FABRIC_USER = FABRIC_USER

    # Vous pouvez ajouter des images personnalisé qui seront traitées par docker build
    IMAGES = []

    # Tous les conteneurs sont détruits et recréés à chaque test
    CONTAINERS = [
        {
            'name': 'srv1',
            'image': "srault95/docker-ssh-testing:centos6" 
        },
        {
            'name': 'srv2',
            'image': "srault95/docker-ssh-testing:centos6"
        },
        {
            'name': FABRIC_MASTER_NAME,
            'image': "srault95/docker-ssh-testing:centos6", 
            'working_dir': INSTALL_PROJECT,
            'links': {
                'srv1': 'srv1',
                'srv2': 'srv2'
            }
        }
    ]

    def setUp(self):
        super(RemoteTestCase, self).setUp()
        self._prepare()

    def _prepare(self):

        self.exec_env = {
            'PATH': '/opt/rh/python27/root/usr/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
            'LD_LIBRARY_PATH': '/opt/rh/python27/root/usr/lib64',
        }

        # Copie le projet dans le conteneur 
        # Vous pouvez aussi le faire par un git clone
        self.docker_put_archive(ct_name=self.FABRIC_MASTER_NAME, 
                                source_path=PROJECT_PATH, 
                                archive_path='/tmp/project.tar', 
                                target=INSTALL_PROJECT)

        cmds = [
            'pip install -U pip',
            'pip install Fabric3',
        ]

        for c in cmds:
            print('RUN : %s' % c)
            exit_code, output = self.run_in_master(c)
            self.assertEquals(exit_code, 0, output)           

    def test_task1_directory_not_exists(self):
        
        directory = '/home/sites_web/www'
        cmd = 'fab -f %s/fabfile create_directory:%s' % (INSTALL_PROJECT, directory)
        exit_code, output = self.run_in_master(cmd, environment=self.exec_env, user=self.FABRIC_USER)
        print('TASK RUN: ', output)
        self.assertEquals(exit_code, 0, output)

        # Verifiez que le répertoire existe dans les conteneurs
        cmd = "sudo test -e %s" % directory
        for srv in ['srv1', 'srv2']:
            exit_code, output = self.get_ct(srv).exec_run(cmd, 
                                                          environment=self.exec_env, 
                                                          user=self.FABRIC_USER)        
            self.assertEquals(exit_code, 0, output)

```

```
# Lancez tous les tests:
$ nosetests -s -v tests

# Pour lancer un seul test:
$ nosetests -s -v tests.test_task1:RemoteTestCase.test_task1_directory_not_exists
```

**Pour lancer ce test à l'intérieur d'un conteneur Docker:**

> Vous devez être **root** ou avoir des privilèges admin et utiliser **sudo**

```
# Placez-vous à la racine du projet et lancez:

$ docker run -it --rm -v /var/run/docker.sock:/var/run/docker.sock -v $PWD:/app -w /app alpine:3.7 sh

$ apk add --no-cache py2-paramiko py2-pip git bash sudo tar

$ pip install -U pip

$ pip install nose docker

$ nosetests -s -v tests
```
