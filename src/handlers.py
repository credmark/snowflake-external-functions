import json
import logging
from eth_utils import event_abi_to_log_topic
from eth_utils import function_abi_to_4byte_selector

from web3 import Web3
from eth_abi import decode_abi
logger = logging.getLogger()
logger.setLevel(logging.INFO)

HEADERS = {"Content-Type": "application/json"}


def to_signature_handler(event: dict, context: dict) -> dict:
    """Takes in Snowflake data and calculates an event/method signature"""

    event_data = _parse_event_for_data(event)
    logger.info(f"event data: {event_data}")

    for row in event_data:
        row[1] = to_signature(row[1])

    return {
        "statusCode": 200,
        "headers": HEADERS,
        "body": json.dumps({"data": event_data})
    }


def to_signature_hash_handler(event: dict, context: dict) -> dict:
    """Takes in Snowflake data and calculates an event/method signature hash"""

    event_data = _parse_event_for_data(event)
    logger.info(f"event data: {event_data}")

    for row in event_data:
        row[1] = to_signature_hash(row[1])

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"data": event_data})
    }


def decode_contract_event_handler(event: dict, context: dict) -> dict:
    """Takes in Snowflake data and decodes contract events"""

    event_data = _parse_event_for_data(event)
    logger.info(f"event data: {event_data}")

    for row in event_data:
        row[1] = decode_contract_event(row[1], row[2], row[3])
        row.pop(3)
        row.pop(2)

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"data": event_data})
    }


def decode_contract_function_handler(event: dict, context: dict) -> dict:
    """Takes in Snowflake data and decodes contract functions"""

    event_data = _parse_event_for_data(event)
    logger.info(f"event data: {event_data}")

    for row in event_data:
        row[1] = decode_contract_function(row[1], row[2], row[3])
        row.pop(3)
        row.pop(2)

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"data": event_data})
    }


def to_signature(abi: dict) -> str:
    """Takes ABI definition and returns an event/method signature
    (i.e. Transfer(address,address,value))"""
    inputs = abi["inputs"]
    name = abi["name"]

    input_types_expanded = []

    def expand_signature_types(inputs):
        types = []
        for i in inputs:
            if i['type'].endswith('storage'):
                types.append('uint256')
                continue
            if i['type'] == 'tuple':
                if i.get('components', None) is not None:
                    types.append(expand_signature_types(i.get('components')))
                    continue
            types.append(i['type'])
        return f"({','.join(types)})"

    return f"{name}{expand_signature_types(inputs)}"


def to_signature_hash(abi: dict) -> str:
    """Takes ABI definition and computes the SHA-3 hash"""
    type = abi["type"]

    if type.lower() == 'event':
        return '0x'+str(event_abi_to_log_topic(abi).hex())
    return '0x'+str(function_abi_to_4byte_selector(abi).hex())


def _parse_event_for_data(event: dict) -> dict:
    logger.info(f"event: {event}")
    body = event["body"]

    try:
        body = json.loads(event["body"])
        return body["data"]
    except Exception as err:
        logger.error("error parsing data from body", exc_info=True)

        return {
            "statusCode": 400,
            "headers": HEADERS,
            "body": json.dumps({"data": str(err)})
        }


def to_eth_abi_types(abi):
    '''
    Docstring
    '''
    types_arr = []
    for o in abi:
        if o['type'].endswith('storage'):
            types_arr.append('uint256')
            continue
        if o['type'] == 'tuple':
            if o.get('components', None) is not None:
                internal_types_arr = to_eth_abi_types(o.get('components'))
                types_arr.append(f"({','.join(internal_types_arr)})")
            continue
        types_arr.append(o['type'])
    return types_arr


def decode_contract_event(abi: dict, topics: str, data: str) -> dict:
    """
        Takes ABI definition, topics, and data, and decodes into readable format.
        it will use the placement index if no name is given.


        example output of this method:
    {
        'name': 'Transfer',
        'signature': 'Transfer(address,address,uint256)',
        'signature_hash': '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef',
        'data': {
            'from': '0xe59d5b5eb2a4e02c033a46a18e47f399f7a1e14b',
            'to': '0x3349217670f9aa55c5640a2b3d806654d27d0569',
            'value': 241002558777421199592
            }
        }
    """
    result = {}
    topic_index = 1
    topics_arr = topics.split(',')
    data_types = []
    data_names = []
    result = {
        'name': abi['name'],
        'signature': to_signature(abi),
        'signature_hash': topics_arr[0],
        'data': {}
    }

    for idx, i in enumerate(abi['inputs']):
        name = i['name'] if i.get('name', '') != '' else str(idx)
        if i['indexed']:
            result['data'][name] = decode_abi(
                [i['type']], bytes.fromhex(topics_arr[topic_index][2:]))[0]
            topic_index += 1
            continue
        data_types.append(i['type'])
        data_names.append(name)
    data_values = decode_abi(data_types, bytes.fromhex(data[2:]))
    result['data'].update(
        {data_names[i]: v for i, v in enumerate(data_values)})
    return result


