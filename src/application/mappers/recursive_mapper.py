import numpy as np
from dataclasses import is_dataclass, asdict, fields


def to_dict_recursive(obj):
    """
    dataclass → dict に再帰的に変換する。
    ndarray は list に変換する。
    """
    # dataclass の場合は asdict() で展開し、再帰処理
    if is_dataclass(obj):
        result = {}
        for key, value in asdict(obj).items():
            result[key] = to_dict_recursive(value)
        return result

    # ndarray → list
    if isinstance(obj, np.ndarray):
        return obj.tolist()

    # list の場合は要素ごとに再帰
    if isinstance(obj, list):
        return [to_dict_recursive(v) for v in obj]

    # dict の場合も再帰
    if isinstance(obj, dict):
        return {k: to_dict_recursive(v) for k, v in obj.items()}

    # プリミティブ型はそのまま返す
    return obj


def from_dict_recursive(cls, data):
    """
    dict → dataclass に再帰的に復元する。
    ndarray は list → ndarray に変換する。
    """
    # dataclass でない場合はそのまま返す
    if not is_dataclass(cls):
        return data

    kwargs = {}
    for f in fields(cls):
        value = data.get(f.name)

        # ndarray の復元
        if f.type is np.ndarray:
            kwargs[f.name] = np.array(value)
            continue

        # ネストした dataclass の復元
        if is_dataclass(f.type):
            kwargs[f.name] = from_dict_recursive(f.type, value)
            continue

        # プリミティブ型
        kwargs[f.name] = value

    return cls(**kwargs)
