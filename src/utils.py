from typing import List


def recursive_flatten_abi_types(abi_fragment: dict, prefix: str, indexed: bool, array_dims: str = None):
    """
    docstring
    """
    def to_name(n, p):
        return p + '.' + n if p else n

    def to_type(t, a):
        return t + a if a else t

    type_arr = []
    name_arr = []
    for inp in abi_fragment:

        if indexed != inp.get('indexed', False):
            continue

        typ = inp["type"]
        name = inp["name"]

        if not isinstance(typ, str):
            continue
        elif typ.endswith("storage"):
            type_arr.append('uint256')
            name_arr.append(to_name(name, prefix))
            continue
        elif not typ.startswith("tuple"):
            type_arr.append(to_type(typ, array_dims))
            name_arr.append(to_name(name, prefix))
            continue
        (tup_types, tup_names) = recursive_flatten_abi_types(
            inp['components'], to_name(name, prefix), False, typ[5:])
        type_arr.extend(tup_types)
        name_arr.extend(tup_names)
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
