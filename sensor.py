from serial import Serial


class Sensor(Serial):
    def __init__(self, port, baudrate=9600, timeout=0.1, bytesize=8, parity='N', stopbits=1):
        super().__init__(port)
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits

    def recv(self):
        self.flush()
        return self.readline().decode('utf-8')

    def estimate(self):
        cnt = 0
        res = 0
        while cnt < 100:
            if not self.recv():
                continue
            if res == 0:
                res = float(self.recv())
            res = min(res, float(self.recv()))
            cnt += 1
        return 160*res/5-80


if __name__ == "__main__":
    s = Sensor("COM6")
    print(s.estimate())
