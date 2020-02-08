import json
from enum import Enum
from functools import partial
import attr
from .dummy import Dummy, Ref, InputSpec, Freshness


ENCODING = '@encoding'
ENCODING_ATTR = 'attr'
ENCODING_ENUM = 'enum'
ATTR_NAME = '@class'
ATTR_VALUE = '@value'


CLASSES = (Dummy, Ref, InputSpec, Freshness)


def encoder(obj):
    if attr.has(obj.__class__):
        return {
            ENCODING: ENCODING_ATTR,
            ATTR_NAME: obj.__class__.__name__,
            **attr.asdict(obj, recurse=False),
        }
    if isinstance(obj, Enum):
        return {
            ENCODING: ENCODING_ENUM,
            ATTR_NAME: obj.__class__.__name__,
            ATTR_VALUE: obj.name,
        }
    raise TypeError('Object with unsupported type', obj)


dump = partial(json.dump, default=encoder, sort_keys=True, indent=4)
dumps = partial(json.dumps, default=encoder, sort_keys=True, indent=4)


def reconstruct(json_dict, type_by_name):
    encoding = json_dict.get(ENCODING)
    construct = {
        ENCODING_ATTR: attr_load,
        ENCODING_ENUM: enum_load,
        None: dict_load,
    }[encoding]
    return construct(json_dict, type_by_name)


def attr_load(json_dict, type_by_name):
    cls = type_by_name[json_dict[ATTR_NAME]]
    attrs = {
        key: value
        for key, value in json_dict.items()
        if key not in {ATTR_NAME, ENCODING}
    }
    return cls(**attrs)


def enum_load(json_dict, type_by_name):
    cls = type_by_name[json_dict[ATTR_NAME]]
    return cls[json_dict[ATTR_VALUE]]


def dict_load(json_dict, _type_by_name):
    return json_dict


def reader(json_stream, types, json_loader):
    type_by_name = {t.__name__: t for t in types}
    return json_loader(json_stream, object_hook=partial(reconstruct, type_by_name=type_by_name))


load = partial(reader, json_loader=json.load, types=CLASSES)
loads = partial(reader, json_loader=json.loads, types=CLASSES)


def write_beads(file_name, beads):
    with open(file_name, 'w') as f:
        dump(beads, f)


def read_beads(file_name):
    with open(file_name) as f:
        return load(f)
