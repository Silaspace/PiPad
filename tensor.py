import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.datasets import mnist

import matplotlib.pyplot as plt
import numpy as np
import argparse

"""
def load
"""

def load_az_dataset(datasetPath):
	data=[]
	labels=[]
	for row in open(datasetPath):
		row=row.split(",")
		label=int(row[0])
		image=np.array([int(x) for x in row[1:]], dtype="unit8")
		image=image.reshape((28,28))
		data.append(image)
		labels.append(label)
	data=np.array(data, dtype="float32")
	labels = np.array(labels, dtype="int")

	return(data, labels)

def load_mnist_dataset():
	((trainData, trainLabels), (testData, testLabels)) = mnist.load_data()
	data = np.vstack([trainData, testData])
	labels = np.hstack([trainLabels, testLabels])
	return (data,labels)

"""
def load
"""

#model

model = keras.Sequential(
	[
		layers.Dense(784, activation="relu", input_shape=(28,28)),
		layers.Dense(600, activation="relu"),
		layers.Dense(400, activation="relu"),
		layers.Dense(36),
	]
)

#model

ap = argparse.ArgumentParser()
ap.add_argument("-a", "--az", required=True, help="path to A-Z dataset")
ap.add_argument("-m","--model", type=str, required=True, help="path to output trained handwriting recognition model")
ap.add_argument("-p","--plot", type=str, default="plot.png", help="path to output training history file")
args=vars(ap.parse_args())

print(("[INFO] loading datasets..."))
(digitsData, digitsLabels) = load_mnist_dataset()

