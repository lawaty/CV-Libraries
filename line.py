import cv2
import numpy as np
import math
import warnings
from abc import ABCMeta, abstractmethod

class ILine(metaclass=ABCMeta):
	@abstractmethod
	def linePassingBy(pt, slope, h):
		"""
			Function constructs a line with a known slope and passes by a given point such that it touches the frame borders
			:param pt: point that the line must pass by
			:param slope: slope of the desired line
			:param h: frame height
			:return : line object
			:example : myLine = Line.linePassingBy(pt, slope, h)
		"""
		pass

	@abstractmethod
	def draw(self, frame, color=(255, 255, 255), dotted=False):
		"""
			Function draws the line on a given frame
			:param frame: frame
			:param color: bgr color
			:param dotted: boolean to draw dotted line instead of solid one
		"""
		pass

	@abstractmethod
	def intercept(self, x=None, y=None):
		"""
			Function returns the intercept with certain horizontal or vertical axis (x and y axes if val is not passed)
			:param x: constant x value for a vertical line
			:param y: constant y value for a horizontal line
			:return status: status True or False
			:return intercept: location of interception
			:warning: status might be False in case the two lines are parallel
		"""
		pass

	@abstractmethod
	def extend(self, horizontals=None, verticals=None):
		"""
			function extends the line to intercept any two horizontal or vertical axes
			:param horizontals: tuple of two horizontal axes.
			:param verticals: tuple of two vertical axes.
			:return : The extended version of line
			:example : "myLine.extend(verticals=(10,490))" extends the line till it intercepts the two vertical axes x=10 & x=490

			Observation
			-----------
			extend can be used also for clipping
		"""
		pass

	@abstractmethod
	def slope(self):
		"""
			Slope Calculation
			:return: slope
		"""
		pass

	@abstractmethod
	def angle(self, rad=False):
		"""
			function measures the angle of a line (measured ccw from the positive x)
			param rad: boolean indicates the angle format
			:return: angle ranging from 0 to 360
		"""
		pass

	@abstractmethod
	def mid(self):
		"""
			function returns the midpoint of the given line
			return: point as tuple
		"""
		pass

	@abstractmethod
	def length(self):
		"""
			function calcaulates the length of a line
			:return: length
		"""
		pass

	@abstractmethod
	def split(self, end, ratio):
		"""
			function splits a line into two by ratio
			param end: the end to start the first portion from (can be 0 or 1)
			param ratio: ratio of the first portion to the 2nd
			return: two splitted lines
		"""
		pass

	@abstractmethod
	def rotate(self, rot_center, deg):
		"""
			function rotates the line by certain angle around a given point
			param rot_center: point around which the line rotates
			param deg: angle in degree
			return: new rotated version of the line
		"""
		pass

	@abstractmethod
	def mirror(self, x=None, y=None):
		"""
			function mirrors the line about a certain axis (x=xi or y=yi) or a certain point (x=xi and y=yi)
			:param x: if you want to mirror the line around a vertical axis (x=xi)
			:param y: if you want to mirror the line around a horizontal axis (y=yi)
			:return: mirrored version of the line

			Observation
			-----------
			Mirroring the line around a point produces a line parallel to the original
		"""
		pass

	@abstractmethod
	def intersect(self, line):
		"""
			Function finds the point of intersection with another line
			:param line: Line object
			:return: point of intersection
		"""
		pass

	@abstractmethod
	def perpDistance(self, obj):
		"""
			Function measures the perpendicular distance between the current line and a pt or another line
			:param obj: pt or line object from which we will calculate the perpendicular distance
			:return: length of the line starting from pt and perpendicular on the current line
		"""
		pass


