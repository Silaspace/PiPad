import os
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers


# Model

model = keras.Sequential(
    [
        layers.Dense(120, activation="relu", input_shape=(1,)),
        layers.Dense(80, activation="relu"),
        layers.Dense(40, activation="relu"),
        layers.Dense(10),
    ]
)

feature_extractor = keras.Model(
    inputs=model.inputs,
    outputs=[layer.output for layer in model.layers],
)





# Dataset

train_dataset = tf.data.experimental.make_csv_dataset(
    "dataset.csv",
    1,
    column_names=["age", "class"],
    label_name="class",
    num_epochs=1)

def pack_features_vector(features, labels):
    features = tf.stack(list(features.values()), axis=1)
    return features, labels

train_dataset = train_dataset.map(pack_features_vector)
features, labels = next(iter(train_dataset))





# Call model

predictions = model(features)
probability = tf.nn.softmax(predictions)

print("Prediction: {}".format(tf.argmax(predictions, axis=1)))
print("    Labels: {}".format(labels))





# Cost

loss_object = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)

def loss(model, x, y, training):
  y_ = model(x, training=training)
  return loss_object(y_true=y, y_pred=y_)

def grad(model, inputs, targets):
  with tf.GradientTape() as tape:
    loss_value = loss(model, inputs, targets, training=True)
  return loss_value, tape.gradient(loss_value, model.trainable_variables)

l = loss(model, features, labels, training=False)
print("Loss test: {}".format(l))





# Optimiser

optimizer = tf.keras.optimizers.SGD(learning_rate=0.01)

loss_value, grads = grad(model, features, labels)
print("Step: {}, Initial Loss: {}".format(optimizer.iterations.numpy(), loss_value.numpy()))
optimizer.apply_gradients(zip(grads, model.trainable_variables))
print("Step: {},         Loss: {}".format(optimizer.iterations.numpy(), loss(model, features, labels, training=True).numpy()))