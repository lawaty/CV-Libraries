import cv2
import numpy as np
from line import Line
from abc import ABCMeta, abstractmethod

def getArea(line):
	return line.area

class ILineDetector(metaclass=ABCMeta):
	"""
		Class for line detection and filtering
	"""
	@abstractmethod
	def __init__(self, algorithm=None, filtering_criteria=None, quantity=None):
		"""
			Constructor identifies the detection specifications
			
			Parameters
			——————————
			algorithm ———> algorithm to find all lines in the canny frame (default=HOUGH_LINES)
			filtering_criteria ———> Array of filtering Constants
			quantity ———> filtering by area as an optional excess filtering step
		"""
		pass

	@abstractmethod
	def xExtremes(self, lines):
		"""
			Function returns the leftmost and rightmost vertical lines
			
			Parameters
			——————————
			lines ———> list of all found lines (list of line objects)
			
			@return : list of two line objects
		"""
		pass

	@abstractmethod
	def yExtremes(self, lines):
		"""
			Function returns the top and bottom horizontal lines
			
			Parameters
			——————————
			lines ———> list of all found lines (list of line objects)
			
			@return : list of two line objects
		"""
		pass

	@abstractmethod
	def run(self, frame):
		"""
			This function does the following:-
			1- Creates the canny version of the frame
			2- Extracts all lines according to the specified algorithm
			3- Applies the desired filtering criterion
			
			Parameters
			——————————
			frame ———> Workpiece frame
		"""
		pass

