import os
import numpy as np
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





# Dataset

def pack_features_vector(features, labels):
  features = tf.stack(list(features.values()), axis=1)
  return features, labels


train_dataset = tf.data.experimental.make_csv_dataset(
  "dataset.csv",
  32,
  column_names=["age", "class"],
  label_name="class",
  num_epochs=1
).map(pack_features_vector)


features, labels = next(iter(train_dataset))





# Cost Function

loss_object = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)


def loss(model, x, y, training):
  y_ = model(x, training=training)
  return loss_object(y_true=y, y_pred=y_)


def grad(model, inputs, targets):
  with tf.GradientTape() as tape:
    loss_value = loss(model, inputs, targets, training=True)
  return loss_value, tape.gradient(loss_value, model.trainable_variables)





# Optimiser Loop

num_epochs = 1
optimizer = tf.keras.optimizers.SGD(learning_rate=0.01)


for epoch in range(num_epochs):
  # Accuracy Calculations
  epoch_loss_avg = tf.keras.metrics.Mean()
  epoch_accuracy = tf.keras.metrics.SparseCategoricalAccuracy()


  for x, y in train_dataset:
    # Optimiser
    loss_value, grads = grad(model, x, y)
    optimizer.apply_gradients(zip(grads, model.trainable_variables))


    # Track progress
    epoch_loss_avg.update_state(loss_value)
    epoch_accuracy.update_state(y, model(x, training=True))


  print("Epoch {:03d}: Loss: {:.3f}, Accuracy: {:.3%}".format(epoch, epoch_loss_avg.result(), epoch_accuracy.result())) if epoch % 32 == 0 else None





# Use Model

test_dataset = tf.data.experimental.make_csv_dataset(
  "test.csv",
  1,
  column_names=["age", "class"],
  label_name="class",
  num_epochs=1,
  shuffle=False
).map(pack_features_vector)


for (x, y) in test_dataset:
  logits = model(x, training=False)
  prediction = tf.argmax(logits, axis=1, output_type=tf.int32)

  print(x)
  print(prediction)
  print(y)
  print()