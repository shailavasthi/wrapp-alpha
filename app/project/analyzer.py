import base64
import io
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

def gen_hist(d):
	# Generate the figure **without using pyplot**.
	fig = Figure()
	ax = fig.subplots()
	num_bins = 10
	ax.hist(d, num_bins, histtype='bar', ec='black')
	ax.set_xlabel('Sentence Length')
	ax.set_ylabel('Frequency')
	ax.set_title('Histogram of Sentence Length')

	# Save it to a temporary buffer.
	pngImage = io.BytesIO()
	FigureCanvas(fig).print_png(pngImage)

	# Encode PNG image to base64 string
	pngImageB64String = "data:image/png;base64,"
	pngImageB64String += base64.b64encode(pngImage.getvalue()).decode('utf8')

	return pngImageB64String

def gen_bar(word_list):
	fig = Figure()
	ax = fig.subplots()
	words = list(zip(*word_list))[0]
	counts = list(zip(*word_list))[1]
	y_pos = np.arange(len(words)) 
	
	ax.barh(y_pos, counts,align='center')
	ax.invert_yaxis()
	ax.set_yticks(y_pos) 
	ax.set_yticklabels(words)
	ax.set_xlabel('Count')
	ax.set_title('Most Common Words')
	
	# Save it to a temporary buffer.
	pngImage = io.BytesIO()
	FigureCanvas(fig).print_png(pngImage)

	# Encode PNG image to base64 string
	pngImageB64String = "data:image/png;base64,"
	pngImageB64String += base64.b64encode(pngImage.getvalue()).decode('utf8')
	return pngImageB64String

def get_length_distribution(list):
	d = []
	for i in list:
		d.append(len(i))
	return np.array(d)