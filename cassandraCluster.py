from cassandra.auth import PlainTextAuthProvider
import config as cfg
import cassandra
from cassandra.cluster import Cluster
from cassandra.policies import *
from ssl import PROTOCOL_TLSv1_2, SSLContext, CERT_NONE
 
try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack
 
 
 
class cassandraCluster(object):
    def __init__(self, app=None):
        self.app = app
        # self.cluster = None
        if app is not None:
            self.init_app(app)
 
    def init_app(self, app):
        app.config.setdefault('CASSANDRA_CLUSTER', ':memory:')
        app.teardown_appcontext(self.teardown)
 
    def connect(self):
        ssl_context = SSLContext(PROTOCOL_TLSv1_2)
        ssl_context.verify_mode = CERT_NONE
        auth_provider = PlainTextAuthProvider(username=cfg.config['username'], password=cfg.config['password'])
        cluster = Cluster([cfg.config['contactPoint']], port = cfg.config['port'], auth_provider=auth_provider,ssl_context=ssl_context)  
        return cluster

   
    def teardown(self, exception):
        ctx = stack.top
        if hasattr(ctx, 'cassandra_cluster'):
            ctx.cassandra_cluster.shutdown()
 
    @property
    def connection(self):
        ctx = stack.top
        if ctx is not None:
            if not hasattr(ctx, 'cassandra_cluster'):
                ctx.cassandra_cluster = self.connect()
            return ctx.cassandra_cluster