# -*- coding: utf-8 -*-
from __future__ import (absolute_import, unicode_literals, print_function)

import sys
import time
import logging
import numpy as np

if len(sys.argv) == 1:
    print("ERROR: Please specify implementation to benchmark, 'sknn' 'dbn' or 'lasagne'.")
    sys.exit(-1)

np.set_printoptions(precision=4)
np.set_printoptions(suppress=True)
logging.basicConfig(format="%(message)s", level=logging.DEBUG, stream=sys.stdout)


from sklearn.base import clone
from sklearn.cross_validation import train_test_split
from sklearn.datasets import fetch_mldata
from sklearn.metrics import classification_report


mnist = fetch_mldata('mnist-original')
X_train, X_test, y_train, y_test = train_test_split(
        (mnist.data / 255.0).astype(np.float32),
        mnist.target.astype(np.int32),
        test_size=0.33, random_state=1234)


classifiers = []

if 'dbn' in sys.argv:
    from nolearn.dbn import DBN
    clf = DBN(
        [X_train.shape[1], 300, 10],
        learn_rates=0.3,
        learn_rate_decays=0.9,
        epochs=10,
        verbose=1)
    classifiers.append(('nolearn.dbn', clf))

if 'sknn' in sys.argv:
    from sknn.mlp import Classifier, Layer

    clf = Classifier(
        layers=[Layer("Rectifier", units=300), Layer("Softmax")],
        learning_rate=0.02,
        learning_rule='momentum',
        learning_momentum=0.9,
        batch_size=25,
        valid_size=0.0,
        n_stable=10,
        n_iter=10,
        # verbose=1,
    )
    classifiers.append(('sknn.mlp', clf))

if 'lasagne' in sys.argv:
    from nolearn.lasagne import NeuralNet, BatchIterator
    from lasagne.layers import InputLayer, DenseLayer
    from lasagne.nonlinearities import softmax
    from lasagne.updates import nesterov_momentum

    clf = NeuralNet(
        layers=[
            ('input', InputLayer),
            ('hidden1', DenseLayer),
            ('output', DenseLayer),
            ],
        input_shape=(None, 784),
        output_num_units=10,
        output_nonlinearity=softmax,
        eval_size=0.0,

        more_params=dict(
            hidden1_num_units=300,
        ),

        update=nesterov_momentum,
        update_learning_rate=0.02,
        update_momentum=0.9,
        batch_iterator_train=BatchIterator(batch_size=25),

        max_epochs=10,
        # verbose=1
        )
    classifiers.append(('nolearn.lasagne', clf))


RUNS = 1

for name, orig in classifiers:
    times = []
    accuracies = []
    for i in range(RUNS):
        start = time.time()

        clf = clone(orig)
        clf.random_state = int(time.time())
        clf.fit(X_train, y_train)

        y_pred = clf.predict(X_test)
        accuracies.append(clf.score(X_test, y_test))
        times.append(time.time() - start)

    a_t = np.array(times)
    a_s = np.array(accuracies)

    print("\n"+name)
    print("\tAccuracy: %5.2f%% ±%4.2f" % (100.0 * a_s.mean(), 100.0 * a_s.std()))
    print("\tTimes:    %5.2fs ±%4.2f" % (a_t.mean(), a_t.std()))
    print("\tReport:")
    print(classification_report(y_test, y_pred))
