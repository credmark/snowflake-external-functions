import json
import logging

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
        print(inputs)
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
    sig = to_signature(abi)
    hash = Web3.sha3(text=sig).hex()

    # Return full hash for event and 0x + first 4 bytes for methods
    if type.lower() == 'event':
        return hash
    return hash[:10]


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
