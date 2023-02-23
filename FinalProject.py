#! /usr/bin/env python

# Johannes Daniswara Pratama
# 5025221276
# Teknik Informatika

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

class VideoCaptureThread:
    # Define a video capture thread
    def __init__(self, video_source):
        self.video_capture = cv2.VideoCapture(video_source) # initialize video capture object
        self.current_frame = None
        self.ret = None
        self.is_running = False

    # For check if its running or not. And add thread for update
    def start(self):
        if self.is_running:
            print("Video capture is already running")
            return None
        self.is_running = True
        thread = threading.Thread(target=self._update, args=()) # create new thread to run update
        thread.start()
        return self

    # Jika ada error, dia akan menghentikan thread dan meng-release video capture
    def stop(self):
        self.is_running = False
        self.video_capture.release() # release video capture

    # the thread continuously updates the current frame (frame video nya di update)
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
    
    # Return ret dan frame
    def get_current_frame(self):
        return self.ret, self.current_frame

# List of possible supported DICT BY ARUCO LIBRARY
# List kombinasi dict yg di support
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

# variable global untuk mengecek berapa kali objeck di deteksi
global times
times = 0

# variable global untuk id dari april tag
global number_ids
number_ids=-1

# Global variable untuk mengecek status deteksi
# 0 = aruco tag (april tag)
# 1 = colour detection
# 3 = jumlah jari detection
global detect_status 
detect_status = 0

def state_cb(msg):
    global current_state
    current_state = msg

# Untuk mengecek local position
def local_position_cb(msg):
    global Position
    Position = msg


def pose_estimation(frame, aruco_dict_type, matrix_coefficients, distortion_coefficients):
    global times
    
    # Get ArUco dictionary
    aruco_dict = cv2.aruco.Dictionary_get(aruco_dict_type)
    
    # Set parameters for marker detection
    parameters = cv2.aruco.DetectorParameters_create()

    # Convert the input frame to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect markers in the input frame
    corners, ids, rejected_img_points = cv2.aruco.detectMarkers(
        gray, aruco_dict, parameters=parameters,
        cameraMatrix=matrix_coefficients, distCoeff=distortion_coefficients)

    # Initialize the marker ID to -1
    number_id = -1
    
    # If one marker is detected in the input frame
    if len(corners) > 0:
        for i in range(len(ids)):
            # Estimate the pose of the marker in the input frame
            rvec, tvec, markerPoints = cv2.aruco.estimatePoseSingleMarkers(
                corners[i], 0.02, matrix_coefficients, distortion_coefficients)
        
        # Draw detected markers and axes on the input frame
        cv2.aruco.drawDetectedMarkers(frame, corners)
        cv2.aruco.drawAxis(frame, matrix_coefficients, distortion_coefficients, rvec, tvec, 0.01)
        
        # Flatten the IDs list
        ids = ids.flatten()
        
        # Loop over all detected markers and draw a bounding box around each one
        for (markerCorner, markerID) in zip(corners, ids):
            corners = markerCorner.reshape((4, 2))
            topLeft, topRight, bottomRight, bottomLeft = corners

            # Compute the center coordinates of the marker
            cX, cY = np.average([topLeft, bottomRight], axis=0).astype(int)
            cv2.circle(frame, (cX, cY), 4, (0, 0, 0xFF), -1)

            # Draw the ID of the marker near its top-left corner
            cv2.putText(frame, str(int(markerID)), (topLeft.astype(int)[0], topLeft.astype(int)[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0xFF, 0), 2)
            
            # Print the ID of the marker to the console
            print("[Inference] ArUco marker ID: {}".format(markerID))
            
            # Update the marker ID
            number_id = markerID
        
        # Define the set of marker IDs that are used to trigger the event
        marker_ids = {289, 291, 293, 295, 297, 299, 301}
        
        # If the current marker ID is in the set of trigger marker IDs, update the event counter
        if number_id in marker_ids:
            times += 1

    # Return the input frame and the marker ID
    return frame, number_id

def takeoff(pose, altitude):

    # Wait for Flight Controller connection

    # Set initial position
    pose.pose.position.x = 0
    pose.pose.position.y = 0
    pose.pose.position.z = altitude

    # Send a few setpoints before starting

    local_pos_pub.publish(pose)

    # Set OFFBOARD mode
    offb_set_mode = SetModeRequest()
    offb_set_mode.custom_mode = 'OFFBOARD'

    while(not rospy.is_shutdown()):

        if current_state.mode != "OFFBOARD":
            if(set_mode_client.call(offb_set_mode).mode_sent == True):
                rospy.loginfo("OFFBOARD enabled")
        else:
            # Arm the vehicle
            if not current_state.armed :
                arm_cmd = CommandBoolRequest()
                arm_cmd.value = True

                if(arming_client.call(arm_cmd).success == True):
                    rospy.loginfo("Vehicle armed")

        # Publish setpoint
        local_pos_pub.publish(pose)

        # Jika sudah mencapai ketinggian, maka akan keluar loop
        if Position.pose.position.z >= 2.99 and Position.pose.position.z <= 3.3:
            rospy.loginfo("Altitude reached: %.2f m", Position.pose.position.z)
            break

def landing (pose,rate):
    global detect_status 
    detect_status = 0

    # LANDING DI CURRENT POSITION , JADI tidak berubah koordinat x dan y
    pose.pose.position.x = Position.pose.position.x
    pose.pose.position.y = Position.pose.position.y
    pose.pose.position.z = 0

    for i in range(100):   

        local_pos_pub.publish(pose)
        rate.sleep()

    rospy.loginfo("Landing success. Altitute reached: %.2f m", Position.pose.position.z)

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
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7) as hands:

        # Convert the image from BGR to RGB for processing with MediaPipe
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # To improve performance, optionally mark the image as not writeable to
        # pass by reference.
        image.flags.writeable = False

        results = hands.process(image)

        # Draw the hand annotations on the image.
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        # Initially set finger count to 0 for each cap
        fingerCount = 0
        global times

        if results.multi_hand_landmarks:
            for hand_landmarks, hand_label in zip(results.multi_hand_landmarks, results.multi_handedness):
                # Get hand label (left or right)
                hand_label = hand_label.classification[0].label

                # Test conditions for each finger: Count is increased if finger is 
                # considered raised.
                # Thumb: TIP x position must be greater or lower than IP x position, 
                # depending on hand label.
                if (hand_label == "Left") == (hand_landmarks.landmark[4].x > hand_landmarks.landmark[3].x):
                    fingerCount += 1

                # Other fingers: TIP y position must be lower than PIP y position, 
                # as image origin is in the upper left corner.
                if hand_landmarks.landmark[8].y < hand_landmarks.landmark[6].y:  #Index finger
                    fingerCount += 1
                if hand_landmarks.landmark[12].y < hand_landmarks.landmark[10].y:  #Middle finger
                    fingerCount += 1
                if hand_landmarks.landmark[16].y < hand_landmarks.landmark[14].y:  #Ring finger
                    fingerCount += 1
                if hand_landmarks.landmark[20].y < hand_landmarks.landmark[18].y:  #Pinky
                    fingerCount += 1

                # Draw hand landmarks 
                mp_drawing.draw_landmarks(
                    image,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    mp_drawing_styles.get_default_hand_landmarks_style(),
                    mp_drawing_styles.get_default_hand_connections_style())

        # Display finger count
        cv2.putText(image, str(fingerCount), (50, 450), cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 0, 0), 10)
        if fingerCount >= 1 and fingerCount <=5:
            times = times + 1

        return image, fingerCount

