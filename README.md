# rpyc_tutorial

Contains server and client that communicate in rpyc (Python 3), for Windows (but should be cross-platform).

To run the server execute (from the project's root directory): <i>python -m rpyc_slave.slave_server</i>

To run the client just run the <i>rpyc/rpyc_client/client.py</i> script with the ip_host, port_host parameters (default is "localhost", 18871).

The supported commands are:

  - upload {srcpath} {dstpath}
    - uploads local {srcpath} file to the remote {dstpath} path   . 	
  - download {srcpath} {dstpath}
      - downloads the remote {srcpath} file to the local {dstpath} path.
  - ps
      - shows the process names and pid on the remote host.
  - ls {path}
      - shows a dirlist of the remote {path}.
  - exec {path} [args]
      - executes the executable in remote {path} with [args] as a new process.
  - stat {path}
      - shows stat of the file in the remote {path}.
  - kill [-signo] {pid}
      - sends signal [signo] to the remote process with pid {pid}. Default is [signo]=9.
  - kill all
      - kills all processes created by the exec command.
  - monitors
      - shows the monitors created by the monitor command.
  - monitor {path} {logpath}
      - monitors changes in the remote {path} and loggs them in the local file {logpath}.
  - monitor -r {path}
      - deletes a monitor of the remote file {path}.
  - rm -r --empy-files {path}
      - deletes all empty files from {path} and all its subdirectories.