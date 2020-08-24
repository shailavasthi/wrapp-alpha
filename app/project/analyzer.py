import numpy as np

def get_length_distribution(list):
	d = []
	for i in list:
		d.append(len(i))
	return np.array(d)

def get_reading_level(flesch_score):
	if 90 < flesch_score:
		reading_level = '5th Grade'
	elif 80 < flesch_score <= 90:
		reading_level = '6th Grade'
	elif 70 < flesch_score <= 80:
		reading_level = '7th Grade'
	elif 60 < flesch_score <= 70:
		reading_level = '8th & 9th Grade'
	elif 50 < flesch_score <= 60:
		reading_level = '10th to 12th Grade'
	elif 30 < flesch_score <= 50:
		reading_level = 'College Student'
	elif 10 < flesch_score <= 30:
		reading_level = 'College Graduate'
	else: 
		reading_level = 'Professional'

	return reading_level