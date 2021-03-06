from .state import StateMachine, StateMachineInterface
from multiprocessing import Queue

class LocalProxyInternalState(StateMachine):
    event_transitions = {
        'error': { 
            'allocating':   'error',
        },
        'create': {
            None:           'allocating'
        },
        'allocated': {
            'allocating':   'created',
        }
    }

    def __init__(self, proxy, load_balancer):
        self.proxy = proxy
        self.load_balancer = load_balancer
        self.queue = Queue()
        super().__init__()

    def error(self, message):
        raise Exception(message)
    
    def allocating(self, klass, args, kwargs):
        self.load_balancer.send('new', self.queue, klass, args, kwargs)

    def created(self, remote_proxy):
        self.proxy.remote_proxy = remote_proxy
        self.proxy.remote_proxy.send(self.proxy.locals_events)
        del self.proxy.local_events
        self.proxy.send = self.proxy.remote_proxy.send

class LocalProxy(StateMachineInterface):
    def __init__(self, load_balancer, klass, *args, **kwargs):
        self.event_transitions = klass.event_transitions
        self.load_balancer = load_balancer
        self.local_events = []
        self.remote_proxy = None
        self.internal = ProxyInternalState(self, load_balancer)
        self.internal.send('create', klass, *args, **kwargs)

    def enqueue_local_events(self, event, *args, **kwargs):
        self.local_events.append((event, args, kwargs))

    send = enqueue_local_events
