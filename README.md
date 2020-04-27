# rpyc_tutorial

Contains server and client that communicating in rpyc.

To run the server execute (from the project's root directory): <i>python -m rpyc_slave.slave_server</i>

To run the client just run the <i>rpyc/rpyc_client/client.py</i> script with the ip_host, port_host parameters (default is "localhost", 18871).

The supported commands are:

  - upload {srcpath} {dstpath}
  - download {srcpath} {dstpath}
  - ps
  - ls {path}
  - exec {path} [args]
  - stat {path}
  - kill [-signo] {pid}
  - kill all
  - monitors
  - monitor {path} {logpath}
  - monitor -r {path}

  
