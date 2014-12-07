import cv2
import cv2.cv as cv
import numpy as np

class Line:
	def __init__(self, img, start_row, end_row):
		self.img = img
		self.start_row = start_row
		self.end_row = end_row
		self.rows,self.cols = np.shape(img)
		self.staff_lines = []

	def translate_lines(self, all_staff_lines):
		for sl in all_staff_lines:
			if (sl > self.start_row) and (sl < self.end_row): #staff line in line
				self.staff_lines.append(sl-self.start_row)
		self.staff_lines.sort()

class MusicReader:

	'''
	A MusicReader has an image (filename passed as param) and whether
	it's two-handed music or not
	'''
	def __init__(self, im_name, twohanded):
		self.img = cv2.imread(im_name,0)
		self.rows, self.cols = np.shape(self.img)
		self.twohanded = twohanded
		self.staff_lines = []

	'''
	Main function that goes through the steps of reading and understanding the music
	1. split into lines
	2. chunk into notes, destroy all columns not containing a note
	3. go though chunked-up music and pull out specific notes as continuous units
	4. if it's twohanded, split each of these into top_row and bottom_row notes
	5. identify each note, both letter (E,G,etc) and type (quarter, half, etc)
	'''
	def read(self):
		self.staff_lines, widths = self.read_staff_lines(self.img)
		print "all staff lines", self.staff_lines
		lines = self.split_into_lines(self.img)
		for line_obj in lines:
			line = line_obj.img
			line_obj.translate_lines(self.staff_lines)
			print line_obj.start_row, line_obj.end_row, line_obj.staff_lines

			unbarred_line = self.destroy_non_note_cols(line)
			cv2.imshow('before',line)
			cv2.waitKey(0)
			cv2.imshow('test',unbarred_line)
			cv2.waitKey(0)
			notes = self.find_notes(unbarred_line)
			if notes != None:
				for note in notes:
					cv2.imshow('note',note)
					cv2.waitKey(0)
					if self.twohanded:
						hand_notes = self.split_into_lines(note)
						top_row = []
						bottom_row = []
						for i in range(len(hand_notes)):
							if i%2==0:
								top_row.append(hand_notes[i])
							else:
								bottom_row.append(hand_notes[i])
						#determine note types, in progress
						for n in top_row:
							self.read_note(n)

	'''
	Function that takes an input_img with multiple rows and splits it by each row
	Returns an array containing each row as a separate element
	'''
	def split_into_lines(self, input_img):
		rows,cols = np.shape(input_img)
		prev_row = 0
		lines = []

		current_row = 0

		row = 0
		while row<rows-1:
			row+=1
			brightnesses = self.get_row_brightnesses(row, input_img)
			current_row = row
			if not self.gray_in_brightnesses(brightnesses):
				while current_row < rows and not self.gray_in_brightnesses(self.get_row_brightnesses(current_row, input_img)):
					current_row+=1

				if current_row - row > 30:
					line = np.zeros([current_row - prev_row, cols])
					for r in range(current_row - prev_row):
						for col in range(cols):
							if input_img[r+prev_row][col] < 200:
								line[r][col] = 0
							else:
								line[r][col] = 255
					line_obj = Line(line, prev_row, current_row)
					lines.append(line_obj)
					prev_row = current_row
			row = current_row
		return lines

	'''
	Takes an input image (line) and goes through each column
	If that column contains no notes, it shades it white (erases it)
	If a column doesn't contain a note, then it's only 5 staff lines
	This determins the staff_line threshold as a percentage of black pixels
	and erases all columns with a smaller percentage than calculated
	'''
	def destroy_non_note_cols(self, input_img):
		rows,cols = np.shape(input_img)
		black_threshold = self.get_black_staff_threshold(input_img)
		unbarred_img = input_img.copy()
		for col in range(cols):
			total_black_in_col = 0
			for row in range(rows):
				if input_img[row][col]==0:
					total_black_in_col += 1
			if float(total_black_in_col)/rows < black_threshold:
				for row in range(rows):
					unbarred_img[row][col]=255
		return unbarred_img

	'''
	Uses connectivity search to take an input image and split it into
	individual notes by considering everything that's connected to be a note
	'''
	def find_notes(self, input_img):
		rows, cols = np.shape(input_img)

		boxes = []
		notes = []

		is_black = False

		start = 0
		for col in range(cols):
			brightnesses = []
			for row in range(rows):
				brightnesses.append(input_img[row][col])

			if 0 in brightnesses and is_black == False:
				start=col
				is_black=True
			if 0 not in brightnesses and is_black == True:
				if (col+1 - start-1) > 5:
					boxes.append((start-1,col+1))
				is_black = False

		for box in boxes:
			note = np.ones([rows, box[1]-box[0]])
			np.multiply(note,255)
			for c in range(box[0],box[1]):
				brightnesses = []
				for row in range(rows):
					brightnesses.append(input_img[row][c])

				loc_index = c - box[0]
				note[:,loc_index] = brightnesses

			# cv2.circle(input_img,(box[0],10),2,(0,0,255),3)
			# cv2.circle(input_img,(box[1],10),2,(0,0,255),3)

			notes.append(note)
		return notes

	def read_note(self, input_img):
		# TODO: take an input image note and identify it
		# BOTH AS quarter note/half etc, as well as E,G,F,etc
		# 
		# run staff lines on it
		# find center of black pixels, maybe using meanShift? or HoughCircles?
		pass

	'''
	Helper function to split_into_lines
	Takes an input image and a specific row in that image
	Returns a list of the pixel brightnesses of every pixel in that row
	'''
	def get_row_brightnesses(self, row, input_img):
		rows, cols = np.shape(input_img)
		brightnesses = []
		for col in range(cols):
			brightnesses.append(input_img[row][col])
		return brightnesses

	'''
	Helper function to split_into_lines
	Takes a list of brightnesses and tells you if any of the values from 0-20 are in it
	Originally we only looked for 0's, but the images are imperfect and have some gray in them
	This prevents it from looking past dark pixels that aren't perfect black
	'''
	def gray_in_brightnesses(self,brightnesses):
		grays = range(20)
		contains_gray = False
		for g in grays:
			if g in brightnesses:
				contains_gray = True
				break
		return contains_gray

	'''
	Helper function to destroy_non_note_cols
	Gets staff lines and determines their total pixelage
	Right now assuming every line has width 2
	This could be fixed
	'''
	def get_black_staff_threshold(self, input_img):
		rows,cols = np.shape(input_img)
		staff_lines, widths = self.read_staff_lines(input_img)
		if staff_lines:
			avg_width = 2 # 
			if widths:
				avg_width = sum(widths)/len(widths)
			return (len(staff_lines)*avg_width + 1)/float(rows)

			#return float(sum(widths)/rows)
			# staff_lines.sort()
			# #assert len(staff_lines)%2==0
			# sum_widths = 0

			# i=0

			# while i<len(staff_lines)-1:
			# 	if staff_lines[i+1] - staff_lines[i] > 10:
			# 		i+=1
			# 	else:
			# 		sum_widths += staff_lines[i+1] - staff_lines[i]
			# 		i+=2

			# sum_widths +=1

			# return float(sum_widths)/rows
		else:
			return 0

	'''
	Helper function to destroy_non_note_cols and get_black_staff_threshold
	Takes an input image and uses HoughLines to find staff lines
	Returns a list of lines with their y-values
	Only one line per actual staff line ***
	'''
	def read_staff_lines(self, input_img):

		rows,cols = np.shape(input_img)
		nump_arr = np.zeros([rows,cols])
		for r in range(rows):
			for c in range(cols):
				if input_img[r][c] < 200:
					nump_arr[r][c] = 0
				else:
					nump_arr[r][c] = 255

		copy = np.uint8(nump_arr)
		edges = cv2.Canny(copy,150,700)
		lines = cv2.HoughLines(edges,1,np.pi/180,250)
		staff_lines = []
		widths = []
		if lines != None:   
			for rho,theta in lines[0]:
				a = np.cos(theta)
				b = np.sin(theta)
				x0 = a*rho
				y0 = b*rho
				x1 = int(x0 + 1000*(-b))
				y1 = int(y0 + 1000*(a))
				x2 = int(x0 - 1000*(-b))
				y2 = int(y0 - 1000*(a))

				th = 6 #pixels
				too_close = False
				for y in staff_lines:
					if abs(y - y1) <= th:
						too_close = True
						widths.append(abs(y - y1))
				if not too_close:
					staff_lines.append((y1))
		staff_lines.sort()
		for y in staff_lines:
			cv2.line(nump_arr,(0,y),(cols,y),(0,0,255),2)
		return staff_lines, widths

if __name__ == "__main__":
	mr = MusicReader("./images/ode_to_joy.png", True)
	mr.read()