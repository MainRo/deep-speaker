Dataset split 
==============

The voxceleb2 dataset contains 2 sets: a train set and a test set.

The test set is composed as pairs of AP (Anchor/Positive) and AN (Anchor 
Negative) utterances. These pairs are used to evluate the model during 
training and at the end of the training. The evauation metric is the same
whether the training is done with a softmax or a triplet loss.

The test set is split in two sets: a train set and a dev set. The dev set is
used to evaluate the model during training. The test set is used to eavluate
the model at the end of the training.

Model evaluation
-----------------

