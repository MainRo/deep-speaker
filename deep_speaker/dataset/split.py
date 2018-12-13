import itertools


def train_test_split(utterances):
    ''' split the dataset in train/dev/test

    The train set is the list of files from the voxceleb2 train set.
    The test set of voxceleb2 is split in two sets, dev/test.
    The dev set should be relatviely small so that training time is not
    increased significantly.

    Parameters
    ----------
    utterances : list of dict
        A list of dicts with file/label/set keys

    Returns
    -------
    dataset : dict
        a dict containing the train/dev/test sets.
    '''
    dataset = {
        'train': [],
        'test': []
    }

    for utterance in utterances:
        if utterance['set'] == 'train':
            dataset['train'].append({
                'file': utterance['file'],
                'label': utterance['label']
            })
        else:
            dataset['test'].append({
                'file': utterance['file'],
                'label': utterance['label']
            })

    return dataset


def pair_set(dataset):
    ''' Pair utterances in dataset as ap/an

    build pair from the utterances in a balanced way between ap/an utterances.
    '''
    groups = []
    ap = []
    an = []
    dataset = sorted(dataset, key=lambda i: i['label'])
    for key, group in itertools.groupby(dataset, lambda i: i['label']):
        groups.append(list(group))

    for group in groups:
        ap.extend(list(itertools.combinations(group, 2)))

    tmp_an = itertools.combinations(dataset, 2)
    for n in tmp_an:
        if n[0]['label'] != n[1]['label']:
            an.append(n)
            if len(an) >= len(ap):
                break

    return ap + an


def test_dev_split(dataset, dev_set_size, test_set_size):
    return {
        'dev': dataset[0:dev_set_size],
        'test': dataset[dev_set_size:dev_set_size+test_set_size]
    }
