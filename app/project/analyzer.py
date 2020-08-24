import numpy as np

def get_length_distribution(list):
	d = []
	for i in list:
		d.append(len(i))
	return np.array(d)