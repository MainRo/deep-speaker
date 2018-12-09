
def split_dataset(utterances, dev_set_count):
    ''' split the dataset in train/dev/test

    The train set is the list of files from the voxceleb2 train set.
    The test set of voxceleb2 is split in two sets, dev/test.
    The dev set should be relatviely small so that training time is not
    increased significantly.

    Parameters
    ----------
    utterances : list of dict
        A list of dicts with file/label/set keys

    dev_set_count: int
        Number of utterances to put in the dev set

    Returns
    -------
    dataset : dict
        a dict containing the train/dev/test sets.
    '''
    dataset = {
        'train': [],
        'dev': [],
        'test': []
    }

    for utterance in utterances:
        if utterance['set'] == 'train':
            dataset['train'].append({
                'file': utterance['file'],
                'label': utterance['label']
            })

    return dataset
