import cv2
from line import Line
from line_detection import LineDetector

class SquareDetector(LineDetector):
    CONTOURS = 1
    HOUGH = 2
    def __init__(self, algorithm):
        self.__algorithm = algorithm
        self.minLength = 50
        self.minLineDistance = 20
        self.squareCorners = []

    def __Found(self, verticals, horizontals):
        return verticals[0] and verticals[1] and horizontals[0] and horizontals[1]

    def __draw(self, frame):
        if len(self.squareCorners) == 4:
            for i in range(3):
                Line([self.squareCorners[i], self.squareCorners[i+1]]).draw(frame)

    def run(self, frame):
        """
            @param frame: workpiece
            @return healthy: boolean
            @return squareCorners:
        """
        canny = LineDetector._toCanny(frame)
		# Detection
        if self.__algorithm == LineDetector.HOUGH:
            result = self._houghAlgorithm(canny)
        elif self.__algorithm == LineDetector.CONTOURS:
            contours, hierarchy = cv2.findContours(canny, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            result = self._contoursAlgorithm(contours, frame)

        self._eliminateRedundancies(result)
        verticals = self.xExtremes(self._verticals)
        horizontals = self.yExtremes(self._horizontals)
        
        success = True
        squareCorners = []
        if self.__Found(verticals, horizontals):
            for vertical in verticals:
                for horizontal in horizontals:
                    success, intersection = vertical.intersect(horizontal)
                    if success:
                        squareCorners.append(intersection)
            self.squareCorners = squareCorners
        else: success = False

        if success:
            self.__draw(frame)

        return success, self.squareCorners