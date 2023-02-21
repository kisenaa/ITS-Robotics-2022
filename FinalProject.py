#! /usr/bin/env python

import rospy
from geometry_msgs.msg import PoseStamped, Twist
from mavros_msgs.msg import State
from mavros_msgs.srv import CommandBool, CommandBoolRequest, SetMode, SetModeRequest
import numpy as np
import threading
import cv2
from mavros_msgs.msg import PositionTarget
import mediapipe as mp
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_hands = mp.solutions.hands



import cv2
import threading


class VideoCaptureThread:
    def __init__(self, video_source):
        self.video_capture = cv2.VideoCapture(video_source) # initialize video capture object
        self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280) # custom resolution
        self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.current_frame = None
        self.ret = None
        self.is_running = False

    def start(self):
        if self.is_running:
            print("Video capture is already running")
            return None
        self.is_running = True
        thread = threading.Thread(target=self._update, args=()) # create new thread to run update
        thread.start()
        return self

    def stop(self):
        self.is_running = False
        self.video_capture.release() # release video capture

    def _update(self):
        while self.is_running:
            ret, frame = self.video_capture.read() # get and read frame from video
            if ret:
                self.ret = ret
                self.current_frame = frame
            else:
                print("Error reading video capture.")
                self.stop()
                break

    def get_current_frame(self):
        return self.ret, self.current_frame


ARUCO_DICT = {
    'DICT_4X4_50': cv2.aruco.DICT_4X4_50,
    'DICT_4X4_100': cv2.aruco.DICT_4X4_100,
    'DICT_4X4_250': cv2.aruco.DICT_4X4_250,
    'DICT_4X4_1000': cv2.aruco.DICT_4X4_1000,
    'DICT_5X5_50': cv2.aruco.DICT_5X5_50,
    'DICT_5X5_100': cv2.aruco.DICT_5X5_100,
    'DICT_5X5_250': cv2.aruco.DICT_5X5_250,
    'DICT_5X5_1000': cv2.aruco.DICT_5X5_1000,
    'DICT_6X6_50': cv2.aruco.DICT_6X6_50,
    'DICT_6X6_100': cv2.aruco.DICT_6X6_100,
    'DICT_6X6_250': cv2.aruco.DICT_6X6_250,
    'DICT_6X6_1000': cv2.aruco.DICT_6X6_1000,
    'DICT_7X7_50': cv2.aruco.DICT_7X7_50,
    'DICT_7X7_100': cv2.aruco.DICT_7X7_100,
    'DICT_7X7_250': cv2.aruco.DICT_7X7_250,
    'DICT_7X7_1000': cv2.aruco.DICT_7X7_1000,
    'DICT_ARUCO_ORIGINAL': cv2.aruco.DICT_ARUCO_ORIGINAL,
    'DICT_APRILTAG_16h5': cv2.aruco.DICT_APRILTAG_16h5,
    'DICT_APRILTAG_25h9': cv2.aruco.DICT_APRILTAG_25h9,
    'DICT_APRILTAG_36h10': cv2.aruco.DICT_APRILTAG_36h10,
    'DICT_APRILTAG_36h11': cv2.aruco.DICT_APRILTAG_36h11,
    }

current_state = State()
global times
times = 0
global number_ids
number_ids=-1

global detect_status 
detect_status = 0

def state_cb(msg):
    global current_state
    current_state = msg

def local_position_cb(msg):
    global Position
    Position = msg


