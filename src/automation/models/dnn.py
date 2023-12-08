import os
import typing as t

import numpy as np
import tensorflow as tf

from automation.utils import get_logger

logger = get_logger("models.dnn")

LEARNING_RATE = float(os.getenv("MODULE_LEARNING_RATE", 0.01))


class DNNAgent:
    def __init__(
        self,
        model: tf.keras.models.Model,
        optimizer: t.Optional[tf.keras.optimizers.Optimizer] = None,
        loss: t.Optional[tf.losses.Loss] = None,
    ):
        if not optimizer:
            optimizer = tf.keras.optimizers.Nadam(learning_rate=LEARNING_RATE)

        if not loss:
            loss = tf.losses.MeanAbsoluteError()

        model.compile(optimizer=optimizer, loss=loss)
        self.model = model
        self.optimizer = optimizer
        self.loss = loss

    @classmethod
    def from_raw(cls, parameters: t.Sequence[str], values: t.Sequence[str]):
        model = create_dnn_network(parameters, values)

        logger.debug(f"Created model with inputs <{', '.join(parameters)}> " + f"and outputs <{', '.join(values)}>")

        return cls(model)

    def train(self, x: t.Dict[str, np.ndarray], y: t.Dict[str, np.ndarray], epochs: int, batch_size: int = 16):
        return self.model.fit(x, y, batch_size=batch_size, epochs=epochs, verbose=False, shuffle=True)

    def evaluate(self, x: t.Dict[str, np.ndarray], y: t.Dict[str, np.ndarray], batch_size: int = 16):
        return self.model.evaluate(x, y, batch_size=batch_size, verbose=False)

    def predict(self, x: t.Dict[str, np.ndarray]) -> t.Dict[str, np.ndarray]:
        return self.model(x)


def create_dnn_network(parameters: t.Sequence[str], values: t.Sequence[str]):
    inputs = {}
    outputs = {}

    for parameter in parameters:
        inputs[parameter] = tf.keras.layers.Input(shape=(1,), name=parameter)

    layer = tf.keras.layers.Concatenate(axis=-1)(list(inputs.values()))
    layer = tf.keras.layers.Dense(128, activation="relu")(layer)
    layer = tf.keras.layers.Dense(64, activation="relu")(layer)

    for value in values:
        # FIXME: same named inputs and outputs will not work
        # train and predict should implement renaming inputs and outputs to proper names
        outputs[value] = tf.keras.layers.Dense(1, activation="tanh")(layer)

    return tf.keras.models.Model(inputs=inputs, outputs=outputs)
