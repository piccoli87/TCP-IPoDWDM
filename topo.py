##
# Mininet code to compare 4 different TCP congestion control algorithms.
#

import argparse
from time import sleep, mktime
import subprocess
import csv
from datetime import datetime
import matplotlib
matplotlib.use('Agg')   # Force matplotlib to not use any Xwindows backend.
import matplotlib.pyplot as plt
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.util import dumpNodeConnections, quietRun
from mininet.log import info, lg, setLogLevel


from mnoptical.dataplane import (
    OpticalLink, UnidirectionalOpticalLink as ULink,
    ROADM, Terminal, OpticalNet as Mininet, km, m, dB, dBm )
from mnoptical.node import Amplifier
from mnoptical.ofcdemo.demolib import OpticalCLI as CLI, cleanup
from mnoptical.rest import RestServer
from mnoptical.ofcdemo.demolib import OpticalCLI as CLI
from mininet.node import OVSBridge, Host
from os.path import dirname, realpath, join
from subprocess import run
from sys import argv
import os


os.system("sudo mn -c")

interfaces = ["r1-wdm1", "r1-wdm2","r1-wdm3","r1-wdm4","r1-wdm5","r1-wdm6","r1-wdm7","r1-wdm8","r1-wdm9","r1-wdm10",
"r1-wdm21", "r1-wdm22","r1-wdm23","r1-wdm24","r1-wdm25","r1-wdm26","r1-wdm27","r1-wdm28","r1-wdm29","r1-wdm30",
"r2-wdm11", "r2-wdm12","r2-wdm13","r2-wdm14","r2-wdm15","r2-wdm16","r2-wdm17","r2-wdm18","r2-wdm19","r2-wdm20",
"r2-wdm21", "r2-wdm22","r2-wdm23","r2-wdm24","r2-wdm25","r2-wdm26","r2-wdm27","r2-wdm28","r2-wdm29","r2-wdm20", "s1-eth1",
"s1-eth2","s2-eth1","s2-eth2","s3-eth1","s4-eth1","t1-wdm1","t2-wdm2","t3-wdm3","t4-wdm4","t5-wdm5","t6-wdm6","t7-wdm7",
"t8-wdm8","t9-wdm9","t10-wdm10","t11-wdm11","t12-wdm12","t13-wdm13","t14-wdm14","t15-wdm15","t16-wdm16","t17-wdm17","t18-wdm18","t19-wdm19",
"t20-wdm20","h1-eth0","t1-eth1"]

for interface in interfaces:
    subprocess.run(["sudo","ip","link","delete", interface])


##
# Globals
##########
# time (sec), cwnd (MSS)
#tcpprobe_csv_header = ['time', 'src_addr_port', 'dst_addr_port', 'bytes', 'next_seq', 'unacknowledged', 'cwnd',
#                       'slow_start', 'swnd', 'smoothedRTT', 'rwnd']
# time (YYYYMMDDHHMMSS), interval (S.S-S.S), bps (bps)
iperf_csv_header = ['time', 'src_addr', 'src_port', 'dst_addr' ,'dst_port', 'other', 'interval', 'B_sent', 'bps']


class DumbbellTopo(Topo):

    def build(self, delay=2):
        """ Create the topology by overriding the class parent's method.

            :param  delay   One way propagation delay, delay = RTT / 2. Default is 2ms.
        """
        # The bandwidth (bw) is in Mbps, delay in milliseconds and queue size is in packets
        br_params = dict(bw=200, delay='{0}ms'.format(delay), max_queue_size=82*delay,
                         use_htb=True)  # backbone router interface tc params
        ar_params = dict(bw=100, delay='0ms', max_queue_size=(21*delay*20)/100,
                         use_htb=True)  # access router intf tc params
        # TODO: remove queue size from hosts and try.
        hi_params = dict(bw=960, delay='0ms', max_queue_size=80*delay, use_htb=True)  # host interface tc params

        # Create routers s1 to s4
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')
        s4 = self.addSwitch('s4')



