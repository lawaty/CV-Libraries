import time
import cv2
import numpy as np
import socket
from ros import RosConnection

class PID:
	SETUP = 1
	ADAPT = 2
	KP = 3
	KI = 4
	def __init__(self, tuning = (0.01, 0.01, 0), set_point = 0, output_limits=(-400, 400), adaptive=False, steps = (0.01, 0.01, 0), danger=100):
		"""
			function initializes the pid calculator translation
			:param tuning: tuple containing the pid constants
			:param set_point: desired error value
		"""
		# PID Parameters
		self.__kp, self.__ki, self.__kd = tuning
		self.__set_point = set_point

		# Calculations Necessary Variables
		self.__integ = 0
		self.__diff = 0
		self.__prev_err = 0
		self.__diff_prev_instance = 0
		self.__min, self.__max = output_limits
		self.__prev_output = 0

		# ---------------------------- Adaptive Tuning Belongings
		self.__phase = PID.SETUP
		# Setup Parameters
		self.__step = PID.KP

		# Adaptive Tuning Params
		self.__adaptive = adaptive
		self.__steps = steps
		self.__danger = danger

		#Fitness Evaluation Belognings
		self.__max_neg_reached = 0
		self.__max_pos_reached = 0
		self.__prev_wavelength = 0

		self.__prev_integ_at_setpoint = 0
		self.__prev_diff_at_setpoint = 0

		self.__healthy = False

	def __setup(self, err):
		"""
			Setup strategy
			Update Kp to Resist Overshooting
			1- Detect minimzation
				compare	the current aplitude to the previous

			2- Resist Overshooting
				Increase Kp till the current overshoot is larger than the previous (decrement it and set it to healthy)

			Update Ki
			1- Detect minimzation
				compare	the current aplitude to the previous

			2- Resist Overshooting
				Increase Ki till the current overshoot is larger than the previous

			@param err: current error value			
		"""

		if self.__max_pos_reached and self.__max_neg_reached: 
			if self.__max_pos_reached - self.__max_neg_reached > self.__prev_wavelength:
				# Resist overshooting by updating kp then ki
				if self.__step == PID.KP:
					self.__kp += self.__steps[0]
				else:
					self.__ki += self.__steps[1]

			# if overshooting is good in KP, go to the next step (Ki)
			elif self.__step == PID.KP:
				self.__step+=1

			else:
				self.__phase = PID.ADAPT

			self.__prev_wavelength = self.__max_pos_reached - self.__max_neg_reached

		# For adaption phase
		if not err:
			self.__prev_integ_at_setpoint = self.__integ
			self.__prev_diff_at_setpoint = self.__diff

	def __adapt(self, err):
		"""
			Adpting Strategy
			Detect Kp Error
				Decrease self.__Kp when: self.__integ at setpoint is low and self.__diff is large
				Increase self.__Kp when: current wavelength > previous

			Detect Ki Error
				Decrease self.__Ki when: self.__integ at setpoint is larger than previous
				Increase self.__Ki when: self.__integ at setpoint is smaller than previous
		"""
		if not err: # Setpoint
			# Kp decreases
			if self.__integ <= self.__prev_integ_at_setpoint and self.__diff > self.__prev_diff_at_setpoint: # Ki is healthy and overshooting exists
				self.__kp -= self.__steps[0]

			# Ki adaption
			if self.__integ <= self.__prev_integ_at_setpoint:
				self.__ki += self.__steps[1]
			else:
				self.__ki -= self.__steps[1]

			self.__prev_integ_at_setpoint = self.__integ
			self.__prev_diff_at_setpoint = self.__diff			

		elif self.__max_pos_reached - self.__max_neg_reached > self.__prev_wavelength:
			# Kp increases
			self.__kp += self.__steps[0]

	def __call__(self, err):
		"""
			function calculates the control value based on the current error
			:param err: current error
			:return: The control value
		 """

		c_time = time.time()
		if c_time - self.__diff_prev_instance == 0:
			return self.__prev_output

		self.__integ += err
		self.__diff = (err - self.__prev_err) / (c_time - self.__diff_prev_instance)
		output = err * self.__kp + self.__integ * self.__ki + self.__diff * self.__kd

		# Measure oscillation wavelength
		if self.__prev_err <= err < 0:
			self.__max_neg_reached = self.__prev_err
		elif 0 < err <= self.__prev_err:
			self.__max_pos_reached = self.__prev_err

		if self.__adaptive and self.__phase == PID.SETUP:
			self.__setup(self.__prev_err)
		elif self.__adaptive:
			self.__adapt(self.__prev_err)

		self.__prev_err = err
		self.__diff_prev_instance = c_time

		if output < self.__min or output > self.__max:
			self.__integ -= err
			output = self.__max if output > self.__max else self.__min

		self.__prev_output = output

		return output

	def display(self, frame):
		cv2.putText(frame, "INPUT: " + str(self.__prev_err), (20, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1, cv2.LINE_AA)
		cv2.putText(frame, "OUTPUT: " + str(self.__prev_output) + ", integ: ("+str(self.__integ)+")", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1, cv2.LINE_AA)
		cv2.putText(frame, "Tuning: ("+str(self.__kp)+" "+str(self.__ki)+" "+str(self.__kd)+")", (20, 60),  cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1, cv2.LINE_AA)	

def calculateErrors(circle, shape):
	w, h = shape[1], shape[0]
	cx, cy = int(shape[1] / 2), int(shape[0] / 2)
	for x, y, r in circle:
		return cx - x, cy - y

def evaluate(t_control):
	"""
		function evaluate the motor values from the calculated pid output
		param t_control: pid output for translation
		param e_control: pid output for elevation
		:return: list motor values
	"""

	motors = [1500, 1500, 1500, 1500, 1500, 1500]

	if t_control:
		# Translation
		motors[0] += t_control
		motors[1] += -t_control
		motors[2] += -t_control
		motors[3] += t_control

	# Elevation
	if e_control:
		motors[4] = motors[5] = 1500 + e_control

	return motors


if __name__ == "__main__":
	cap = cv2.VideoCapture("http://localhost:8070/stream?topic=/robotech/robotech/camerapilot/camera_image")
	t_pid = PID(adaptive=True)
	# e_pid = PID(adaptive=True)
	circle = None
	UDP_IP = "localhost"
	UDP_PORT = 2222
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	controller = RosConnection()
	running = False

	while cap.isOpened():
		motors = [1500, 1500, 1500, 1500, 1500, 1500, 0]
		_, img = cap.read()
		gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
		blurred = cv2.medianBlur(gray, 25)

		minDist = 30
		param1 = 30
		param2 = 20
		minRadius = 10
		maxRadius = 100

		new_circle = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, 1, minDist, param1=param1, param2=param2, minRadius=minRadius, maxRadius=maxRadius)
		circle = new_circle[0] if new_circle is not None else circle

		if circle is not None:
			circle = np.uint16(np.around(circle))
			for x, y, r in circle:
				cv2.circle(img, (x, y), r, (0, 255, 0), 2)

			if running:
				errorx, errory = calculateErrors(circle, img.shape)
				t_signal = t_pid(errorx) / 400
				# e_signal = e_pid(errory)
				motors = evaluate(t_signal)
				controller.send_data(motors)

				t_pid.display(img)

		cv2.imshow('lol', img)	
		key = cv2.waitKey(20)
		if key == 27:
			break;
		elif key == ord('s'):
			running = True
		elif key == ord('e'):
			running = False