def decode_contract_function(abi: dict, input: str, output: str) -> dict:
    """
        Takes ABI definition, input, and output, and decodes into readable format.
        it will use the placement index if no name is given.
        outputs to functions may not be captured by the signature hash, therefore
        multiple decoded traces may have the same signature with different output structure.

        example output of this method:

        {
            'name': 'transfer',
            'signature': 'transfer(address,uint256)',
            'signature_hash': '0xa9059cbb',
            'inputs': {
                'recipient': '0x42e2e1afe6dc0701640601a6728a097a09efd44b',
                'amount': 242859825102880658436213
                },
            'outputs': {
                '0': True
                }
        }
    """

    # TODO: Handle internalType
    # TODO: Handle delegateCall

    def names(abi):
        return [o['name'] if o.get('name', '') != '' else str(
            idx) for idx, o in enumerate(abi)]

    decoded_input_values = decode_abi(
        to_eth_abi_types(abi['inputs']), bytes.fromhex(input[10:]))
    decoded_output_values = decode_abi(
        to_eth_abi_types(abi['outputs']), bytes.fromhex(output[2:]))

    input_names = names(abi['inputs'])
    output_names = names(abi['outputs'])
    result = {
        'name': abi['name'],
        'signature': to_signature(abi),
        'signature_hash': input[:10]
    }
    result['inputs'] = {input_names[i]: v for i,
                        v in enumerate(decoded_input_values)}
    result['outputs'] = {output_names[i]: v for i,
                         v in enumerate(decoded_output_values)}

    return result


