import pyrealsense2 as rs
import numpy as np
import cv2


class Camera:
    def __init__(self):

        # Configure color streams
        self.pipeline = rs.pipeline()
        self.config = rs.config()

        # aruco tag configuration
        self.aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_ARUCO_ORIGINAL)
        self.arucoParams = cv2.aruco.DetectorParameters_create()

        self.color_image = None
        self.calibration_status = False

        # aruco tage center point
        self.cX = 0
        self.cY = 0

        # panel center point
        self.pX = 0
        self.pY = 0

    def enable_camera(self):
        pipeline_wrapper = rs.pipeline_wrapper(self.pipeline)
        pipeline_profile = self.config.resolve(pipeline_wrapper)
        device = pipeline_profile.get_device()
        print(str(device.get_info(rs.camera_info.product_line)))

        self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

        # Start streaming
        self.pipeline.start(self.config)

    def detection(self):
        # Wait for a coherent pair of color frame
        frames = self.pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()

        # Convert images to numpy arrays
        color_image = np.asanyarray(color_frame.get_data())

        # aruco tag detection
        corners, ids, rejected = cv2.aruco.detectMarkers(color_image, self.aruco_dict, parameters=self.arucoParams)

        if not self.calibration_status:
            self._panel_detection(color_image)
        else:
            self._aruco_detection(corners, ids, color_image)

    def _aruco_detection(self, corners, ids, color_image):
        if len(corners) > 0:
            ids = ids.flatten()
            for markerCorner, markerID in zip(corners, ids):
                corners = markerCorner.reshape((4, 2))
                topLeft, topRight, bottomRight, bottomLeft = corners
                topRight = (int(topRight[0]), int(topRight[1]))
                bottomRight = (int(bottomRight[0]), int(bottomRight[1]))
                bottomLeft = (int(bottomLeft[0]), int(bottomLeft[1]))
                topLeft = (int(topLeft[0]), int(topLeft[1]))
                cv2.line(color_image, topLeft, topRight, (0, 255, 0), 2)
                cv2.line(color_image, topRight, bottomRight, (0, 255, 0), 2)
                cv2.line(color_image, bottomRight, bottomLeft, (0, 255, 0), 2)
                cv2.line(color_image, bottomLeft, topLeft, (0, 255, 0), 2)

                # calculate and draw the center of tags
                self.cX = int((topLeft[0] + bottomRight[0]) / 2.0)
                self.cY = int((topLeft[1] + bottomRight[1]) / 2.0)
                cv2.circle(color_image, (self.cX, self.cY), 2, (0, 0, 255), -1)
                cv2.putText(color_image, f"[{self.cX}, {self.cY}]", (self.cX + 40, self.cY),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 1)

        self.color_image = color_image

    def _panel_detection(self, color_image):
        gray = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        binary = cv2.Canny(gray, 30, 120)
        # turn grey image into binary image(edge)
        # tuning parameter cv2.Canny(image,low_threshold',high_threshold)
        # The high_threshold shall be set as 3 times the low_threshold following Canny's recommendation .
        contours, hierarchy = cv2.findContours(binary,
                                               cv2.RETR_EXTERNAL,
                                               cv2.CHAIN_APPROX_SIMPLE)
        for i in range(len(contours)):
            # filter small area
            area = cv2.contourArea(contours[i])
            if area < 800:
                continue
            rect = cv2.minAreaRect(contours[i])
            # calculate corners coordinate
            box = cv2.boxPoints(rect)
            box = np.int0(box)
            # x, y = rect[0]

            #get four vertices' coordinate

            left_point_x = np.min(box[:, 0])
            right_point_x = np.max(box[:, 0])
            top_point_y = np.min(box[:, 0])
            bottom_point_y = np.max(box[:, 0])

            left_point_y = box[:, 1][np.where(box[:, 0] == left_point_x)][0]
            right_point_y = box[:, 1][np.where(box[:, 0] == right_point_x)][0]




            left_point_x = np.min(box[:, 0])


            panelHei, panelWid = rect[1]
            self.pX0 = int((box[0][0] + box[2][0]) / 2.0)
            self.pY0 = int((box[0][1] + box[2][1]) / 2.0)
            self.pX1 = int((box[0][0] + box[2][0]) / 2.0 + panelWid / 7.0 * 2.0)
            self.pY1 = int((box[0][1] + box[2][1]) / 2.0)
            self.pX2 = int((box[0][0] + box[2][0]) / 2.0 + panelWid / 7.0 * 2.0)
            self.pY2 = int((box[0][1] + box[2][1]) / 2.0 + panelHei / 7.0 * 2.0)
            self.pX3 = int((box[0][0] + box[2][0]) / 2.0)
            self.pY3 = int((box[0][1] + box[2][1]) / 2.0 + panelHei / 7.0 * 2.0)
            self.pX4 = int((box[0][0] + box[2][0]) / 2.0 - panelWid / 7.0 * 2.0)
            self.pY4 = int((box[0][1] + box[2][1]) / 2.0 + panelHei / 7.0 * 2.0)
            self.pX5 = int((box[0][0] + box[2][0]) / 2.0 - panelWid / 7.0 * 2.0)
            self.pY5 = int((box[0][1] + box[2][1]) / 2.0)
            self.pX6 = int((box[0][0] + box[2][0]) / 2.0 - panelWid / 7.0 * 2.0)
            self.pY6 = int((box[0][1] + box[2][1]) / 2.0 - panelHei / 7.0 * 2.0)
            self.pX7 = int((box[0][0] + box[2][0]) / 2.0)
            self.pY7 = int((box[0][1] + box[2][1]) / 2.0 - panelHei / 7.0 * 2.0)
            self.pX8 = int((box[0][0] + box[2][0]) / 2.0 + panelWid / 7.0 * 2.0)
            self.pY8 = int((box[0][1] + box[2][1]) / 2.0 - panelHei / 7.0 * 2.0)


            # define the center and other 8 points of the panel.
            self.px = [self.pX0, self.pX1, self.pX2, self.pX3, self.pX4, self.pX5, self.pX6, self.pX7, self.pX8]
            self.py = [self.pY0, self.pY1, self.pY2, self.pY3, self.pY4, self.pY5, self.pY6, self.pY7, self.pY8]

            cv2.circle(color_image, (self.pX, self.pY), 2, (0, 0, 255), -1)

            #putText Panel
            cv2.putText(color_image, f"[{self.pX}, {self.pY}]", (self.pX + 40, self.pY),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 1)




            cv2.drawContours(color_image, [box], 0, (0, 255, 0), 2)

        self.color_image = color_image
