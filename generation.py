from PIL import Image, ImageDraw, ImageFont
import time
import os
import random
import json

from web3 import Web3
from web3.middleware import geth_poa_middleware
from config import CONFIG


def parse_config():
    assets_path = 'img'

    for layer in CONFIG:
        layer_path = os.path.join(assets_path, layer['directory'])
        traits = sorted([trait for trait in os.listdir(layer_path) if trait[0] != '.'])
        if not layer['required']:
            traits = [None] + traits
        if layer['rarity_weights'] is None:
            rarities = [1 for x in traits]
        elif layer['rarity_weights'] == 'random':
            rarities = [random.random() for x in traits]
        elif type(layer['rarity_weights'] == 'list'):
            assert len(traits) == len(layer['rarity_weights']), "Make sure you have the current number of rarity weights"
            rarities = layer['rarity_weights']
        else:
            raise ValueError("Rarity weights is invalid")

        layer['rarity_weights'] = rarities
        layer['traits'] = traits


def save_metadata(metadata, nft_name, op_path):
    with open(f'{op_path}/{nft_name}.json', 'w') as json_file:
        json.dump(metadata, json_file)


def hex_to_rgb(hex):
    rgb = []
    for i in (0, 2, 4):
        decimal = int(hex[i:i+2], 16)
        rgb.append(decimal)

    return tuple(rgb)


def generate_single_image(filepaths, hp, damage, color, output_filename=None):
    print(filepaths)
    bg = Image.open(os.path.join('img', filepaths[0]))
    bg.paste(hex_to_rgb(color), [0, 0, bg.size[0], bg.size[1]])

    for filepath in filepaths[1:]:
        if filepath.endswith('.png'):
            img = Image.open(os.path.join('img', filepath))
            bg.paste(img, (0, 0), img)

    font = ImageFont.truetype('D:/GenerationNFT/Videotype.ttf', size=18)
    draw_text = ImageDraw.Draw(bg)
    draw_text.text(
        (20, 20),
        str(hp),
        font=font,
        fill=('#ff002a')
    )
    draw_text.text(
        (20, 50),
        str(damage),
        font=font,
        fill=('#000000')
    )

    if output_filename is not None:
        bg.save(output_filename)
    else:
        if not os.path.exists(os.path.join('output', 'single_images')):
            os.makedirs(os.path.join('output', 'single_images'))
        bg.save(os.path.join('output', 'single_images', str(int(time.time())) + '.png'))


def get_total_combinations():
    total = 1
    for layer in CONFIG:
        total = total * len(layer['traits'])
    return total


def generate_trait_set_from_config(hp, damage):
    trait_set = []
    trait_paths = []

    for layer in CONFIG:
        traits, rarities = layer['traits'], layer['rarity_weights']
        trait_index = -1
        if layer['id'] == 4 or layer['id'] == 5:
            if layer['id'] == 4:
                param = hp
            else:
                param = damage
            for weight in layer['rarity_weights']:
                if param > weight:
                    trait_index += 1
                else:
                    trait_set.append(traits[trait_index])
                    trait_path = os.path.join(layer['directory'], traits[trait_index])
                    trait_paths.append(trait_path)
                    break
                if weight == layer['rarity_weights'][-1]:
                    trait_set.append(traits[trait_index])
                    trait_path = os.path.join(layer['directory'], traits[trait_index])
                    trait_paths.append(trait_path)
        else:
            chosen_trait = random.choice(traits)
            trait_set.append(chosen_trait)
            if chosen_trait is not None:
                trait_path = os.path.join(layer['directory'], chosen_trait)
                trait_paths.append(trait_path)
    return trait_set, trait_paths


def generate_images(edition, count, hp, damage, color, knight_number, image_name):
    rarity_table = {}
    for layer in CONFIG:
        rarity_table[layer['name']] = []

    op_path = os.path.join('output', 'edition ' + str(edition), 'images')
    json_path = os.path.join('output', 'edition ' + str(edition), 'json')

    zfill_count = len(str(count - 1))

    if not os.path.exists(op_path):
        os.makedirs(op_path)

    if not os.path.exists(json_path):
        os.makedirs(json_path)

    for n in range(count):
        metadata = {"name": "Test #",
                    "symbol": "TST",
                    "description": "Test generator",
                    "external_url": "",
                    "image": "",
                    "attributes": [{"trait_type": "Background", "value": ""},
                                   {"trait_type": "Knight", "value": "Knight "},
                                   {
                                       "display_type": "number",
                                       "trait_type": "Health Points",
                                       "value": 0
                                   },
                                   {
                                       "display_type": "number",
                                       "trait_type": "Damage",
                                       "value": 0
                                   }]}

        image_name_png = image_name + '.png'
        trait_sets, trait_paths = generate_trait_set_from_config(hp, damage)
        generate_single_image(trait_paths, hp, damage, color, os.path.join(op_path, image_name_png))

        metadata['name'] += image_name
        metadata['image'] += image_name
        metadata['attributes'][0]['value'] = color
        metadata['attributes'][1]['value'] += knight_number
        metadata['attributes'][2]['value'] = hp
        metadata['attributes'][3]['value'] = damage

        save_metadata(metadata, image_name, json_path)
    return metadata


def generate_stats(wallet, address_number):
    bonus_hp = 0
    bonus_damage = 10
    hp = 0
    for i in range(2, 42):
        if wallet[i].isdigit():
            bonus_hp += int(wallet[i])
            hp += 1
            if bonus_damage == 10 and i != 2:
                bonus_damage = i - 2
    damage = 40 - hp
    if damage == hp:
        bonus_damage *= 1
    else:
        bonus_damage *= abs(damage - hp)
    hp *= bonus_hp
    damage *= bonus_damage
    knight_number = str(int(address_number) % 20)
    return hp, damage, wallet[2:8], knight_number


def main(wallet, file_name):
    parse_config()

    tot_comb = get_total_combinations()
    print(f"You can create a total of {tot_comb} distinct avatars")
    num_avatars = 1

    edition_name = "test"

    hp, damage, color, knight_number = generate_stats(wallet, file_name)
    print(color)
    metadata = generate_images(edition_name, num_avatars, hp, damage, color, knight_number, file_name)
    print(metadata)


if __name__ == '__main__':
    wallets = ['0xe5200e5d24ebd6c24621a3e2e3e439e66cb35be2', '0xc32ebc9e32c8da0bbc890469cf3361137714a9f3',
               '0x81d904be6d1edb9be32a3040f27b450751717e53', '0x09bf5aa3bec0a4dfab93d889c9505628ea6bde03',
               '0x8968b4e9bd8d771b175c7ea4885c1603b62d5b93', '0x8e80472cab83d6ce691e4b0a684f987a3ce6fc84',
               '0x02986e6b5ca3f4885ade7e0c15a3a723c22af124', '0x39482f05ad798e15effb214417bf0633dcfc8664',
               '0x8dcbc7ce257d2ec08887d897e57dccdcf646e605', '0xd720fc0bc4fc12dd37f4913c358fb2977e2aa77e',
               '0xf235b2298e34d1b9b12945e7213fc5742d3324d9', '0xb80b6da844cbf3c10b47d547a30b98da87eca0f1']
    for wallet in wallets:
        image_name = str(wallets.index(wallet) + 1)
        main(wallet, image_name)
