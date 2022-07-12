import json
import logging

from web3 import Web3

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


def to_signature(abi: dict) -> str:
    """Takes ABI definition and returns an event/method signature
    (i.e. Transfer(address,address,value))"""
    inputs = abi["inputs"]
    name = abi["name"]

    if len(inputs) > 0:
        types = [i["type"] for i in inputs]
        return f"{name}({','.join(types)})"

    return f"{name}()"


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