def pose_estimation(frame,aruco_dict_type,matrix_coefficients,distortion_coefficients):
    global times
    number_id = -1
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    cv2.aruco_dict = cv2.aruco.Dictionary_get(aruco_dict_type)
    parameters = cv2.aruco.DetectorParameters_create() # get aruco dictionary

    # detect any aruco marker in the frame
    (corners, ids, rejected_img_points) = cv2.aruco.detectMarkers(gray, cv2.aruco_dict, parameters=parameters,cameraMatrix=matrix_coefficients, distCoeff=distortion_coefficients)

    if len(corners) > 0:
        for i in range(0, len(ids)):
            (rvec, tvec, markerPoints) = \
                cv2.aruco.estimatePoseSingleMarkers(corners[i], 0.02, matrix_coefficients, distortion_coefficients)
                # draw the detected marker and estimated pose

            cv2.aruco.drawDetectedMarkers(frame, corners)

            cv2.aruco.drawAxis(frame,matrix_coefficients,distortion_coefficients,rvec,tvec,0.01,)

        ids = ids.flatten()

        for (markerCorner, markerID) in zip(corners, ids):
            # mencari corner pada gambar dan menuliskan teks
            corners = markerCorner.reshape((4, 2))
            (topLeft, topRight, bottomRight, bottomLeft) = corners

            topRight = (int(topRight[0]), int(topRight[1]))
            bottomRight = (int(bottomRight[0]), int(bottomRight[1]))
            bottomLeft = (int(bottomLeft[0]), int(bottomLeft[1]))
            topLeft = (int(topLeft[0]), int(topLeft[1]))

            cX = int((topLeft[0] + bottomRight[0]) / 2.0)
            cY = int((topLeft[1] + bottomRight[1]) / 2.0)
            cv2.circle(frame, (cX, cY), 4, (0, 0, 0xFF), -1)

            cv2.putText(frame,str(markerID),(topLeft[0], topLeft[1] - 10),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0, 0xFF, 0),2,)

            print("[Inference] ArUco marker ID: {}".format(markerID))
            number_id = markerID

            if number_id == 289 or number_id == 291 or number_id == 293 or number_id == 295 or number_id == 297 or number_id == 299 or number_id == 301:
                times = times + 1

    return frame, number_id


def takeoff(pose, altitude=2):

    # Setpoint publishing MUST be faster than 2Hz
    rate = rospy.Rate(20)

    # Wait for Flight Controller connection

    # Set initial position
    pose.pose.position.x = 0
    pose.pose.position.y = 0
    pose.pose.position.z = altitude

    # Send a few setpoints before starting
    for i in range(100):   

        if(rospy.is_shutdown()):
            break

        local_pos_pub.publish(pose)
        rate.sleep()

    # Set OFFBOARD mode
    offb_set_mode = SetModeRequest()
    offb_set_mode.custom_mode = 'OFFBOARD'

    last_req = rospy.Time.now()

    while(not rospy.is_shutdown()):


        if(current_state.mode != "OFFBOARD" and (rospy.Time.now() - last_req) > rospy.Duration(5.0)):
            if(set_mode_client.call(offb_set_mode).mode_sent == True):
                rospy.loginfo("OFFBOARD enabled")
            
            last_req = rospy.Time.now()
        else:
            # Arm the vehicle
            if(not current_state.armed and (rospy.Time.now() - last_req) > rospy.Duration(5.0)):
                arm_cmd = CommandBoolRequest()
                arm_cmd.value = True

                if(arming_client.call(arm_cmd).success == True):
                    rospy.loginfo("Vehicle armed")
            
                last_req = rospy.Time.now()

        # Publish setpoint
        local_pos_pub.publish(pose)

        if Position.pose.position.z >= 2.99 and Position.pose.position.z <= 3.5:
            rospy.loginfo("Altitude reached: %.2f m", Position.pose.position.z)
            break

def backward_x(pose,distance,altitude):
    pose.pose.position.x = Position.pose.position.x - distance
    pose.pose.position.y = 0
    pose.pose.position.z = altitude

    for i in range(100):   

        if(rospy.is_shutdown()):
            break

        local_pos_pub.publish(pose)
        rate.sleep()

    rospy.loginfo("Altitude reached: %.2f m", Position.pose.position.x)

def foward_x (pose,distance,altitude):
    pose.pose.position.x = distance + Position.pose.position.x
    pose.pose.position.y = 0
    pose.pose.position.z = altitude

    for i in range(100):   

        if(rospy.is_shutdown()):
            break

        local_pos_pub.publish(pose)
        rate.sleep()
        

    rospy.loginfo("Altitude reached: %.2f m", Position.pose.position.x)

def foward_y (pose,distance,altitude):
    pose.pose.position.x = 0
    pose.pose.position.y = distance + Position.pose.position.y
    pose.pose.position.z = altitude

    for i in range(100):   

        if(rospy.is_shutdown()):
            break

        local_pos_pub.publish(pose)
        rate.sleep()
        

    rospy.loginfo("Altitude reached: %.2f m", Position.pose.position.y)

