import json
import logging
import traceback
from typing import List

from eth_abi import decode_abi
from eth_abi.exceptions import InsufficientDataBytes
from eth_utils.abi import (_abi_to_signature, event_abi_to_log_topic,
                           function_abi_to_4byte_selector)


logger = logging.getLogger()
logger.setLevel(logging.INFO)

HEADERS = {"Content-Type": "application/json"}


def to_signature_handler(event: dict, context: dict) -> dict:
    """Takes in Snowflake data and calculates an event/method signature"""

    try:
        event_data = _parse_event_for_data(event)
        logger.info(f"event data: {event_data}")

        for row in event_data:
            row[1] = to_signature(row[1])

        return {
            "statusCode": 200,
            "headers": HEADERS,
            "body": json.dumps({"data": event_data})
        }

    except Exception as e:
        logger.error(e, exc_info=True)
        return {
            "statusCode": 500,
            "headers": HEADERS,
            "body": json.dumps(format_exception(e, event_data))
        }


def to_signature_hash_handler(event: dict, context: dict) -> dict:
    """Takes in Snowflake data and calculates an event/method signature hash"""

    try:
        event_data = _parse_event_for_data(event)
        logger.info(f"event data: {event_data}")

        for row in event_data:
            row[1] = to_signature_hash(row[1])

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"data": event_data})
        }

    except Exception as e:
        logger.error(e, exc_info=True)
        return {
            "statusCode": 500,
            "headers": HEADERS,
            "body": json.dumps(format_exception(e, event_data))
        }


def decode_contract_event_handler(event: dict, context: dict) -> dict:
    """Takes in Snowflake data and decodes contract events"""

    event_data = _parse_event_for_data(event)
    logger.info(f"event data: {event_data}")
    for row in event_data:
        try:
            row[1] = decode_contract_event(row[1], row[2], row[3])
        except Exception as e:
            logger.error(e, exc_info=True)
            row[1] = {
                "error": "could not decode row",
                "abi": row[1],
                "topics": row[2],
                "data": row[3]}
        row.pop(3)
        row.pop(2)

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"data": event_data}, default=_default)
    }


def decode_contract_function_handler(event: dict, context: dict) -> dict:
    """Takes in Snowflake data and decodes contract functions"""

    event_data = _parse_event_for_data(event)
    logger.info(f"event data: {event_data}")

    for row in event_data:
        try:
            row[1] = decode_contract_function(row[1], row[2], row[3])
        except Exception as e:
            logger.error(e, exc_info=True)
            row[1] = {
                "error": "could not decode row",
                "abi": row[1],
                "input": row[2],
                "output": row[3]}
        row.pop(3)
        row.pop(2)

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"data": event_data}, default=_default)
    }


def to_signature(abi: dict) -> str:
    """Takes ABI definition and returns an event/method signature
    (i.e. Transfer(address,address,value))"""

    return _abi_to_signature(abi)


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
    decoded_successfully = True
    topics_data = "".join(t[2:] for t in topics.split(',')[1:])

    decoded_types_and_names = to_decodable_types(abi)
    try:
        decoded_input_values = decode_abi(
            decoded_types_and_names['inputs']['types'], bytes.fromhex(data[2:]))

        decoded_indexed_values = decode_abi(
            decoded_types_and_names['indexed']['types'], bytes.fromhex(topics_data))

        evt_data = {decoded_types_and_names['inputs']['names']
                    [i]: v for i, v in enumerate(decoded_input_values)}

        for i, v in enumerate(decoded_indexed_values):
            evt_data[decoded_types_and_names['indexed']['names'][i]] = v

    except InsufficientDataBytes as e:
        logger.error("exception", exc_info=True)
        logger.error(json.dumps({"abi": abi, "topics": topics, "data": data}))
        decoded_successfully = False
        evt_data = {"exception": str(e)}

    return {
        'name': abi['name'],
        'signature': to_signature(abi),
        'signature_hash': topics.split(',')[0],
        'data': evt_data,
        'decoded_successfully': decoded_successfully,
    }


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

    decoded_types_and_names = to_decodable_types(abi)
    decoded_input_values = []
    if input is not None:
        decoded_input_values = decode_abi(
            decoded_types_and_names['inputs']['types'], bytes.fromhex(input[10:]))
    decoded_output_values = []
    if output is not None:
        decoded_output_values = decode_abi(
            decoded_types_and_names['outputs']['types'], bytes.fromhex(output[2:]))

    return {
        'name': abi['name'],
        'signature': to_signature(abi),
        'signature_hash': input[:10],
        'inputs': {decoded_types_and_names['inputs']['names'][i]: v for i,
                   v in enumerate(decoded_input_values)},
        'outputs': {decoded_types_and_names['outputs']['names'][i]: v for i,
                    v in enumerate(decoded_output_values)}
    }


def recursive_flatten_abi_types(abi_fragment: dict, prefix: str, indexed: bool, array_dims: str = None):
    """
    docstring
    """
    def to_name(n, p, i=0):
        if n == "":
            return p + '.' + "_"+str(i) if p else "_"+str(i)
        return p + '.' + n if p else n

    def to_type(t, a):
        return t + a if a else t

    type_arr = []
    name_arr = []
    idx = 0
    for inp in abi_fragment:

        if indexed != inp.get('indexed', False):
            continue

        typ = inp["type"]
        name = inp["name"]

        if not isinstance(typ, str):
            continue
        elif typ.endswith("storage"):
            type_arr.append('uint256')
            name_arr.append(to_name(name, prefix, idx))
            continue
        elif not typ.startswith("tuple"):
            type_arr.append(to_type(typ, array_dims))
            name_arr.append(to_name(name, prefix, idx))
            continue
        (tup_types, tup_names) = recursive_flatten_abi_types(
            inp['components'], to_name(name, prefix, idx), False, typ[5:])
        type_arr.extend(tup_types)
        name_arr.extend(tup_names)
        idx = idx+1
    return (type_arr, name_arr)


def to_decodable_types(abi: dict) -> List[str]:
    '''
    Docstring
    '''
    i_t, i_n = recursive_flatten_abi_types(abi.get('inputs', []), '', False)
    i_i_t, i_i_n = recursive_flatten_abi_types(abi.get('inputs', []), '', True)
    o_t, o_n = recursive_flatten_abi_types(abi.get('outputs', []), '', False)
    flattened_types = {
        "inputs": {
            "names": i_n,
            "types": i_t
        },
        "indexed": {
            "names": i_i_n,
            "types": i_i_t
        },
        "outputs": {
            "names": o_n,
            "types": o_t
        },
    }
    return flattened_types


def _default(obj):
    if isinstance(obj, bytes):

        try:
            return '0x' + str(obj.hex())
        except UnicodeDecodeError:
            # TODO: Maybe find a better way to handle certain bytes data
            # rather than ignore and strip out the invalid byte characters

            return str(obj, errors='ignore')

    raise TypeError(f"type {type(obj)} is not JSON serializable. obj: {obj}")


def format_exception(exc: Exception, event: dict):
    return {
        "exception": str(exc),
        "stackTrace": traceback.format_exc(),
        "event": event
    }


if __name__ == "__main__":
    import sys
    from pprint import pprint

    filename = sys.argv[1]
    print(f"loading event {filename}")

    with open(filename) as fp:
        event = json.load(fp)

    response = decode_contract_event_handler(event, {})
    pprint(response, indent=2)