class Line(ILine, RuntimeError, RuntimeWarning):
	"""
		Class conecerned with line operations for easier manipulation
	"""

	verticalTolerance = 1
	horizontalTolerance = 1
	def __init__(self, pts, area=None):
		"""
			Function initializes our line's important belongings
			:param pts: list of two tuples representing each endpoint
		"""
		if type(pts) is np.ndarray:
			self.pts = [(int(pts[0][0]), int(pts[0][1])), (int(pts[0][2]), int(pts[0][3]))]
		else:
			self.pts = pts
		
		self.area = area

	@staticmethod
	def linePassingBy(pt, slope, h):
		"""
			Function constructs a line with a known slope and passes by a given point such that it touches the frame borders
			:param pt: point that the line must pass by
			:param slope: slope of the desired line
			:param h: frame height
			:return : line object
			:example : myLine = Line.linePassingBy(pt, slope, h)
		"""
		x, y = pt
		pt1 = (int(x - y / slope), 0)
		pt2 = (int(x - (y - h) / slope), h)
		return Line([pt1, pt2])
	
	def draw(self, frame, color=(255, 255, 255), dotted=False):
		"""
			Function draws the line on a given frame
			:param frame: frame
			:param color: bgr color
			:param dotted: boolean to draw dotted line instead of solid one
		"""
		if dotted:
			# TODO : Needs More Work with special cases
			dash_length = int(self.length()/40)
			dash_length = 5 if dash_length < 5 else dash_length

			theta = self.angle(True)
			x_displacement = int(dash_length * math.cos(theta))
			y_displacement = int(dash_length * math.sin(theta))

			x1, y1 = self.pts[0]
			x2, y2 = (x1 + x_displacement, y1 + y_displacement)
			while x2 < self.pts[1][0] or y2 < self.pts[1][1]:
				cv2.line(frame, (x1, y1), (x2, y2), color, 1)

				x1 += int(2 * x_displacement)
				y1 += int(2 * y_displacement)
				x2, y2 = (x1 + x_displacement, y1 + y_displacement)
				
		else:
			cv2.line(frame, self.pts[0], self.pts[1], color, 9)

	def intercept(self, x=None, y=None):
		"""
			Function returns the intercept with certain horizontal or vertical axis (x and y axes if val is not passed)
			:param x: constant x value for a vertical line
			:param y: constant y value for a horizontal line
			:return status: status True or False
			:return intercept: location of interception
			:warning: status might be False in case the two lines are parallel
		"""
		if x != None and y != None:
			raise Exception('Intercept Error: One axis should be given at a time', Line)

		x1, y1 = self.pts[0]
		x2, y2 = self.pts[1]
		ret = True

		if y != None:
			if y2 - y1 == 0:
				ret = False; # Horizontal
				x = 0
			else:
				x = (x2 - x1) * (y - y2) / (y2 - y1) + x2
			return ret, int(x)

		elif x != None:
			if x2 - x1 == 0:
				ret = False # Vertical
				y = 0
			else:
				y = (y2 - y1) * (x - x2) / (x2 - x1) + y2
			return ret, int(y)

	def extend(self, horizontals=None, verticals=None):
		"""
			# TODO: Extend till any two intercepts (x1=None, y1=None, x2=None, y2=None)
			function extends the line to intercept any two horizontal or vertical axes
			:param horizontals: tuple of two horizontal axes.
			:param verticals: tuple of two vertical axes.
			:return : The extended version of line
			:example : "myLine.extend(verticals=(10,490))" extends the line till it intercepts the two vertical axes x=10 & x=490

			Observation
			-----------
			extend can be used also for clipping
		"""
		x1, y1 = self.pts[0]
		x2, y2 = self.pts[1]

		if horizontals and verticals:
			raise Exception('Extend Error: Extending needs either horizontals or verticals not both', Line)

		# Extend using horizontal axes
		elif horizontals != None:
			axis1, axis2 = horizontals
			if axis1 > axis2:
				axis1, axis2 = axis2, axis1

			if y1 == y2:
				raise Exception('Extend Error: Line is parallel to the axes', Line)

			if y1 == axis1 and y2 == axis2 or y1 == axis2 and y2 == axis1:
				warnings.warn("Line is Already Extended", Line)
				return self

			x1, y1 = self.intercept(y=axis1)[1], axis1
			x2, y2 = self.intercept(y=axis2)[1], axis2

		# Extend using horizontal axes			
		elif verticals != None:
			axis1, axis2 = verticals
			if axis1 > axis2:
				axis1, axis2 = axis2, axis1

			if x1 == x2:
				raise Exception('Extend Error: Line is parallel to the axes', Line)

			if x1 == axis1 and x2 == axis2 or x1 == axis2 and x2 == axis1:
				warnings.warn("Line is Already Extended", Line)
				return self

			x1, y1 = axis1, self.intercept(x=axis1)[1]
			x2, y2 = axis2, self.intercept(x=axis2)[1]

		else:
			if self.isHorizontal():
				return self.extend(verticals=(0, 500))
			else:
				return self.extend(horizontals=(0, 500))

		pts = [(x2, y2), (x1, y1)]
		return Line(pts)

	def slope(self):
		"""
			Slope Calculation
			:return: slope
		"""
		x1, y1 = self.pts[0]
		x2, y2 = self.pts[1]
		if x2 - x1 == 0:
			return 100000 # Vertical Line
		return (y2 - y1) / (x2 - x1)

	def angle(self, rad=False):
		"""
			function measures the angle of a line (measured ccw from the positive x)
			param rad: boolean indicates the angle format
			:return: angle ranging from 0 to 360
		"""
		x1, y1 = self.pts[0]
		x2, y2 = self.pts[1]

		absolute_angle = abs(math.atan(self.slope()))

		if x2 - x1 >= 0:
			if y2 - y1 >= 0:
				result = absolute_angle
			else: result =  2 * math.pi - absolute_angle;
		else:
			if y2 - y1 >= 0:
				result = math.pi - absolute_angle
			else: result = math.pi + absolute_angle

		return result if rad else math.degrees(result)

	def mid(self):
		"""
			function returns the midpoint of the given line
			return: point as tuple
		"""
		return (self.pts[1][0] + self.pts[0][0]) // 2, (self.pts[1][1] + self.pts[0][1]) // 2

	def length(self):
		"""
			function calcaulates the length of a line
			:return: length
		"""
		x1, y1 = self.pts[0]
		x2, y2 = self.pts[1]
		return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

	def split(self, end, ratio):
		"""
			function splits a line into two by ratio
			param end: the end to start the first portion from (can be 0 or 1)
			param ratio: ratio of the first portion to the 2nd
			return: two splitted lines
		"""
		if not 0 < ratio < 1:
			raise Exception("Split Error: Ratio must be BETWEEN 0 and 1", Line)

		if end == 0:
			x1, y1 = self.pts[0]
			x2, y2 = self.pts[1]
		else:
			x1, y1 = self.pts[1]
			x2, y2 = self.pts[0]			

		split_pt = (int(x1 + (x2 - x1) * ratio), int(y1 + (y2 - y1) * ratio))
		return Line([self.pts[0], split_pt]), Line([split_pt, self.pts[1]])

	def rotate(self, rot_center, deg):
		"""
			function rotates the line by certain angle around a given point
			param rot_center: point around which the line rotates
			param deg: angle in degree
			return: new rotated version of the line
		"""
		def rotatePoint(pt, invert=0):
			"""
				inner function rotates point by degree
				param deg: angle in degree
				param invert: flag to invert the angle for the second portion of the line (one half of the line would have the angle theta and the other would be (theta + 180) % 360)
				return: new rotated version of the line
			"""
			length = self.length() / 2
			alpha = math.radians((self.angle() + invert + deg) % 360)
			o1, o2 = rot_center

			return ( int(o1 + length * math.cos(alpha)), int(o2 + length * math.sin(alpha)) )		
			
		new_pts = [rotatePoint(self.pts[0], 180), rotatePoint(self.pts[1])]
		return Line(new_pts)	

	def mirror(self, x=None, y=None):
		"""
			function mirrors the line about a certain axis (x=xi or y=yi) or a certain point (x=xi and y=yi)
			:param x: if you want to mirror the line around a vertical axis (x=xi)
			:param y: if you want to mirror the line around a horizontal axis (y=yi)
			:return: mirrored version of the line

			Observation
			-----------
			Mirroring the line around a point produces a line parallel to the original
		"""
		x1, y1 = self.pts[0]
		x2, y2 = self.pts[1]
		if x:
			x1 += 2 * (x - x1)
			x2 += 2 * (x - x2)
		if y:
			y1 += 2 * (y - y1)
			y2 += 2 * (y - y2)

		return Line([(x1, y1), (x2, y2)])

	def intersect(self, line):
		"""
			Function finds the point of intersection with another line
			:param line: Line object
			:return: point of intersection
		"""
		m1 = self.slope()
		b1 = self.intercept(x=0)[1]
		m2 = line.slope()
		b2 = line.intercept(x=0)[1]
		if m1 - m2:
			x = (b2 - b1) / (m1 - m2)
		else:
			print("Intersection Error: Parallel Lines")
			return False, (None, None)
		y = m1 * x + b1

		return True, (int(x), int(y))

	def perpDistance(self, obj):
		"""
			Function measures the perpendicular distance between the current line and a pt or another line
			:param obj: pt or line object from which we will calculate the perpendicular distance
			:return: length of the line starting from pt and perpendicular on the current line
		"""
		def perpDistPoint(pt):
			x, y = pt
			x1, y1 = self.pts[0]
			x2, y2 = self.pts[1]
			l1 = Line([(x, y), (x1, y1)]).length()
			l2 = Line([(x, y), (x2, y2)]).length()
			l3 = self.length()
			if not (l1 and l3): 
				theta = math.acos((l1**2 + l3**2 - l2**2) / (2*l1*l3))
			else: return 0
			return l1 * math.sin(theta)

		if type(obj) is tuple:
			return perpDistPoint(obj)

		elif type(obj) is Line:
			return perpDistPoint(obj.mid())

		else :
			raise Exception("perpDistance Error: Invalid Parameter", Line)

	def isVertical(self):
		"""
			Uses the static variableTolerance to return a boolean
		"""
		return self.slope() >= Line.verticalTolerance

	def isHorizontal(self):
		"""
			Uses the static horizontalTolerance to return a boolean
		"""
		return self.slope() <= Line.horizontalTolerance

