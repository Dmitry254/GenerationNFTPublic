import pandas as pd
import numpy as np
import time
import os
from progressbar import progressbar
import json
from copy import deepcopy

import warnings

warnings.simplefilter(action='ignore', category=FutureWarning)

BASE_IMAGE_URL = "ipfs://<-- Your CID Code-->"
BASE_NAME = ""

BASE_JSON = {
    "name": BASE_NAME,
    "description": "",
    "image": BASE_IMAGE_URL,
    "attributes": [],
}


def generate_paths(edition_name):
    edition_path = os.path.join('output', 'edition ' + str(edition_name))
    metadata_path = os.path.join(edition_path, 'metadata.csv')
    json_path = os.path.join(edition_path, 'json')

    return edition_path, metadata_path, json_path


def clean_attributes(attr_name):
    clean_name = attr_name.replace('_', ' ')
    clean_name = list(clean_name)

    for idx, ltr in enumerate(clean_name):
        if (idx == 0) or (idx > 0 and clean_name[idx - 1] == ' '):
            clean_name[idx] = clean_name[idx].upper()

    clean_name = ''.join(clean_name)
    return clean_name


def get_attribute_metadata(metadata_path):
    df = pd.read_csv(metadata_path)
    df = df.drop('Unnamed: 0', axis=1)
    df.columns = [clean_attributes(col) for col in df.columns]
    zfill_count = len(str(df.shape[0] - 1))

    return df, zfill_count


def main():
    print("Enter edition you want to generate metadata for: ")
    while True:
        edition_name = input()
        edition_path, metadata_path, json_path = generate_paths(edition_name)

        if os.path.exists(edition_path):
            print("Edition exists! Generating JSON metadata...")
            break
        else:
            print("Oops! Looks like this edition doesn't exist! Check your output folder to see what editions exist.")
            print("Enter edition you want to generate metadata for: ")
            continue

    if not os.path.exists(json_path):
        os.makedirs(json_path)

    df, zfill_count = get_attribute_metadata(metadata_path)

    for idx, row in progressbar(df.iterrows()):

        item_json = deepcopy(BASE_JSON)

        item_json['name'] = item_json['name'] + str(idx)

        item_json['image'] = item_json['image'] + '/' + str(idx).zfill(zfill_count) + '.png'

        attr_dict = dict(row)

        for attr in attr_dict:

            if attr_dict[attr] != 'none':
                item_json['attributes'].append({'trait_type': attr, 'value': attr_dict[attr]})

        item_json_path = os.path.join(json_path, str(idx))
        with open(item_json_path, 'w') as f:
            json.dump(item_json, f)


if __name__ == '__main__':
    main()