# menggerakan drone ke sumbu x
def move_x (pub, vel,rate, speed):
    vel.linear.x = speed
    vel.linear.y = 0
    vel.linear.z = 0
    pub.publish(vel)

# menggerakan drone ke sumbu y
def move_y (pub, vel, rate,speed):
    vel.linear.x = 0
    vel.linear.y= speed
    vel.linear.z = 0
    pub.publish(vel)

# menggerakan drone ke sumbu z
def move_z (pub, vel, rate, speed):
    vel.linear.x = 0
    vel.linear.y = 0
    vel.linear.z= speed
    pub.publish(vel)


    
if __name__ == "__main__":
    # inisialisasi ros node
    rospy.init_node("offb_node_py")

    # buat state subscriber untuk mavros state topic
    state_sub = rospy.Subscriber("mavros/state", State, callback = state_cb)

    # buat variable local_pos_pub untuk ngepublish local position setpoint
    local_pos_pub = rospy.Publisher("mavros/setpoint_position/local", PoseStamped, queue_size=10)
    
    # tunggu service dari mavros/cmd/arming 
    rospy.wait_for_service("/mavros/cmd/arming")
    rospy.loginfo("arm client enabled")
    arming_client = rospy.ServiceProxy("mavros/cmd/arming", CommandBool)    

    # tunggu service dari mavros/setmode
    rospy.wait_for_service("/mavros/set_mode")
    set_mode_client = rospy.ServiceProxy("mavros/set_mode", SetMode)

    # buat subscriber untuk mavros/localposition/pose
    PositionP = rospy.Subscriber("mavros/local_position/pose", PoseStamped, local_position_cb)


