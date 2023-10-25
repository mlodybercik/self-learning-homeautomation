import typing as t
import tensorflow as tf
import numpy as np

class DNNAgent:
    def __init__(self, parameters: t.Sequence[str], values: t.Sequence[str], learning_rate: float = 0.005):
        self.model = create_dnn_network(parameters, values)
        self.optimizer = tf.keras.optimizers.Adam(learning_rate=learning_rate)
        self.loss = tf.losses.MeanSquaredError(reduction='sum')
        self.model.compile(optimizer=self.optimizer, loss=self.loss)

    def train(self, x: t.Dict[str, np.ndarray], y: t.Dict[str, np.ndarray], epochs: int):
        return self.model.fit(x, y, 16, epochs=epochs, verbose=True)

    def predict(self, x: t.Dict[str, np.ndarray]) -> t.Dict[str, np.ndarray]:
        return self.model.predict(x, verbose=False)

def create_dnn_network(parameters: t.Sequence[str], values: t.Sequence[str]):
    inputs = {}
    outputs = {}

    for parameter in parameters:
        inputs[parameter] = tf.keras.layers.Input(shape=(1,), name=parameter)
    
    input = tf.keras.layers.Concatenate(axis=-1)(list(inputs.values()))
    proper_input = tf.keras.layers.Flatten()(input)
    layer = tf.keras.layers.Dense(128, activation='relu')(proper_input)
    layer = tf.keras.layers.Dense(64, activation='relu')(layer)
    
    for value in values:
        outputs[value] = tf.keras.layers.Dense(1, activation='tanh')(layer)

    return tf.keras.models.Model(inputs=inputs, outputs=outputs)