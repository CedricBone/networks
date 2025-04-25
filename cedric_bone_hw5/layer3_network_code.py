"""
- LAN B: 20.10.172.0/25
- LAN A: 20.10.172.128/26
- LAN C: 20.10.172.192/27
"""

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node, Controller
from mininet.log import setLogLevel, info
from mininet.cli import CLI

class LinuxRouter(Node):
    "A Node with IP forwarding enabled."
    def config(self, **params):
        super(LinuxRouter, self).config(**params)
        # Enable forwarding on the router
        self.cmd('sysctl net.ipv4.ip_forward=1')

    def terminate(self):
        self.cmd('sysctl net.ipv4.ip_forward=0')
        super(LinuxRouter, self).terminate()

class NetworkTopo(Topo):
    "A network topology with 3 LANs"
    
    def build(self, **_opts):

        #defaultIP = '192.168.1.1/24'  # IP address for r0-eth1
        #router = self.addNode( 'r0', cls=LinuxRouter, ip=defaultIP )

        # Add routers
        ra = self.addNode('ra', cls=LinuxRouter, ip='20.10.172.129/26')  # LAN A
        rb = self.addNode('rb', cls=LinuxRouter, ip='20.10.172.1/25')     # LAN B
        rc = self.addNode('rc', cls=LinuxRouter, ip='20.10.172.193/27')   # LAN C
        
        # Add switches LANs
        s1 = self.addSwitch('s1')  
        s2 = self.addSwitch('s2')  
        s3 = self.addSwitch('s3')
        
        # Connect routers to switches
        self.addLink(s1, ra, intfName1='s1-ra', intfName2='ra-s1',
                      params2={'ip': '20.10.172.129/26'})
        self.addLink(s2, rb, intfName1='s2-rb', intfName2='rb-s2',
                      params2={'ip': '20.10.172.1/25'})
        self.addLink(s3, rc, intfName1='s3-rc', intfName2='rc-s3',
                      params2={'ip': '20.10.172.193/27'})
        
        # Connect routers to routers
        self.addLink(ra, rb, intfName1='ra-rb', intfName2='rb-ra',
                      params1={'ip': '20.10.100.1/24'},
                      params2={'ip': '20.10.100.2/24'})
        
        self.addLink(rb, rc, intfName1='rb-rc', intfName2='rc-rb',
                      params1={'ip': '20.10.100.3/24'},
                      params2={'ip': '20.10.100.4/24'})
        
        self.addLink(rc, ra, intfName1='rc-ra', intfName2='ra-rc',
                      params1={'ip': '20.10.100.5/24'},
                      params2={'ip': '20.10.100.6/24'})
        
        # LAN A
        ha1 = self.addHost('ha1', ip='20.10.172.130/26',
                           defaultRoute='via 20.10.172.129')
        ha2 = self.addHost('ha2', ip='20.10.172.131/26',
                           defaultRoute='via 20.10.172.129')
        
        # Add hosts for LAN B
        hb1 = self.addHost('hb1', ip='20.10.172.2/25',
                           defaultRoute='via 20.10.172.1')
        hb2 = self.addHost('hb2', ip='20.10.172.3/25',
                           defaultRoute='via 20.10.172.1')
        
        # LAN C
        hc1 = self.addHost('hc1', ip='20.10.172.194/27',
                           defaultRoute='via 20.10.172.193')
        hc2 = self.addHost('hc2', ip='20.10.172.195/27',
                           defaultRoute='via 20.10.172.193')
        
        # Connect hosts to switches
        self.addLink(ha1, s1)
        self.addLink(ha2, s1)
        self.addLink(hb1, s2)
        self.addLink(hb2, s2)
        self.addLink(hc1, s3)
        self.addLink(hc2, s3)

def run():
    "Test network with 3 routers and their hosts"
    topo = NetworkTopo()
    # Use a controller to avoid connection issues with switches
    net = Mininet(topo=topo, controller=Controller)
    net.start()
    
    info('*** Routing Tables on Routers:\n')
    for router in ['ra', 'rb', 'rc']:
        info(f'*** Routing Table on {router}:\n')
        info(net[router].cmd('route'))
        info('\n')
    
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()