# Create publisher for velocity setpoint
    pub_vel = rospy.Publisher('mavros/setpoint_velocity/cmd_vel_unstamped', Twist, queue_size=10)    
    vel = Twist()

    # Setpoint publishing MUST be faster than 2Hz
    rate = rospy.Rate(20)

    # Initialize PoseStamped object
    pose = PoseStamped()

    # Wait for Flight Controller connection
    while(not rospy.is_shutdown() and not current_state.connected):
        rate.sleep()

    # define the type of aruco that we will used
    # i use apriltag 36h11
    aruco_type = "DICT_APRILTAG_36h11"
    arucoDict = cv2.aruco.Dictionary_get(ARUCO_DICT[aruco_type])

    # Initialize ArUco dictionary and parameters
    arucoParams = cv2.aruco.DetectorParameters_create()

    # Set camera intrinsic parameters and distortion coefficients
    intrinsic_camera = np.array(((933.15867, 0, 657.59),(0,933.1586, 400.36993),(0,0,1)))
    distortion = np.array((-0.43948,0.18514,0,0))

    # Initialize variables for marker detection status
    cornerss = 0
    detect_status = 0

  # create a VideoCaptureThread instance and start 
    video_thread = VideoCaptureThread(0)
    video_thread.start()

    while not rospy.is_shutdown():
        ret, img = video_thread.get_current_frame()

        #Aruco marker detection
        if img is not None and detect_status == 0:
            output, number_ids = pose_estimation(img, ARUCO_DICT[aruco_type], intrinsic_camera, distortion)
            cv2.imshow('Video Capture', output)

            if times >= 4:
                times = 0

                if number_ids == 289:
                    rospy.loginfo("[ID 289] DRONE TAKEOFF")
                    alt = 3
                    thread_takeoff = threading.Thread(target=takeoff,args=(pose,alt))
                    thread_takeoff.start()  

                elif number_ids == 291:
                    rospy.loginfo("[ID 291] DRONE MOVE FOWARD - X DIRECTION")
                    move_x(pub_vel, vel,rate, speed=2)

                elif number_ids == 293:
                    rospy.loginfo("[ID 293] DRONE MOVE BACKWARD - X DIRECTION")
                    move_x(pub_vel, vel,rate, speed=-2)

                elif number_ids == 295:
                    rospy.loginfo("[ID 295] DRONE MOVE FOWARD - Y DIRECTION")
                    move_y(pub_vel, vel, rate,speed=2)

                elif number_ids == 297:
                    rospy.loginfo("[ID 295] DRONE MOVE BACKWARD - Y DIRECTION")
                    move_y(pub_vel, vel,rate, speed=-2)

                elif number_ids == 299:
                    if detect_status == 0:
                        detect_status = 1
                        rospy.loginfo("[ID 299] SWITCHED TO COLOUR DETECTION MODE")

                elif number_ids == 301:
                    detect_status = 2
                    rospy.loginfo("[ID 301] SWITCHED TO HAND TRACKING DETECTION MODE")

    # Image colour detection for landing pad
        elif detect_status == 1:
            outputs, cornerss = colour_detect(img)
            cv2.imshow('Video Capture', outputs)

            if cornerss == 12 and times >=5:
                times = 0
                detect_status = 0
                thread_landing = threading.Thread(target=landing, args=(pose,rate))
                thread_landing.start()  
                rospy.loginfo("[SYSTEM] SWITCHED TO AR-TAG (APRIL TAG) DETECTION MODE")
                continue    

    # Hand gesture detection
        elif detect_status == 2:
            outputss, finger_count = hand_counter(img)
            cv2.imshow('Video Capture', outputss)

            if times >= 4:
                times = 0

                if finger_count == 1:
                    rospy.loginfo("[FINGER COUNT 1] DRONE MOVING FOWARD - Z DIRECTION")
                    move_z(pub_vel, vel,rate, speed=2)

                elif finger_count == 2:
                    rospy.loginfo("[FINGER COUNT 2] DRONE MOVE BACKWARD - Z DIRECTION")
                    move_z(pub_vel, vel,rate, speed=-2)

                elif finger_count == 3:
                    detect_status = 0
                    rospy.loginfo("[FINGER COUNT 3] SWITCHED TO AR-TAG (APRIL TAG) DETECTION MODE")

                    if detect_status != 0:
                        status_update()
                        continue
                    
                elif finger_count == 4:
                    rospy.loginfo("[FINGER COUNT 4] DRONE MOVE FOWARD - X DIRECTION")
                    move_x(pub_vel,vel,rate,speed=2)
                    
                elif finger_count == 5:
                    rospy.loginfo("[FINGER COUNT 5] DRONE MOVE BACKWORD - X DIRECTION")
                    move_x(pub_vel,vel,rate,speed=-2)

        if cv2.waitKey(1) == ord('q'):
            break
    video_thread.stop()
    cv2.destroyAllWindows()

    rospy.spin()
