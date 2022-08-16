import json
import handlers

to_signature = handlers.to_signature
to_signature_hash = handlers.to_signature_hash
decode_contract_event = handlers.decode_contract_event
decode_contract_function = handlers.decode_contract_function

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

    transfer_fn_abi = '''{
    "constant": false,
    "inputs": [
    {
        "name": "self",
        "type": "BTTSLib.Data storage"
    },
    {
        "name": "to",
        "type": "address"
    },
    {
        "name": "tokens",
        "type": "uint256"
    }
    ],
    "name": "transfer",
    "outputs": [
    {
        "name": "success",
        "type": "bool"
    }
    ],
    "payable": false,
    "stateMutability": "nonpayable",
    "type": "function"
}'''
    transfer_fn_sighash = '0x06ad0e7b'
    transfer_fn_input_data = "0x06ad0e7b0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000dead000000000000000000000000000000000000000000000021152395c3376e2faa"
    transfer_fn_output_data = "0x0000000000000000000000000000000000000000000000000000000000000001"
    fn_out = decode_contract_function(
        json.loads(transfer_fn_abi),
        transfer_fn_input_data,
        transfer_fn_output_data)
    print(fn_out)

    transfer_fn_abi = '''{
    "constant": false,
    "inputs": [
    {
        "name": "self",
        "type": "SortedDoublyLL.Data storage"
    },
    {
        "name": "_id",
        "type": "address"
    },
    {
        "name": "_newKey",
        "type": "uint256"
    },
    {
        "name": "_prevId",
        "type": "address"
    },
    {
        "name": "_nextId",
        "type": "address"
    }
    ],
    "name": "updateKey",
    "outputs": [],
    "payable": false,
    "stateMutability": "nonpayable",
    "type": "function"
}'''
    transfer_fn_sighash = '0x38237efe'
    transfer_fn_input_data = "0x38237efe000000000000000000000000000000000000000000000000000000000000001000000000000000000000000010b21af759129f32c6064adfb85d3ea2a8c0209c000000000000000000000000000000000000000000001c0bdb4574e70c19a18e0000000000000000000000004712e01e944802613de3a0a6d23274e7e0243015000000000000000000000000e9e284277648fcdb09b8efc1832c73c09b5ecf59"
    transfer_fn_output_data = "0x"
    fn_out = decode_contract_function(
        json.loads(transfer_fn_abi),
        transfer_fn_input_data,
        transfer_fn_output_data)
    print(fn_out)
    print(to_signature(json.loads(transfer_fn_abi)))
    print()
    print(transfer_fn_input_data[:10], to_signature_hash(
        json.loads(transfer_fn_abi)))
    print()

    transfer_fn_abi = '''{   "constant": false,   "inputs": [     {       "name": "_path",       "type": "address[]"     },     {       "name": "_amount",       "type": "uint256"     },     {       "name": "_minReturn",       "type": "uint256"     },     {       "name": "_beneficiary",       "type": "address"     },     {       "name": "_affiliateAccount",       "type": "address"     },     {       "name": "_affiliateFee",       "type": "uint256"     }   ],   "name": "convertByPath",   "outputs": [     {       "name": "",       "type": "uint256"     }   ],   "payable": true,   "stateMutability": "payable",   "type": "function" }'''
    transfer_fn_sighash = '0x38237efe'
    transfer_fn_input_data = "0xb77d239b00000000000000000000000000000000000000000000000000000000000000c000000000000000000000000000000000000000000000065a4da25d3016c0000000000000000000000000000000000000000000000000000000000002ca269b9d00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000050000000000000000000000004691937a7508860f876c9c0a2a617e7d9e945d4b00000000000000000000000030c6fe4d0526c5c6707d7e2ebbd4ffbbdce1728c0000000000000000000000001f573d6fb3f13d689ff844b4ce37794d79a7ff1c0000000000000000000000005365b5bc56493f08a38e5eb08e36cbbe6fcc8306000000000000000000000000dac17f958d2ee523a2206206994597c13d831ec7"
    transfer_fn_output_data = "0x00000000000000000000000000000000000000000000000000000002cdbd507f"
    fn_out = decode_contract_function(
        json.loads(transfer_fn_abi),
        transfer_fn_input_data,
        transfer_fn_output_data)
    print(fn_out)

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
    fn_out = decode_contract_function(
        json.loads(transfer_fn_abi),
        transfer_fn_input_data,
        transfer_fn_output_data)
    print(fn_out)

    print(to_signature(json.loads(transfer_fn_abi)))
    print("0x414bf389", to_signature_hash(json.loads(transfer_fn_abi)))
    print(to_signature(json.loads(transfer_evt_abi)))
    print("0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
          to_signature_hash(json.loads(transfer_evt_abi)))
    evt_out = decode_contract_event(
        json.loads(transfer_evt_abi),
        transfer_evt_topics,
        transfer_evt_data
    )
    print(evt_out)
