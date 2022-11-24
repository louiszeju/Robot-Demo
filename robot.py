import numpy as np
from time import sleep
from threading import Thread
from robot_api.dobot_api import MyType, DobotApi, DobotApiMove, DobotApiDashboard


class RobotExec:
    def __init__(self):
        # TCP/IP protocol settings
        self.ip = "192.168.1.6"
        self.dashboard_port = 29999
        self.move_port = 30003
        self.feed_port = 30004

        self.feed_data = None

    def connect_robot(self):
        dashboard = DobotApiDashboard(self.ip, self.dashboard_port)
        move = DobotApiMove(self.ip, self.move_port)
        feed = DobotApi(self.ip, self.feed_port)
        return dashboard, move, feed

    def get_feed(self, feed: DobotApi):
        hasRead = 0
        while True:
            data = bytes()
            while hasRead < 1440:
                temp = feed.socket_dobot.recv(1440 - hasRead)
                if len(temp) > 0:
                    hasRead += len(temp)
                    data += temp
            hasRead = 0

            a = np.frombuffer(data, dtype=MyType)
            if hex((a['test_value'][0])) == '0x123456789abcdef':
                # Refresh Properties
                self.feed_data = a
                # print(a["tool_vector_actual"][0])

            # sleep(0.001)

    # point_list --> [x, y, z, R] (mm, mm, mm, degrees)
    def wait_arrive(self, point_list: list):
        while True:
            is_arrive = True

            if self.feed_data is not None:
                for index in range(4):
                    if abs(self.feed_data["tool_vector_actual"][0][index] - point_list[index]) > 1:
                        is_arrive = False

                if is_arrive:
                    return

            # sleep(0.001)


if __name__ == "__main__":
    robot = RobotExec()
    dashboard_r, move_r, feed_r = robot.connect_robot()
    dashboard_r.EnableRobot()
    dashboard_r.PayLoad(10, 0)
    dashboard_r.Tool(1)
    feed_thread = Thread(target=robot.get_feed, args=(feed_r,))
    feed_thread.setDaemon(True)
    feed_thread.start()
    print("执行坐标系0...")
    point_a = [338, -45, -70, 4]
    point_b = [338, -45, -163, 4]
    point_c = [400, -45, -70, 4]
    point_d = [400, -45, -160, 4]
    # move_r.MovL(point_a[0], point_a[1], point_a[2], point_a[3])
    # # robot.wait_arrive(point_a)
    # move_r.MovL(point_b[0], point_b[1], point_b[2], point_b[3])
    # # robot.wait_arrive(point_b)
    # sleep(1)
    # dashboard_r.DO(1, 1)
    # move_r.MovL(point_c[0], point_c[1], point_c[2], point_c[3])
    # # robot.wait_arrive(point_c)
    # move_r.MovL(point_d[0], point_d[1], point_d[2], point_d[3])
    # # robot.wait_arrive(point_d)
    # dashboard_r.DO(1, 0)