if __name__ == '__main__':

    transfer_evt_sighash = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
    transfer_evt_topics = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef,0x000000000000000000000000e59d5b5eb2a4e02c033a46a18e47f399f7a1e14b,0x0000000000000000000000003349217670f9aa55c5640a2b3d806654d27d0569'
    transfer_evt_data = '0x00000000000000000000000000000000000000000000000d109516526063f8e8'
    transfer_evt_abi = '''{
        "anonymous": false,
        "inputs": [
            {
            "indexed": true,
            "internalType": "address",
            "name": "from",
            "type": "address"
            },
            {
            "indexed": true,
            "internalType": "address",
            "name": "to",
            "type": "address"
            },
            {
            "indexed": false,
            "internalType": "uint256",
            "name": "value",
            "type": "uint256"
            }
        ],
        "name": "Transfer",
        "type": "event"
        }'''

    #     transfer_fn_abi = '''{
    #   "constant": false,
    #   "inputs": [
    #     {
    #       "name": "self",
    #       "type": "BTTSLib.Data storage"
    #     },
    #     {
    #       "name": "to",
    #       "type": "address"
    #     },
    #     {
    #       "name": "tokens",
    #       "type": "uint256"
    #     }
    #   ],
    #   "name": "transfer",
    #   "outputs": [
    #     {
    #       "name": "success",
    #       "type": "bool"
    #     }
    #   ],
    #   "payable": false,
    #   "stateMutability": "nonpayable",
    #   "type": "function"
    # }'''
    #     transfer_fn_sighash = '0x06ad0e7b'
    #     transfer_fn_input_data = "0x06ad0e7b0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000dead000000000000000000000000000000000000000000000021152395c3376e2faa"
    #     transfer_fn_output_data = "0x0000000000000000000000000000000000000000000000000000000000000001"
    #     fn_out = decode_contract_function(
    #         json.loads(transfer_fn_abi),
    #         transfer_fn_input_data,
    #         transfer_fn_output_data)
    #     print(fn_out)

    #     transfer_fn_abi = '''{
    #   "constant": false,
    #   "inputs": [
    #     {
    #       "name": "self",
    #       "type": "SortedDoublyLL.Data storage"
    #     },
    #     {
    #       "name": "_id",
    #       "type": "address"
    #     },
    #     {
    #       "name": "_newKey",
    #       "type": "uint256"
    #     },
    #     {
    #       "name": "_prevId",
    #       "type": "address"
    #     },
    #     {
    #       "name": "_nextId",
    #       "type": "address"
    #     }
    #   ],
    #   "name": "updateKey",
    #   "outputs": [],
    #   "payable": false,
    #   "stateMutability": "nonpayable",
    #   "type": "function"
    # }'''
    #     transfer_fn_sighash = '0x38237efe'
    #     transfer_fn_input_data = "0x38237efe000000000000000000000000000000000000000000000000000000000000001000000000000000000000000010b21af759129f32c6064adfb85d3ea2a8c0209c000000000000000000000000000000000000000000001c0bdb4574e70c19a18e0000000000000000000000004712e01e944802613de3a0a6d23274e7e0243015000000000000000000000000e9e284277648fcdb09b8efc1832c73c09b5ecf59"
    #     transfer_fn_output_data = "0x"
    #     fn_out = decode_contract_function(
    #         json.loads(transfer_fn_abi),
    #         transfer_fn_input_data,
    #         transfer_fn_output_data)
    #     print(fn_out)

    #     transfer_fn_abi = '''{   "constant": false,   "inputs": [     {       "name": "_path",       "type": "address[]"     },     {       "name": "_amount",       "type": "uint256"     },     {       "name": "_minReturn",       "type": "uint256"     },     {       "name": "_beneficiary",       "type": "address"     },     {       "name": "_affiliateAccount",       "type": "address"     },     {       "name": "_affiliateFee",       "type": "uint256"     }   ],   "name": "convertByPath",   "outputs": [     {       "name": "",       "type": "uint256"     }   ],   "payable": true,   "stateMutability": "payable",   "type": "function" }'''
    #     transfer_fn_sighash = '0x38237efe'
    #     transfer_fn_input_data = "0xb77d239b00000000000000000000000000000000000000000000000000000000000000c000000000000000000000000000000000000000000000065a4da25d3016c0000000000000000000000000000000000000000000000000000000000002ca269b9d00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000050000000000000000000000004691937a7508860f876c9c0a2a617e7d9e945d4b00000000000000000000000030c6fe4d0526c5c6707d7e2ebbd4ffbbdce1728c0000000000000000000000001f573d6fb3f13d689ff844b4ce37794d79a7ff1c0000000000000000000000005365b5bc56493f08a38e5eb08e36cbbe6fcc8306000000000000000000000000dac17f958d2ee523a2206206994597c13d831ec7"
    #     transfer_fn_output_data = "0x00000000000000000000000000000000000000000000000000000002cdbd507f"
    #     fn_out = decode_contract_function(
    #         json.loads(transfer_fn_abi),
    #         transfer_fn_input_data,
    #         transfer_fn_output_data)
    #     print(fn_out)

    transfer_fn_abi = '''{"inputs":[
        {
            "components":[
                {"internalType":"address","name":"tokenIn","type":"address"},
                {"internalType":"address","name":"tokenOut","type":"address"},
                {"internalType":"uint24","name":"fee","type":"uint24"},
                {"internalType":"address","name":"recipient","type":"address"},
                {"internalType":"uint256","name":"deadline","type":"uint256"},
                {"internalType":"uint256","name":"amountIn","type":"uint256"},
                {"internalType":"uint256","name":"amountOutMinimum","type":"uint256"},
                {"internalType":"uint160","name":"sqrtPriceLimitX96","type":"uint160"}
                ],
                "internalType":"struct ISwapRouter.ExactInputSingleParams",
                "name":"params",
                "type":"tuple"}
            ],
            "name":"exactInputSingle","outputs":[
                {"internalType":"uint256","name":"amountOut","type":"uint256"}],"stateMutability":"payable","type":"function"}'''
    transfer_fn_sighash = '0x38237efe'
    transfer_fn_input_data = "0x414bf3890000000000000000000000005a98fcbea516cf06857215779fd812ca3bef1b32000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc20000000000000000000000000000000000000000000000000000000000002710000000000000000000000000a3b83d0e2f3d2c675439188ef1aa13d1c6abca160000000000000000000000000000000000000000000000000000000062d9c1b500000000000000000000000000000000000000000000014dde846addf8321a08000000000000000000000000000000000000000000000000567ea384ed9d353b0000000000000000000000000000000000000000082dbdc9e357ad2ceef10783"
    transfer_fn_output_data = "0x00000000000000000000000000000000000000000000000000000002cdbd507f"
    # fn_out = decode_contract_function(
    #     json.loads(transfer_fn_abi),
    #     transfer_fn_input_data,
    #     transfer_fn_output_data)
    # print(fn_out)

    print(to_signature(json.loads(transfer_fn_abi)))
    print("0x414bf389", to_signature_hash(json.loads(transfer_fn_abi)))
    print(to_signature(json.loads(transfer_evt_abi)))
    print("0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
          to_signature_hash(json.loads(transfer_evt_abi)))
    # evt_out = decode_contract_event(
    #     json.loads(transfer_evt_abi),
    #     transfer_evt_topics,
    #     transfer_evt_data
    # )
    # print(evt_out)