###################################################
        # Link backbone routers (s1 & s2) together
        self.addLink(s1, s2, cls=TCLink, **br_params)

        
###################################################
        # Link access routers (s3 & s4) to the backbone routers
        self.addLink(s1, s3, cls=TCLink, **ar_params)
        self.addLink(s2, s4, cls=TCLink, **ar_params)

        # Create the hosts h1 to h4, and link them to access router 1
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        h3 = self.addHost('h3')
        h4 = self.addHost('h4')

        # Link the source hosts (h1 & h3) to access router 1 (s3)
        self.addLink(s3, h1, cls=TCLink, **hi_params)
        self.addLink(s3, h3, cls=TCLink, **hi_params)
        
        # Link the receiver hosts (h2 & h4) to access router 2 (s4)
        self.addLink(s4, h2, cls=TCLink, **hi_params)
        self.addLink(s4, h4, cls=TCLink, **hi_params)
        



#def draw_fairness_plot(time_h1, bw_h1, time_h3, bw_h3, alg, delay,Ganho_Amp):
def draw_fairness_plot(time_h1, bw_h1, time_h3, bw_h3, alg, delay):
    """ Draw the fairness plot for the iperf client hosts.
    """
    print('*** Drawing the fairness plot...')
    plt.plot(time_h1, bw_h1, label='Source Host 1 (h1)')
    plt.plot(time_h3, bw_h3, label='Source Host 2 (h3)')

    plt.xlabel('Time (sec)')
    plt.ylabel('Bandwidth (Mbps)')
    plt.ylim(0,120)
    plt.grid()

#    plt.title("TCP Fairness Graph\n{0} TCP Cong Control Alg Delay={1}ms Ganho Ampl={2}dB"
#              .format(alg.capitalize(), delay,Ganho_Amp))

    plt.title("TCP Fairness Graph\n{0} TCP Cong Control Alg Delay={1}ms"
              .format(alg.capitalize(), delay))

    plt.legend()
#    plt.grid(1250,100)

    plt.savefig('fairness_graph_{0}_{1}ms'.format(alg, delay))
    plt.close()


def dumbbell_test():
    """ Create and test a dumbbell network.
    """
    topo = DumbbellTopo(delay=21)
    net = Mininet(topo)
    net.start()

    print("Dumping host connections...")
    dumpNodeConnections(net.hosts)

    print("Testing network connectivity...")
    h1, h2 = net.get('h1', 'h2')
    h3, h4 = net.get('h3', 'h4')

    for i in range(1, 10):
        net.pingFull(hosts=(h1, h2))

    for i in range(1, 10):
        net.pingFull(hosts=(h2, h1))

    for i in range(1, 10):
        net.pingFull(hosts=(h4, h3))

    for i in range(1, 10):
        net.pingFull(hosts=(h3, h4))

    print("Testing bandwidth between h1 and h2...")
    net.iperf(hosts=(h1, h2), fmt='m', seconds=10, port=5001)

    print("Testing bandwidth between h3 and h4...")
    net.iperf(hosts=(h3, h4), fmt='m', seconds=10, port=5001)

    print("Stopping test...")
    net.stop()