class DemoLine:
	"""
		Class for looking over the line different features
	"""
	def __init__(self, pts=[(400, 100), (100, 400)]):
		self.__w, self.__h = 500, 500
		self.__frame = np.zeros((self.__w, self.__h, 3), np.uint8)
		self.__line = Line(pts)

	def __wait(self):
		cv2.imshow("Demo", self.__frame)
		cv2.waitKey(0)

	def intercept(self):
		#TODO : labelPosition is a bit dumb
		def singleIntercept(x=None, y=None):
			if x != None: # only x is passed
				cv2.line(self.__frame, (x, 0), (x, self.__w), (255, 0, 0), 9)
				intercept1 = self.__line.intercept(x=x)[1]
				labelPosition = self.__h - 20 if intercept1 > self.__h - 20 else intercept1
				cv2.putText(self.__frame, "("+str(x)+", "+str(intercept1)+")", (x, labelPosition), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1,cv2.LINE_AA)

			else: # only y is passed
				cv2.line(self.__frame, (0, y), (self.__h, y), (255, 0, 0), 9)
				intercept2 = self.__line.intercept(y=y)[1]
				labelPosition = self.__w - 20 if intercept2 > self.__w - 20 else intercept2
				cv2.putText(self.__frame, "("+str(intercept2)+", "+str(y)+")", (labelPosition, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1,cv2.LINE_AA)

		singleIntercept(x=0)
		singleIntercept(y=0)
		singleIntercept(x=300)
		singleIntercept(x=300)
		self.__wait()

	def extend(self):
		def singleExtend(horizontals=None, verticals=None):
			if horizontals != None: # only horizontals is passed
				cv2.line(self.__frame, (0, horizontals[0]), (self.__w, horizontals[0]), (255, 0, 0), 3)
				cv2.line(self.__frame, (0, horizontals[1]), (self.__w, horizontals[1]), (255, 0, 0), 3)
				self.__line.extend(horizontals=horizontals).draw(self.__frame)

			else: # only verticals is passed
				cv2.line(self.__frame, (verticals[0], 0), (verticals[0], self.__h), (255, 0, 0), 3)
				cv2.line(self.__frame, (verticals[1], 0), (verticals[1], self.__h), (255, 0, 0), 3)
				line2 = self.__line.extend(verticals=verticals).draw(self.__frame)

		singleExtend(horizontals=(10, 490))
		singleExtend(verticals=(110, 390))
		self.__wait()

	def basic(self):
		slope = self.__line.slope()
		angle_in_degs = self.__line.angle()
		angle_in_rads = self.__line.angle(True)
		midpoint = self.__line.mid()
		length = self.__line.length()
		print(f"Line Characteristics:-\nLength: {length}\nSlope: {slope}\nAngle: {angle_in_degs}deg or {angle_in_rads}rad\nMidpoint: {midpoint}")

	def split(self):
		line1, line2 = self.__line.split(0, 0.3)
		line1.draw(self.__frame)
		line2.draw(self.__frame, (0, 255, 0))
		self.__wait()

	def rotate(self):
		self.__line.draw(self.__frame, (0, 0, 255))
		self.__line.rotate(self.__line.mid(), 90).draw(self.__frame)
		self.__wait()

	def mirror(self):
		def singleMirror(x=None, y=None):
			if x and y:
				cv2.circle(self.__frame, (x, y), (3), (255, 255, 255), -1)
				self.__line.mirror(x=x, y=y).draw(self.__frame, (0, 0, 255))

			elif y:
				Line([(0, y), (self.__w, y)]).draw(self.__frame, dotted=True)
				self.__line.mirror(y=y).draw(self.__frame, (0, 0, 255))
			else :
				Line([(x, 0), (x, self.__h)]).draw(self.__frame, dotted=True)
				self.__line.mirror(x=x).draw(self.__frame, (0, 0, 255))		


		self.__line.draw(self.__frame)
		singleMirror(x=200)
		singleMirror(y=250)
		singleMirror(x=200, y=200)
		self.__wait()

	def intersect(self):
		self.__line.draw(self.__frame)
		second_line = Line([(200, 200), (300, 500)])
		second_line.draw(self.__frame)
		success, intersection = self.__line.intersect(second_line)
		if success:
			cv2.circle(self.__frame, intersection, 10, (0, 0, 255), 2)
			self.__wait()
		else:
			print("Intersection Error: Parallel Lines")

	def perpDistance(self):
		def singlePerpDistance(obj):
			# Contains another way to calculate the perpDistance from a point but it is verbose and heavily depends on other methods (used here just to draw the line representing the perpendicular distance)
			calculated_length = self.__line.perpDistance(obj)

			if type(obj) == Line:
				obj.draw(self.__frame, (255, 0, 0))
				obj = obj.mid()

			cv2.circle(self.__frame, obj, 5, (0, 255, 255), -1)
			success, pt2 = Line.linePassingBy(obj, -1/self.__line.slope(), self.__h).intersect(self.__line)
			if success:	
				perp = Line([obj, pt2])
				perp.draw(self.__frame, dotted=True)
				print(perp.length(), " VS ", calculated_length)

		#-------------------------------------------------
		self.__line.draw(self.__frame)
		singlePerpDistance(Line([(400, 100), (100, 200)]))
		singlePerpDistance((200, 200))
		self.__wait()

if __name__ == "__main__":
	DemoLine().extend()