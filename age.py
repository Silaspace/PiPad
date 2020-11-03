import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers


#Model

model = keras.Sequential(
    [
        layers.Input(shape=(1)),
        layers.Dense(3, activation="relu"),
        layers.Dense(4),
    ]
)

feature_extractor = keras.Model(
    inputs=model.inputs,
    outputs=[layer.output for layer in model.layers],
)



#Dataset

#train_dataset_fp = tf.keras.utils.get_file(fname=os.path.basename(train_dataset_url), origin=train_dataset_url)
batch_size = 32

train_dataset = tf.data.experimental.make_csv_dataset(
    train_dataset_fp,
    batch_size,
    column_names=["age", "class"],
    label_name=label_name,
    num_epochs=1)

# Call model on a test input
x = tf.ones(1)
y = model(x)

model.summary()
#print(feature_extractor(x))