class LineDetector(ILineDetector):
	"""
		Class builder for extracting lines from a frame
		Dependencies
        ————————————
		- ImageManipulator

		All Dynamic Variables
		————————————————————
		self.__algorithm ———> Hough detection or contours
		self.__minLength ———> The minimum length of a line
		self.__quantity ———> The minimum length of a line
		self.__filtering ———> Filtering Criteria
		self._horizontals ———> Horizontal Lines after eliminating redundancies
		self._verticals ———> Vertical Lines after eliminating redundancies

		All Static Variables
		————————————————————
		—) For Algorithms
			1. CONTOURS
			2. HOUGH

		—) For Filtering
			1. XEXTREMES
			2. YEXTREMES
			3. ANGLE
			4. HORIZONTALS
			5. VERTICALS
	"""
	CONTOURS = 1
	HOUGH = 2
	
	XEXTREMES=1
	YEXTREMES=2
	ANGLE=3 #TODO
	HORIZONTALS=4
	VERTICALS=5


	def __init__(self, algorithm=None, filtering_criteria=None, quantity=None):
		"""
			Constructor identifies the detection specifications
			
			Parameters
			——————————
			algorithm ———> algorithm to find all lines in the canny frame (default=HOUGH_LINES)
			filtering_criteria ———> list of filtering sequences
			quantity ———> filtering by area as an optional excess filtering step
		"""
		self.__algorithm = algorithm
		self.minLength = 1
		self.minLineDistance = 20

		self.__quantity = quantity
		self.__filtering = filtering_criteria

	def _toCanny(frame):
		"""
			#TODO : use salama's class
			function constructs the canny version of a frame
			:param frame: workpiece frame 
			:return: canny version
		"""
		gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		erosion = cv2.erode(gray, (5, 5), iterations=1)
		canny = cv2.Canny(erosion, 120, 80)
		cv2.imshow('canny', canny)
		return canny		

	def _houghAlgorithm(self, canny):
		lines = cv2.HoughLinesP(canny, rho=1, theta=np.pi/180.0, threshold=5,minLineLength=self.minLength, maxLineGap=5)
		result = []
		try:
			for line in lines:
				result.append(Line(line))
		except:
			pass
		return result

	def _contoursAlgorithm(self, contours, frame):
		"""
			Method filters the found contours to return only those representing lines
		"""
		result = []
		for contour in contours:
			[vx,vy,x,y] = cv2.fitLine(contour, cv2.DIST_L2,0,0.01,0.01)
			this_line = Line([(int(x), int(y)), (int(vx*2), int(vy*2))], cv2.contourArea(contour)).draw(frame)
			result.append(this_line)
			# print(contour)
			# temp = contour.tolist()
			# list_version = []
			# for cnt in temp:
			# 	list_version.append(cnt[0])
			# pts = [(list_version[0][0], list_version[0][1]), (list_version[-1][0], list_version[-1][1])]
			# this_line = Line(pts, cv2.contourArea(contour))
			
			# if this_line.length() > self.minLength:
			# 	result.append(this_line)
		return result

	def _eliminateRedundancies(self, lines):
		"""
			Ayman Optimized gedan here
		"""
		originalTolerances = (Line.horizontalTolerance, Line.verticalTolerance)
		Line.horizontalTolerance = 1
		Line.verticalTolerance = 1

		self._verticals = LineDetector.__filterVerticals(lines)
		self._horizontals = LineDetector.__filterHorizontals(lines)
		
		length = len(self._verticals)
		i = 0
		while i < length:
			j = i+1
			while j < length:
				if abs(self._verticals[i].perpDistance(self._verticals[j])) < self.minLineDistance:
					self._verticals.remove(self._verticals[j])
					length -= 1	
				j += 1
			i += 1		

		length = len(self._horizontals)
		i = 0
		while i < length:
			j = i+1
			while j < length:
				if abs(self._horizontals[i].perpDistance(self._horizontals[j])) < self.minLineDistance:
					self._horizontals.remove(self._horizontals[j])
					length -= 1	
				j += 1
			i += 1

		Line.horizontalTolerance = originalTolerances[0]
		Line.verticalTolerance = originalTolerances[1]

	def xExtremes(self, lines):
		"""
			Function returns the leftmost and rightmost vertical lines

			Parameters
			——————————
			lines ———> list of all found lines (list of line objects)

			@return : list of two line objects
		"""
		leftmost = None
		rightmost = None
		for line in lines:
			if line.isVertical():
				if not leftmost or line.pts[0][0] < leftmost.pts[0][0] - 10:
					leftmost = line

				if not rightmost or line.pts[0][0] > rightmost.pts[0][0] + 10:
					rightmost = line

		return [leftmost, rightmost]	

	def yExtremes(self, lines):
		"""
			Function returns the top and bottom horizontal lines

			Parameters
			——————————
			lines ———> list of all found lines (list of line objects)

			@return : list of two line objects
		"""
		topmost = None
		bottommost = None
		for line in lines:
			if line.isHorizontal():
				if not topmost or line.pts[0][1] < topmost.pts[0][1] - 10:
					topmost = line

				if not bottommost or line.pts[0][0] > bottommost.pts[0][0] + 10:
					bottommost = line

		return [topmost, bottommost]			

	def run(self, frame):
		"""
			This function does the following:-
				1- Creates the canny version of the frame
				2- Extracts all lines according to the specified algorithm
				3- Applies the desired filtering criterion

			Parameters
			——————————
			frame ———> Workpiece frame
		"""
		canny = LineDetector.__toCanny(frame)
		# Detection
		if self.__algorithm == LineDetector.HOUGH:
			result = self.__houghAlgorithm(canny)
		elif self.__algorithm == LineDetector.CONTOURS:
			contours, hierarchy = cv2.findContours(canny, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
			result = self.__contoursAlgorithm(contours, frame)
		print(result)
		self.__eliminateRedundancies(result)
		print(result)
		# Now you have the lines stored in self._horizontals and self._verticals
		# Filtering
		
		if self.__filtering != None:
			result = []
			for sequence in self._filtering:
				sequence_result = None
				for criterion in sequence:
					if sequence_result is None:
						sequence_result = []
						sequence_result.extend(self.__horizontals)
						sequence_result.extend(self.__verticals)
				
					if criterion == LineDetector.XEXTREMES:
						sequence_result = self.xExtremes(sequence_result)
				
					elif criterion == LineDetector.YEXTREMES:
						sequence_result = self.yExtremes(sequence_result)

					elif criterion == LineDetector.VERTICALS:
						sequence_result = LineDetector.__filterVerticals(sequence_result)

					elif criterion == LineDetector.HORIZONTALS:
						sequence_result = LineDetector.__filterHorizontals(sequence_result)
				result.extend(sequence_result)
		
		if self.__quantity:
				result = self.__filterByArea(result)
		return result

	def __filterVerticals(lines):
		"""
			Filter vertical lines
		"""
		if not lines:
			return []

		result = []
		for line in lines:
			if line and line.isVertical():
				result.append(line)
		return result

	def __filterHorizontals(lines):
		"""
			Filter horizontal lines
		"""
		if not lines:
			return []

		result = []
		for line in lines:
			if line and line.isHorizontal():
				result.append(line)
		return result

	def __filterByArea(self, lines):
		"""
			Filter lines by area
		"""
		lines.sort(key=getArea, reverse=True)
		return lines[:self.__quantity]

if __name__ == "__main__":
	cap = cv2.VideoCapture("http://localhost:8070/stream?topic=/robotech/robotech/cameraright/camera_image")

	while cap.isOpened():
		_, img = cap.read()

		Detector = LineDetector(LineDetector.HOUGH, [[LineDetector.XEXTREMES], [LineDetector.YEXTREMES]])
		lines = Detector.run(img)
		for line in lines:
			if line:
				if line.isVertical():
					line.draw(img)
				else:
					line.draw(img)

		cv2.imshow('lol', img)	
		key = cv2.waitKey(20)
		if key == 27:
			break;