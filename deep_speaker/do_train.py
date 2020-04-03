import asyncio
import argparse
import pickle
import yaml
from deep_speaker.toolbox import import_function
from makinage.data import pull


import numpy as np
import torch
from torch.utils.tensorboard import SummaryWriter


def load_config(config_file):
    with open(config_file, 'r') as f:
        return yaml.load(f)


def parse_arguments():
    parser = argparse.ArgumentParser("deep-speaker train")
    parser.add_argument("--config", required=True)
    return parser.parse_args()


def label_to_array(label):
    a = np.zeros(9300, dtype=np.float)
    a[label] = 1.0
    return a


async def train(config):
    loop = asyncio.get_running_loop()
    #device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    epoch_count = config['config']['train']['epoch_count']
    batch_size = config['config']['train']['batch_size']

    criterion = import_function(config['config']['train']['loss'])()
    model = import_function(config['config']['train']['model'])()
    #model.to(device)
    optimizer = import_function(config['config']['train']['optimizer'])(model.parameters())

    writer = SummaryWriter(config['config']['train']['summary_path'])
    print("train...")

    #writer.add_graph(model, verbose=True)
    #writer.close()

    step = 0
    for epoch in range(epoch_count):
        print("on epoch {}".format(epoch))
        train_data = pull(
            loop,
            config['kafka']['endpoint'],
            "feature_utterance",
            "train_set",
            batch_size=batch_size)

        running_loss = 0.0
        i = 0
        async for batch in train_data:
            # get the inputs; data is a list of [inputs, labels]
            batch = [pickle.loads(i.value) for i in batch]
            inputs = [np.expand_dims(i.data, axis=0) for i in batch]
            inputs = np.stack(inputs)
            inputs = torch.from_numpy(inputs)

            labels_class = [i.label for i in batch]
            labels_class = np.stack(labels_class)
            labels_class = torch.from_numpy(labels_class)

            labels = [label_to_array(i.label) for i in batch]
            labels = np.stack(labels)
            labels = torch.from_numpy(labels)

            #inputs, labels = data[0].to(device), data[1].to(device)

            # zero the parameter gradients
            optimizer.zero_grad()

            # forward + backward + optimize
            outputs = model(inputs.float())
            loss = criterion(outputs, labels_class)
            loss.backward()
            optimizer.step()

            # print statistics
            running_loss += loss.item()
            if i % 20 == 0:    # print every 2000 mini-batches
                writer.add_scalar('training loss',
                            running_loss / 1000,
                            step)

                print('[%d, %5d] loss: %.3f' %
                    (epoch + 1, i + 1, running_loss / 2000))
                running_loss = 0.0

            i += 1
            step += 1

    writer.close()
    print('Finished Training')


def main():
    args = parse_arguments()
    config = load_config(args.config)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(train(config))
