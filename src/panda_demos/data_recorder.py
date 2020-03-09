import pyqtgraph as pg
from PyQt5.QtCore import Qt, QObject, QRunnable, pyqtSignal, pyqtSlot, QSize, QThreadPool
import random
from time import sleep
from panda_pbd.srv import EnableTeaching, EnableTeachingRequest
import rospy
import tf
import numpy as np
import pickle
import os


class Datarecorder():

    def __init__(self, interface):
        self.ee_velocities = []
        self.gripper_velocities = []
        self.gripper_states = []
        self.trajectory_points = []
        self.time_axis_ee = []
        self.time_axis_gripper = []
        self.recording = False
        self.recordingThreadpool = QThreadPool()
        self.interface = interface
<<<<<<< HEAD
        self.rate = 50
        self.timeStep = rospy.Rate(self.rate)
=======
        self.timeStep = 0.005
>>>>>>> c1eda9f909969ba8f8d463803d46c3f72092f2a6
        self.pose = None
        self.gripperstate = None
        self.data = {}
        self.listener = tf.TransformListener()

    def startRecording(self, dataLine_v, dataLine_g):
        self.worker = RecordingWorker(self.recordData, dataLine_v, dataLine_g)
        self.recordingThreadpool.start(self.worker)

    def stopRecording(self):
        self.recording = False 

    def saveData(self, path, filename):
        self.data["ee_velocities"] = self.ee_velocities
        self.data["gripper_velocities"] = self.gripper_velocities
        self.data["trajectory_points"] = self.trajectory_points
        self.data["gripper_states"] = self.gripper_states
        self.data["time_axis_ee"] = self.time_axis_ee
        self.data["time_axis_gripper"] = self.time_axis_gripper
        with open(os.path.join(os.path.expanduser(path), filename), 'wb') as f:
            pickle.dump(self.data, f)

    def loadData(self, path, filename):
        with open(os.path.join(os.path.expanduser(path), filename), 'rb') as f:
            loaded_program = pickle.load(f)
            return loaded_program        

    def getListenerValues(self):
        try:
            trans, rot = self.listener.lookUpTransform("panda_link0", "panda_K", rospy.Time(0)) #Use panda_K or panda_EE for the target frame
            traj_time = rospy.Time.now()
            linear, angular = self.listener.lookUpTwist("panda_link0", "panda_K", rospy.Time(0))
            vel_time = rospy.Time.now()
        except (tf.LookupException, tf.ConnectivityException, tf.ExtrapolationException):
            print("Could not get tf listener values")    

        self.trajectory_points.append((trans, rot))
        self.pose = trans
        self.ee_velocities.append(linear)
        self.time_axis_ee.append(vel_time)    

    '''
    def poseRequest(self):
        req = EnableTeachingRequest()
        req.ft_threshold_multiplier = self.interface.default_parameters['kinesthestic_ft_threshold']
        req.teaching = 1

        try:
            res = self.interface.kinesthetic_client(req)
        except rospy.ServiceException:
            rospy.logerr('Cannot contact Kinesthetic Teaching client!')
            self.pose = None

        if res.success:
            self.pose = res.ee_pose       
    '''
        

    def clearPlot(self, graphs):
        for graph in graphs:
            graph.clear()
        self.ee_velocities = []
        self.gripper_velocities = []
        self.time_axis_ee = []
        self.time_axis_gripper = []
        self.trajectory_points = []
        self.gripper_states = [] 
        self.previous_gripper_state = None
        self.previous_pose = None              

    '''
    def calculateDistance(self):
        a = np.array([self.pose.pose.position.x, self.pose.pose.position.y, self.pose.pose.position.z])
        b = np.array([self.previous_pose.pose.position.x, self.previous_pose.pose.position.y, self.previous_pose.pose.position.z])
        dist = np.linalg.norm(a - b)
        return dist
    '''

    def getGripperValues(self):
        self.previous_gripper_state = self.gripperstate
        self.gripperstate = self.interface.last_gripper_width
        if len(self.time_axis_gripper) > 1:
            v = abs(self.gripperstate - self.previous_gripper_state)/abs(self.time_axis_gripper[-1] - self.time_axis_gripper[-2])
        else:
            v = 0
        self.gripper_velocities.append(v)        
        gripper_time = rospy.Time.now()
        self.time_axis_gripper.append(gripper_time)

    def recordData(self, dataLine_v, dataLine_g):
        self.interface.relax()
        self.recording = True
        if len(self.time_axis_ee) == 0:
            currTime = 0.0
        else:
            currTime = self.time_axis_ee[-1]    
        while self.recording:
            #print(self.interface.robotless_debug)
            if not self.interface.robotless_debug:
                self.gripper_states.append(self.gripperstate)
                self.getListenerValues()
                self.getGripperValues()                   
            else:    
                newVelocity = random.uniform(0, 0.25)
                gripperVelocity = random.uniform(0, 0.05)
                self.ee_velocities.append(newVelocity)
                self.gripper_velocities.append(gripperVelocity)
                self.time_axis_ee.append(currTime)
                self.time_axis_gripper.append(currTime)
                currTime += float(1.0/self.rate)
            dataLine_v.setData(self.time_axis_ee, self.ee_velocities)
            dataLine_g.setData(self.time_axis_gripper, self.gripper_velocities)
            self.timeStep.sleep()

class RecordingWorker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super(RecordingWorker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs 

    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''

        # Retrieve args/kwargs here; and fire processing using them
        #result = self.fn(*self.args, **self.kwargs)
        try:
            result = self.fn(*self.args, **self.kwargs)
        except Exception as e:
            print(e)              
            
            