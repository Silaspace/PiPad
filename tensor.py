import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

from tensorflow.keras.datasets import mnist

model = keras.Sequential(
	[
		layers.Dense(784, activation="relu", input_shape=(28,28)),
		layers.Dense(600, activation="relu"),
		layers.Dense(400, activation="relu"),
		layers.Dense(36),
	]
)

def load_mnist_dataset():
	((trainData, trainLabels), (testData, testLabels)) = mnist.load_data()
	data = np.vstack([trainData, testData])
	labels = np.hstack([trainLabels, testLabels])
	return (data,labels)

train_dataset = tf.data.experimental.make_csv_dataset(
	"dataset_J",
	32,
	coloumn_names = ["col1","col2"],
	label_name = "col2",
	num_epochs = 1
).map(load_mnist_dataset)

data, labels = next(iter(train_dataset))

