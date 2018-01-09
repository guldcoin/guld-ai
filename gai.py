import os
import time
import logging
from zmq import Context, SUB, SUBSCRIBE
from guldcfg import BLOCKTREE, GuldConfig
from guldgit import Git
cfg = GuldConfig()

class GuldAI(object):

    # TODO bug: does not know which .git/ tree is active (use git.toplevel)
    # TODO bug: does not read .gitignore (use fnmatch from stdlib)
    # TODO push to all remotes

    # TODO feature: post-process fsync's (GPG, AES, torrent)
    # TODO feature: pre-process on open/read (GPG, AES, torrent)

    # TODO assume always create git submodules
    # TODO feature: publish to TPC port
    # TODO feature: listen for, validate, and fetch valid commits from friends
    # TODO feature: listen for, validate and act on commands from ADMIN

    stop = None

    def __init__(self, name=None):
        self.name = name
        logging.basicConfig(filename='/var/log/guldfs/gai-%s.log' % self.name,
            level=logging.DEBUG)
        self.context = Context()
        self.subscriber = self.context.socket(SUB)
        self.subscriber.connect("ipc:///tmp/guldfs0.ipc")
        self.subscriber.setsockopt(SUBSCRIBE, b"guldfs")
        # publisher = context.socket(zmq.PUB)
        # publisher.bind("tpc://127.0.0.1:6070")
        self.stop = False
        self.repos = {}

    def run(self):
        # TODO replace with more efficient loop
        while not self.stop:
            # Read envelope with address
            [channel, message] = self.subscriber.recv_multipart()
            self.handle_fs_message(channel, message)
        logging.info("done running")

    def handle_fs_message(self, channel, message):
        if (channel != b'guldfs'):
            return
        parts = message.decode().split(":")
        # TODO be more specific about this
        if hasattr(self, parts[0]) and callable(getattr(self, parts[0])):
            args = []
            if len(parts) > 1:
                args = parts[1:]
            getattr(self, parts[0])(*args)
        #else:
        #    logging.warn('unknown message: %s' % message)

    def get_or_load_repo(self, path):
        if path in self.repos:
            return self.repos[path]
        else:
            self.repos[path] = Git(path)
            return self.repos[path]

    def mount(self, mountpoint, user):
        repo = self.get_or_load_repo('/')
        repo.pull()

    def destroy(self):
        logging.info('destroying')
        # clean up zmq socket connections
        self.subscriber.close()
        self.context.term()
        self.stop = True

    def fsync(self, path):
        if '.git/' not in path and not path.startswith('/git/'):
            repo = self.get_or_load_repo(os.path.dirname(path))
            repo.add(cfg.rawpath(path).replace(repo.toplevel, ''))
            repo.commit('gai: found changes to %s' % path)

    def fsyncdir(self, path):
        # TODO add files, commit and push. Cascade up to user home.
        if '.git/' not in path and not path.startswith('/git/'):
	        repo = self.get_or_load_repo(path)
	        repo.stash()
	        repo.pull()
	        repo.stash('apply')
            #repo.commit('gai: found changes to %s' % path)

    def open(self, path, flags):
        if '.git/' not in path and not path.startswith('/git/'):
    	    # TODO pull! check signatures! decrypt and otherwise post-process
    	    repo = get_or_load_repo(path)
    	    repo.pull()

    def readdir(self, path):
        if '.git/' not in path and not path.startswith('/git/'):
    	    # TODO pull! check signatures! decrypt and otherwise post-process
    	    repo = get_or_load_repo(path)
    	    repo.pull()

    #def chmod(self, path, mode):
    #    # TODO change gitolite server in addition to the file
    #    # TODO check that "path" is a directory, or throw an error.
    #    pass

    #def chown(self, path, uid, gid):
    #    # TODO change gitolite server in addition to the file
    #    # TODO check that "path" is a directory, or throw an error.
    #    pass

    #def create(self, path, mode):
    #    # TODO change gitolite server in addition to the file
    #    repo = self.get_or_load_repo(os.path.dirname(path))

    #def readlink(self, path):
    #    pass

    #def link(self, target, source):
    #    # TODO make a git submodule? What if there's no dir in between?
    #    pass

    #def mkdir(self, path, mode):
    #    # TODO create git submodule if mode is different from parent dir
    #    pass

    #def rmdir(self):
    #    # TODO remove from gitolite config? Not always... but sometimes?
    #	    #self.repos[path] = Git(path)
    #	    #self.repos[path].pull()
    #    pass


if __name__ == "__main__":
    t = GuldAI(name=cfg.username)
    t.run()
