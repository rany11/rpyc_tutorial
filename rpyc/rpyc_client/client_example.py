import rpyc


def on_file_change(oldstat, newstat):
    print("file changed")
    print("old stat: ", oldstat)
    print("new stat: ", newstat)


if __name__ == "__main__":
    f = open("..\\stam.txt", "w")
    conn = rpyc.connect("localhost", 18871)
    bgsrv = rpyc.BgServingThread(conn)
    mon = conn.root.FileMonitor("..\\stam.txt", on_file_change)

    f.write("shmoop")
    f.flush()
    f.write("shmoopsy")
    f.flush()

    f.close()
    mon.stop()
    bgsrv.stop()
    conn.close()