def backward_y (pose,distance,altitude):
    pose.pose.position.x = 0
    pose.pose.position.y = Position.pose.position.y - distance
    pose.pose.position.z = altitude

    for i in range(100):   

        if(rospy.is_shutdown()):
            break

        local_pos_pub.publish(pose)
        rate.sleep()
        

    rospy.loginfo("Altitude reached: %.2f m", Position.pose.position.y)

def foward_z (pose,distance):
    pose.pose.position.x = 0
    pose.pose.position.y = 0
    pose.pose.position.z = distance + Position.pose.position.z

    for i in range(100):   

        if(rospy.is_shutdown()):
            break

        local_pos_pub.publish(pose)
        rate.sleep()
        

    rospy.loginfo("Altitude reached: %.2f m", Position.pose.position.z)

def backward_z (pose,distance):
    pose.pose.position.x = 0
    pose.pose.position.y = 0
    pose.pose.position.z = Position.pose.position.z - distance

    for i in range(100):   

        if(rospy.is_shutdown()):
            break

        local_pos_pub.publish(pose)
        rate.sleep()
        

    rospy.loginfo("Altitude reached: %.2f m", Position.pose.position.z)

def landing (pose):
    global detect_status 
    detect_status = 0

    pose.pose.position.x = Position.pose.position.x
    pose.pose.position.y = Position.pose.position.y
    pose.pose.position.z = 0

    for i in range(100):   

        if(rospy.is_shutdown()):
            break

        local_pos_pub.publish(pose)
        rate.sleep()
        
    rospy.loginfo("Altitude reached: %.2f m", Position.pose.position.z)

def colour_detect(img):
    global times
    amount = 0
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
# define range of blue color in HSV
    lower_blue = np.array([115,150,150])
    upper_blue = np.array([130,255,255])

# Threshold range to generate mask
    mask = cv2.inRange(hsv, lower_blue, upper_blue)

# Find contours in the mask
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

# Mencari Berapa banyak sisi dari contournya
    for i in contours:
        corner = cv2.approxPolyDP( i, 0.01 * cv2.arcLength(i, True), True)

    # If length of corner is 12 , then it will draw the countour 
        if len(corner) == 12:
        # Draw countour with green colour
            cv2.drawContours(img, [i], 0, (0,255,0), 6)
        # Put the text "Amount of corner"
            cv2.putText(img, f"{len(corner)}", (40,100), cv2.FONT_HERSHEY_DUPLEX, 3, (0, 0, 0), 3)
            amount = len(corner)
            times = times + 1
    
    return img, amount

def status_update():
    detect_status = 0


def hand_counter(image):
    with mp_hands.Hands(
    model_complexity=0,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5) as hands:

    # To improve performance, optionally mark the image as not writeable to
    # pass by reference.
        global times

        image.flags.writeable = False
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = hands.process(image)

    # Draw the hand annotations on the image.
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    # Initially set finger count to 0 for each cap
        fingerCount = 0

        if results.multi_hand_landmarks:

            for hand_landmarks in results.multi_hand_landmarks:
        # Get hand index to check label (left or right)
                handIndex = results.multi_hand_landmarks.index(hand_landmarks)
                handLabel = results.multi_handedness[handIndex].classification[0].label

        # Set variable to keep landmarks positions (x and y)
                handLandmarks = []

        # Fill list with x and y positions of each landmark
                for landmarks in hand_landmarks.landmark:
                    handLandmarks.append([landmarks.x, landmarks.y])

        # Test conditions for each finger: Count is increased if finger is 
        #   considered raised.
        # Thumb: TIP x position must be greater or lower than IP x position, 
        #   deppeding on hand label.
                if handLabel == "Left" and handLandmarks[4][0] > handLandmarks[3][0]:
                    fingerCount = fingerCount+1
                elif handLabel == "Right" and handLandmarks[4][0] < handLandmarks[3][0]:
                    fingerCount = fingerCount+1

        # Other fingers: TIP y position must be lower than PIP y position, 
        #   as image origin is in the upper left corner.
                if handLandmarks[8][1] < handLandmarks[6][1]:       #Index finger
                    fingerCount = fingerCount+1
                if handLandmarks[12][1] < handLandmarks[10][1]:     #Middle finger
                    fingerCount = fingerCount+1
                if handLandmarks[16][1] < handLandmarks[14][1]:     #Ring finger
                    fingerCount = fingerCount+1
                if handLandmarks[20][1] < handLandmarks[18][1]:     #Pinky
                    fingerCount = fingerCount+1

        # Draw hand landmarks 
                mp_drawing.draw_landmarks(
                image,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style())

    # Display finger count
        cv2.putText(image, str(fingerCount), (50, 450), cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 0, 0), 10)
        if fingerCount >= 1 and fingerCount <=3:
            times = times + 1

        return image, fingerCount


