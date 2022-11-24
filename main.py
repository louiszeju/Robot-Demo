import sys
import csv
import time
from threading import Thread
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import QMessageBox, QMainWindow, QWidget
from qtwidgets import AnimatedToggle

from vision_api.camera import Camera
from vision_api.handeye_calibration import Calibration
from robot_api.robot import RobotExec, DobotApiDashboard, DobotApiMove, DobotApi
from UI.FTT import Ui_MainWindow
from UI.calib import Ui_Form
from vision_api.sensor import Sensor


class MainUI(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # initialize hand-eye calibration window
        self.calibration_ui = CalibUI()
        self.calibration_ui.signal_out.connect(self.get_pos_data)
        self.calibration_ui.signal_camera.connect(self.switch_detection_mode)

        # realsense camera
        self.cam = Camera()
        self.timer = QtCore.QTimer()
        self.camera_status = False

        # MG400 Robot
        self.robot = RobotExec()
        self.robot_status = False
        self.dashboard: DobotApiDashboard
        self.move: DobotApiMove
        self.feed: DobotApi

        # read hand-eye vision_api data
        self.calib = Calibration("vision_api/calibration_data.csv")

        # initialize thickness gauge table
        self.tableWidget.setColumnCount(10)
        self.tableWidget.setHorizontalHeaderLabels(["Avg", "①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨"])
        self.tableWidget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        # toggle connections
        self._add_toggles()

        # slot connections
        self._init_features()

        # deep sensor
        self.sensor = Sensor("COM6")

    # ============================ Start Task & Export Data ============================
    # put your code here
    # walk 9 points and detect film thickness
    # go back to origin after tasks finished
    def start_task(self):


        sens = self.sensor.estimate()
        # sens = distance data retrived from laser sensor.
        if not self.robot_status or not self.camera_status:
            QMessageBox.warning(self, "Task Starting Error",
                                f"Robot: <{'Not Connected' if not self.robot_status else 'Connected'}>\r"
                                f"Camera: <{'Not Connected' if not self.camera_status else 'Connected'}>",
                                QMessageBox.Ok)

        else:
            robot_X = []
            robot_Y = []

            for i in range(9):
                robot_x, robot_y = self.calib.transfer_camera2robot(self.cam.px[i], self.cam.py[i])
                robot_X.append(robot_x)
                robot_Y.append(robot_y)

            self.move.MovL(275, -30, 130, 46)
            for i in range(9):
                # self.move.MovL(robot_X[i], robot_Y[i], -172, 46)
                self.move.MovL(robot_X[i], robot_Y[i], -166, 46)
                # self.dashboard.DO(1, 1)
                # time.sleep(1)
                self.move.MovL(robot_X[i], robot_Y[i], -150, 46)

            self.move.MovL(robot_X[4], robot_Y[4], -166, 46)

            self.dashboard.DO(1, 1)
            self.dashboard.DO(1, 0)
            self.move.MovL(275, -30, 130, 46)


            #test with code
            # for i in range(9):
            #     # self.move.MovL(robot_X[i], robot_Y[i], -172, 46)
            #     self.move.MovL(robot_X[i], robot_Y[i], -123, 46)
            #     # self.dashboard.DO(1, 1)
            #     # time.sleep(1)
            #     self.move.MovL(robot_X[i], robot_Y[i], -100, 46)
            #
            # self.dashboard.DO(1, 0)
            # self.move.MovL(275, -30, 130, 46)

            # use for test
            # robot_x, robot_y = self.calib.transfer_camera2robot(494, 172)
            # self.move.MovL(robot_x, robot_y, -123, 46)
            # time.sleep(5)
            # self.move.MovL(275, -30, 130, 46)

    def export_measurement_data(self):
        pass

    def test_insert(self):
        self.tableWidget.setRowCount(3)
        # for i in range(0, 3):
        #     for j in range(1, 10):
        #         self.tableWidget.setItem(i, j, QtWidgets.QTableWidgetItem(str(random.randint(50, 80))))
        #         sleep(0.1)
        self.insert_data(0, [56, 67, 78, 47, 95, 13, 80, 30, 55])

    def insert_data(self, panel_num, data: list):
        for i in range(1, 10):
            self.tableWidget.setItem(0, i, QtWidgets.QTableWidgetItem(str(data[i-1])))
        self.tableWidget.setItem(panel_num, 0, QtWidgets.QTableWidgetItem(str(round(sum(data)/len(data), 1))))

    # ============================ Realsense D455i Camera Features ============================
    def load_stream(self):
        try:
            if not self.camera_status:
                if not self.timer.isActive():
                    self.cam.enable_camera()
                    self.timer.start(30)
                    self.camera_status = True
                    self.Button_camera.setText("Close Camera")
                    self.label_camera_status.setStyleSheet("background-color: green")
            else:
                self.close_camera()
                self.camera_status = False
                self.Button_camera.setText("Open Camera")
                self.label_camera_status.setStyleSheet("background-color: red")

        except RuntimeError as e:
            QMessageBox.warning(self, "Camera Error", f"{e}", QMessageBox.Ok)

    def show_image(self):
        self.cam.detection()
        image = QtGui.QImage(self.cam.color_image, 640, 480, QtGui.QImage.Format_BGR888)
        self.label_image.setPixmap(QtGui.QPixmap.fromImage(image))

    def switch_detection_mode(self):
        self.cam.calibration_status = False

    def close_camera(self):
        self.timer.stop()
        self.cam.config.disable_all_streams()
        self.cam.pipeline.stop()

    # ============================ MG400 Features ============================
    def control_robot(self):
        try:
            if not self.robot_status:
                self.dashboard, self.move, self.feed = self.robot.connect_robot()
                Thread(target=self.robot.get_feed, args=(self.feed,), daemon=True).start()
                self.dashboard.EnableRobot()
                self.check_robot_mode()

                self.robot_status = True
                self.Button_robot.setText("Disconnect Robot")
                self.label_robot_status.setStyleSheet("background-color: green")
            else:
                self.dashboard.DisableRobot()
                self.check_robot_mode()
                self.dashboard.socket_dobot.close()
                self.move.socket_dobot.close()
                self.feed.socket_dobot.close()

                self.robot_status = False
                self.Button_robot.setText("Connect Robot")
                self.label_robot_status.setStyleSheet("background-color: red")

        except Exception as e:
            QMessageBox.warning(self, "Robot Error", f"{str(e).split(',')[0][2:-2]}", QMessageBox.Ok)

    def enable_switch_robot(self):
        if self.enable_robot_toggle.isChecked():
            if self.robot_status:
                self.dashboard.EnableRobot()
            self.enable_robot_toggle.setCheckState(QtCore.Qt.Checked)
        else:
            if self.robot_status:
                self.dashboard.DisableRobot()
            self.enable_robot_toggle.setCheckState(QtCore.Qt.Unchecked)

    def check_robot_mode(self):
        if self.robot.feed_data["robot_mode"][0] == 5:
            self.enable_robot_toggle.setCheckState(QtCore.Qt.Checked)
        elif self.robot.feed_data["robot_mode"][0] == 4:
            self.enable_robot_toggle.setCheckState(QtCore.Qt.Unchecked)

    # ============================ Hand-Eye Calibration ============================
    def enable_calibration(self):
        if not self.robot_status or not self.camera_status:
            QMessageBox.warning(self, "Calibration Error",
                                f"Robot: <{'Not Connected' if not self.robot_status else 'Connected'}>\r"
                                f"Camera: <{'Not Connected' if not self.camera_status else 'Connected'}>",
                                QMessageBox.Ok)
        else:
            reply = QMessageBox.warning(self, "Hand-eye Calibration", "Updating the hand-eye calibration may change "
                                                                      "programmed positions. "
                                                                      "Are you sure want to proceed?",
                                        QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.calibration_ui.show()
                self.cam.calibration_status = True

    def get_pos_data(self):
        self.calibration_ui.robot_x = self.robot.feed_data["tool_vector_actual"][0][0]
        self.calibration_ui.robot_y = self.robot.feed_data["tool_vector_actual"][0][1]
        self.calibration_ui.marker_x = self.cam.cX
        self.calibration_ui.marker_y = self.cam.cY

    # ============================ Slot & Signal ============================
    def _add_toggles(self):
        # toggle to enable and disable robot
        self.enable_robot_toggle = AnimatedToggle(
            checked_color="#FFB000",
            pulse_checked_color="#44FFB000")
        self.gridLayout_robot.addWidget(self.enable_robot_toggle)

    def pause_task(self):
        if self.robot_status:
            self.dashboard.DisableRobot()
            self.robot_status = False
            stop = QMessageBox.warning(self, "Stop", "The robot movement is now terminated. "
                                                     "Please click again to initialize it. ")
        else:
            # self.dashboard.
            self.dashboard.EnableRobot()
            self.robot_status = True
            self.move.MovL(275, -30, 130, 46)

    def _init_features(self):
        self.Button_camera.clicked.connect(self.load_stream)
        self.Button_robot.clicked.connect(self.control_robot)
        self.Button_9pt_calibration.clicked.connect(self.enable_calibration)
        self.Button_start.clicked.connect(self.start_task)
        self.Button_export.clicked.connect(self.export_measurement_data)
        self.enable_robot_toggle.clicked.connect(self.enable_switch_robot)
        self.timer.timeout.connect(self.show_image)
        self.Button_stop.clicked.connect(self.pause_task)

    def closeEvent(self, event):
        self.calibration_ui.close()


class CalibUI(QWidget, Ui_Form):
    signal_out = QtCore.pyqtSignal()
    signal_camera = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.retranslateUi(self)

        self._init_features()

        # initialize the robot and marker pose
        self.robot_x = 0
        self.robot_y = 0
        self.marker_x = 0
        self.marker_y = 0

        # initialize tableView model
        self.model = QtGui.QStandardItemModel(0, 4)
        self.cnt_robot = 0
        self.cnt_marker = 0
        self.init_table(self.model)

    def record_pos(self, marker: bool, robot: bool):
        self.signal_out.emit()

        if marker:
            self.model.setItem(self.cnt_marker, 0, QtGui.QStandardItem(str(self.marker_x)))
            self.model.setItem(self.cnt_marker, 1, QtGui.QStandardItem(str(self.marker_y)))
            self.cnt_marker += 1

        elif robot:
            print(ui.robot.feed_data["tool_vector_actual"])
            ui.dashboard.ClearError()
            ui.dashboard.EnableRobot()
            ui.calibration_ui.robot_x = ui.robot.feed_data["tool_vector_actual"][0][0]
            ui.calibration_ui.robot_y = ui.robot.feed_data["tool_vector_actual"][0][1]
            ui.calibration_ui.robot_z = -150
            ui.calibration_ui.robot_r = 46

            ui.move.MovL(ui.calibration_ui.robot_x,ui.calibration_ui.robot_y,
                         ui.calibration_ui.robot_z,ui.calibration_ui.robot_r)
            # ui.move.MovL(275, -30, 130, 46)
            # ui.move.MovL(275, -30, 130, 46)


            self.model.setItem(self.cnt_robot, 2, QtGui.QStandardItem(str(round(self.robot_x, 1))))
            self.model.setItem(self.cnt_robot, 3, QtGui.QStandardItem(str(round(self.robot_y, 1))))
            self.cnt_robot += 1

    def export_data(self):
        if self.cnt_robot != self.cnt_marker:
            QMessageBox.warning(self, "Calibration Error", "Calibration data is incomplete!", QMessageBox.Ok)
        else:
            header = ["marker_X", "marker_Y", "robot_X", "robot_Y"]
            with open("vision_api/calibration_data.csv", 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(header)
                data = []
                for i in range(max(self.cnt_marker, self.cnt_robot)):
                    data.append([self.model.item(i, 0).text(), self.model.item(i, 1).text(),
                                 self.model.item(i, 2).text(), self.model.item(i, 3).text()])
                writer.writerows(data)
                QMessageBox.information(self, "Hand-eye vision_api",
                                        "Data saved in vision_api/calibration_data.csv", QMessageBox.Ok)

    def clear_data(self):
        indexes = self.tableView.selectionModel().selectedRows()
        selected_row = []
        for index in indexes:
            selected_row.append(index.row())
            selected_row.sort(key=int, reverse=True)
        for i in selected_row:
            self.model.removeRow(i)
        self.cnt_robot -= len(selected_row)
        self.cnt_marker -= len(selected_row)

    def init_table(self, model):
        model.setHorizontalHeaderLabels(["Marker_X", "Marker_Y", "Robot_X", "Robot_Y"])
        self.tableView.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.tableView.setModel(model)
        self.tableView.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

    def closeEvent(self, event):
        self.signal_camera.emit()

    # ============================ Slot & Signal ============================
    def _init_features(self):
        self.Button_get_robot_pos.clicked.connect(lambda: self.record_pos(robot=True, marker=False))
        self.Button_get_marker_pos.clicked.connect(lambda: self.record_pos(marker=True, robot=False))
        self.Button_clear.clicked.connect(self.clear_data)
        self.Button_export.clicked.connect(self.export_data)


if __name__ == "__main__":
    QtWidgets.QApplication.setAttribute(QtCore.Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    MainWindow = QtWidgets.QMainWindow()
    ui = MainUI()
    ui.show()
    sys.exit(app.exec_())
