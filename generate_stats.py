import ecdsa
from Crypto.Hash import keccak
import json
import traceback
import base64
import os

from web3 import Web3
from web3.middleware import geth_poa_middleware

from PIL import Image, ImageDraw, ImageFont


def generate_wallet():
    private_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)

    public_key_hex = private_key.get_verifying_key().to_string().hex()

    public_key_as_bytes = bytes.fromhex(str(public_key_hex))

    keccak_hash = keccak.new(digest_bits=256)
    keccak_hash.update(public_key_as_bytes)
    full_keccak_hash = str(keccak_hash.hexdigest())

    return full_keccak_hash[24:]


def save_wallets(wallets_dict):
    with open('wallets.json', 'w') as json_file:
        json.dump(wallets_dict, json_file)


def create_wallets_json():
    wallets_dict = {"wallets": []}
    for i in range(1000):
        wallet_address = "0x" + generate_wallet()
        wallets_dict["wallets"].append(wallet_address)
    return wallets_dict


def read_wallets():
    with open('wallets.json') as json_file:
        return json.load(json_file)['wallets']


def generate_stats(wallet):
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
    return hp, damage


def check_whitelist(wallet):
    if (wallet[2] == "3" or wallet[3] == "3" or wallet[4] == "3") and (wallet[-3] == "3" or wallet[-2] == "3" or wallet[-1] == "3"):
        return True
    else:
        return False


def set_http_web3(bsc):
    web3 = Web3(Web3.HTTPProvider(bsc))
    web3.middleware_onion.inject(geth_poa_middleware, layer=0)
    return web3


def get_transaction_data(web3, contract, transaction_hash):
    transaction = web3.eth.getTransaction(transaction_hash)
    func_obj, func_params = contract.decode_function_input(transaction["input"])
    return func_obj, func_params


def get_contract(web3, contract_address, increase_abi_file):
    f = open(increase_abi_file)
    abi = json.load(f)
    contract = web3.eth.contract(contract_address, abi=abi)
    f.close()
    return contract


def check_stats(wallet, hp, damage):
    try:
        contract_hp, contract_damage = contract.functions.generateStatsView(web3.to_checksum_address(wallet)).call()
        contract_hp = int(contract_hp)
        contract_damage = int(contract_damage)
        if contract_hp != hp or contract_damage != damage:
            print(f"Ошибка {hp} и {contract_hp}, {damage} и {contract_damage}")
        else:
            print("Совпадение")
    except:
        error = traceback.format_exc()
        print(error)


def get_wallets_from_web3():
    for block in range(28556300, 28556322):
        block_info = web3.eth.get_block(block)
        print(block_info)


def get_transfer_event():
    try:
        my_filter = contract.events.Transfer.createFilter(fromBlock="latest")
        event_list = my_filter.get_all_entries()
        print(event_list)
    except:
        error = traceback.format_exc()
        print(error)


def get_nft_stats(token_id):
    try:
        token_uri = contract.functions.tokenURI(token_id).call()[29:]
        decode_token_uri = json.loads(base64.b64decode(token_uri).decode("utf-8"))
        nft_number = decode_token_uri['name']
        nft_hp = decode_token_uri['hp']
        nft_damage = decode_token_uri['damage']
        print(nft_number, nft_hp, nft_damage)
        return nft_hp, nft_damage
    except:
        error = traceback.format_exc()
        print(error)


def add_stats(token_id):
    hp, damage = get_nft_stats(token_id)
    img = Image.open(os.path.join('img', 'knights', 'knights', f"{token_id}.png"))
    font = ImageFont.truetype('D:/GenerationNFT/Videotype.ttf', size=18)
    draw_text = ImageDraw.Draw(img)
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
    if not os.path.exists(os.path.join('img', 'knights', 'knights_stats')):
        os.makedirs(os.path.join('img', 'knights', 'knights_stats'))
    img.save(os.path.join('img', 'knights', 'knights_stats', f"{token_id}.png"))


if __name__ == '__main__':
    hp_sum = 0
    damage_sum = 0
    min_hp = 10000
    max_hp = 0
    min_damage = 10000
    max_damage = 0
    whitelists = 0
    wallets = ['']

    private_key = ""
    my_address = ""
    contract_address = ""

    bsc = "https://data-seed-prebsc-1-s3.binance.org:8545"

    contract_abi = "contract_abi.json"

    web3 = set_http_web3(bsc)
    contract = get_contract(web3, contract_address, contract_abi)
    wallets = create_wallets_json()['wallets']
    print(wallets)
    for wallet in wallets:
        hp, damage = generate_stats(wallet)
        hp_sum += hp
        damage_sum += damage
        is_whitelist = check_whitelist(wallet)
        if is_whitelist:
            whitelists += 1
        print(f"hp - {hp}, damage - {damage}, address - {wallet}")

        if hp > max_hp:
            max_hp = hp
        if hp < min_hp:
            min_hp = hp
        if damage > max_damage:
            max_damage = damage
        if damage < min_damage:
            min_damage = damage
    hp_avg = hp_sum / len(wallets)
    damage_avg = damage_sum / len(wallets)
    print(hp_avg)
    print(damage_avg)
    print(f"Максимальное hp - {max_hp}, минимальное hp - {min_hp}, максимальный damage - {max_damage}, минимальный damage - {min_damage}")