#def parse_iperf_data(alg, delay, host_addrs, Ganho_Amp):
def parse_iperf_data(alg, delay, host_addrs):
    """ Parse the iperf data files for the given algorithm and RTT.

        :param  alg         String with the TCP congestion control algorithms data to parse.
        :param  delay       Integer with the delay data to parse.
        :param  host_addrs  Dictionary with the host names as keys and their addresses as values.
    """
    print('*** Parsing iperf data...')
    data = dict({'h1': {'Mbps': list(), 'time': list()}, 'h2': {'Mbps': list(), 'time': list()},
                 'h3': {'Mbps': list(), 'time': list()}, 'h4': {'Mbps': list(), 'time': list()}})

    # Use time's first value as time=0, and convert the bps to Mbps
    first_row = True
    with open('iperf_{0}_h1-h2_{1}ms.txt'.format(alg, delay),'r+') as fcsv:
        r = csv.DictReader(fcsv, delimiter=',', fieldnames=iperf_csv_header)
        for row in r:
            if host_addrs['h1'] in row['src_addr']:
                time = mktime(datetime.strptime(str(row['time']), '%Y%m%d%H%M%S').timetuple())

                # On the first row set up the required values. Then, check for repeated timestamps and fix that
                if first_row:
                    time_init = time
                    first_row = False
                    data['h1']['time'].append(time - time_init)
                elif time-time_init == data['h1']['time'][-1]:
                    data['h1']['time'].append(time - time_init + 1)
                else:
                    data['h1']['time'].append(time - time_init)
                data['h1']['Mbps'].append(int(row['bps'])/1000000)
    # Pop the last row because it is the average bandwidth of the session
    print('h1: time={0}, bandwidth={1}'.format(data['h1']['time'].pop(), data['h1']['Mbps'].pop()))

    # Use time's first value obtained for the previous host as time=0 since the seconds iperf command was started with
    # a few seconds after the first cmd, and convert the bps to Mbps
    first_row = True
   

    with open('iperf_{0}_h3-h4_{1}ms.txt'.format(alg, delay), 'r+') as fcsv:
        r = csv.DictReader(fcsv, delimiter=',', fieldnames=iperf_csv_header)
        for row in r:
            if host_addrs['h3'] in row['src_addr']:
                time = mktime(datetime.strptime(str(row['time']), '%Y%m%d%H%M%S').timetuple())
                # Check for repeated timestamps and fix that
                if first_row:
                    first_row = False
                    data['h3']['time'].append(time - time_init)
                elif time-time_init == data['h3']['time'][-1]:
                    data['h3']['time'].append(time - time_init + 1)
                else:
                    data['h3']['time'].append(time - time_init)
                data['h3']['Mbps'].append(int(row['bps'])/1000000)
    # Pop the last row because it is the average bandwidth of the session
    print('h3: time={0}, bandwidth={1}'.format(data['h3']['time'].pop(), data['h3']['Mbps'].pop()))

    return data




def test(net):
    "Run config script and simple test"
    testdir = dirname(realpath(argv[0]))
    # Note config-singlelink.sh works for us as well
    script = join(testdir, 'config-singlelink.sh')
    run(script)
    assert net.pingAll() == 0