if __name__ == "__main__":
    rospy.init_node("offb_node_py")

    state_sub = rospy.Subscriber("mavros/state", State, callback = state_cb)

    local_pos_pub = rospy.Publisher("mavros/setpoint_position/local", PoseStamped, queue_size=10)
    
    rospy.wait_for_service("/mavros/cmd/arming")
    rospy.loginfo("arm client enabled")
    arming_client = rospy.ServiceProxy("mavros/cmd/arming", CommandBool)    

    rospy.wait_for_service("/mavros/set_mode")
    set_mode_client = rospy.ServiceProxy("mavros/set_mode", SetMode)

    PositionP = rospy.Subscriber("mavros/local_position/pose", PoseStamped, local_position_cb)

    pub_vel = rospy.Publisher('mavros/setpoint_velocity/cmd_vel_unstamped', Twist, queue_size=10)    
    vel = Twist()

    # Setpoint publishing MUST be faster than 2Hz
    rate = rospy.Rate(20)

    pose = PoseStamped()

    # Wait for Flight Controller connection
    while(not rospy.is_shutdown() and not current_state.connected):
        rate.sleep()

    aruco_type = "DICT_APRILTAG_36h11"

    arucoDict = cv2.aruco.Dictionary_get(ARUCO_DICT[aruco_type])

    arucoParams = cv2.aruco.DetectorParameters_create()


    intrinsic_camera = np.array(((933.15867, 0, 657.59),(0,933.1586, 400.36993),(0,0,1)))
    distortion = np.array((-0.43948,0.18514,0,0))

    cornerss = 0

    detect_status = 0

  # create a VideoCaptureThread instance and start it
    video_thread = VideoCaptureThread(0)
    video_thread.start()

    while not rospy.is_shutdown():
        ret, img = video_thread.get_current_frame()

        #Aruco marker detection
        if img is not None and detect_status == 0:
            output, number_ids = pose_estimation(img, ARUCO_DICT[aruco_type], intrinsic_camera, distortion)
            cv2.imshow('Video Capture', output)
        
            if times >= 10: 
                times = 0

                if number_ids == 289:
                    takeoff(pose,altitude=3)
                if number_ids == 291:
                    foward_x(pose,distance=6,altitude=3)
                if number_ids == 293:
                    backward_x(pose,distance=6,altitude=3)
                if number_ids == 295:
                    foward_y(pose,distance=6,altitude=3)
                if number_ids == 297:
                    backward_y(pose,distance=6,altitude=3)
                if number_ids == 299:
                    rospy.sleep(2)
                    if detect_status == 0:
                        detect_status = 1
                        print("1")
                if number_ids == 301:
                    rospy.sleep(2)
                    detect_status = 2
                    print("2")

        # Image colour detection for landing pad
        if img is not None and detect_status == 1:
            outputs, cornerss = colour_detect(img)
            cv2.imshow('Video Capture', outputs)

            if cornerss == 12 and times >=5:
                times = 0
                detect_status = 0
                landing(pose)
                print(detect_status)
                continue    
        
        # Hand gesture detection
        if img is not None and detect_status == 2:
            outputss, finger_count = hand_counter(img)
            cv2.imshow('Video Capture', outputss)

            if times >= 5:
                times = 0
                if finger_count == 1:
                    foward_z(pose,distance=4)
                if finger_count == 2:
                    backward_z(pose,distance=3)
                if finger_count == 3:
                    detect_status = 0
                    print(detect_status)

                    if detect_status != 0:
                        status_update()
                    continue

        if cv2.waitKey(1) == ord('q'):
            break
    video_thread.stop()
    cv2.destroyAllWindows()

    rospy.spin()