def tcp_tests(algs, delays, iperf_runtime, iperf_delayed_start):
    """ Run the TCP congestion control tests.

        :param  algs                List of strings with the TCP congestion control algorithms to test.
        :param  delays              List of integers with the one-directional propagation delays to test.
        :param  iperf_runtime       Time to run the iperf clients in seconds.
        :param  iperf_delayed_start Time to wait before starting the second iperf client in seconds.
    """
    print("*** Tests settings:\n - Algorithms: {0}\n - delays: {1}\n - Iperf runtime: {2}\n - Iperf delayed start: {3}"
          .format(algs, delays, iperf_runtime, iperf_delayed_start))
    for alg in algs:
        print('*** Starting test for algorithm={0}...'.format(alg))
        for delay in delays:
            print('*** Starting test for delay={0}ms...'.format(delay))



            # Create the net topology
            print('*** Creating topology for delay={0}ms...'.format(delay))
            topo = DumbbellTopo(delay=delay)

            # Start mininet
            net = Mininet(topo)
        
            restServer = RestServer(net)
            net.start()
     
            # Get the hosts
            h1, h2, h3, h4 = net.get('h1', 'h2', 'h3', 'h4')
            host_addrs = dict({'h1': h1.IP(), 'h2': h2.IP(), 'h3': h3.IP(), 'h4': h4.IP()})
            print('Host addrs: {0}'.format(host_addrs))
            
            
    


            # Run iperf
            popens = dict()
            print("*** Starting iperf servers h2 and h4...")
            popens[h2] = h2.popen(['iperf', '-s', '-p', '5001', '-w', '16m'])
            popens[h4] = h4.popen(['iperf', '-s', '-p', '5001', '-w', '16m'])

            # Client options:
            # -i: interval between reports set to 1sec
            # -l: length read/write buffer set to default 8KB
            # -w: TCP window size (socket buffer size) set to 16MB
            # -M: TCP MSS (MTU-40B) set to 1460B for an MTU of 1500B
            # -N: disable Nagle's Alg
            # -Z: select TCP Congestion Control alg
            # -t: transmission time
            # -f: format set to kilobits
            # -y: report style set to CSV
            # TODO: run iperfs without the -y C to see if we get errors setting the MSS. Use sudo?
            print("*** Starting iperf client h1...")

            popens[h1] = h1.popen('iperf -c {0} -p 5001 -i 1 -w 16m -M 1460 -N -Z {1} -t {2} -y C > \
                                   iperf_{1}_{3}_{4}ms.txt'
                                  .format(h2.IP(), alg, iperf_runtime, 'h1-h2', delay), shell=True)

            # Delay before starting the second iperf proc
            print("*** Waiting for {0}sec...".format(iperf_delayed_start))
            sleep(iperf_delayed_start)

            print("*** Starting iperf client h3...")
            popens[h3] = h3.popen('iperf -c {0} -p 5001 -i 1 -w 16m -M 1460 -N -Z {1} -t {2} -y C > \
                                   iperf_{1}_{3}_{4}ms.txt'
                                  .format(h4.IP(), alg, iperf_runtime, 'h3-h4', delay), shell=True)

            # Wait for clients to finish sending data
            print("*** Waiting {0}sec for iperf clients to finish...".format(iperf_runtime))
            popens[h1].wait()
            popens[h3].wait()

            # Terminate the servers and tcpprobe subprocesses
            print('*** Terminate the iperf servers and tcpprobe processes...')
            popens[h2].terminate()
            popens[h4].terminate()
         

            popens[h2].wait()
            popens[h4].wait()

            print("*** Stopping test...")
            net.stop()

            print('*** Processing data...')

            data_fairness = parse_iperf_data(alg, delay, host_addrs)


            draw_fairness_plot(data_fairness['h1']['time'], data_fairness['h1']['Mbps'],
                               data_fairness['h3']['time'], data_fairness['h3']['Mbps'], alg, delay)


if __name__ == '__main__':
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='TCP Congestion Control tests in a dumbbell topology.')
    parser.add_argument('-a', '--algorithms', nargs='+', default=['reno', 'bic', 'cubic', 'bbr'],
                        help='List TCP Congestion Control algorithms to test.')
    parser.add_argument('-d', '--delays', nargs='+', type=int, default=[10, 50, 75, 100],
                        help='List of backbone router one-way propagation delays to test.')
    parser.add_argument('-i', '--iperf-runtime', type=int, default=1000, help='Time to run the iperf clients.')
    parser.add_argument('-j', '--iperf-delayed-start', type=int, default=250,
                        help='Time to wait before starting the second iperf client.')
    parser.add_argument('-l', '--log-level', default='info', help='Verbosity level of the logger. Uses `info` by default.')
    parser.add_argument('-t', '--run-test', action='store_true', help='Run the dumbbell topology test.')

    args = parser.parse_args()

    if args.log_level:
        # Tell mininet to print useful information
        setLogLevel(args.log_level)
    else:
        setLogLevel('info')

    if args.run_test:
        dumbbell_test()
    else:
        # Run tests
        #tcp_reno_test(['reno', 'cubic'], [21, 81, 162], 1000, 250)
        tcp_tests(args.algorithms, args.delays, args.iperf_runtime, args.iperf_delayed_start)




