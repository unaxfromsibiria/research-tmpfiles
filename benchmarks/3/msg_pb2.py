# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: msg.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
from google.protobuf import descriptor_pb2
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='msg.proto',
  package='messages',
  serialized_pb=_b('\n\tmsg.proto\x12\x08messages\"\'\n\x07\x44\x61taMsg\x12\r\n\x01\x61\x18\x01 \x03(\x02\x42\x02\x10\x01\x12\r\n\x01\x62\x18\x02 \x03(\x02\x42\x02\x10\x01\"-\n\nDataAnswer\x12\t\n\x01\x61\x18\x01 \x02(\x02\x12\t\n\x01\x62\x18\x02 \x02(\x02\x12\t\n\x01\x63\x18\x03 \x02(\x02')
)
_sym_db.RegisterFileDescriptor(DESCRIPTOR)




_DATAMSG = _descriptor.Descriptor(
  name='DataMsg',
  full_name='messages.DataMsg',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='a', full_name='messages.DataMsg.a', index=0,
      number=1, type=2, cpp_type=6, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=_descriptor._ParseOptions(descriptor_pb2.FieldOptions(), _b('\020\001'))),
    _descriptor.FieldDescriptor(
      name='b', full_name='messages.DataMsg.b', index=1,
      number=2, type=2, cpp_type=6, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=_descriptor._ParseOptions(descriptor_pb2.FieldOptions(), _b('\020\001'))),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=23,
  serialized_end=62,
)


_DATAANSWER = _descriptor.Descriptor(
  name='DataAnswer',
  full_name='messages.DataAnswer',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='a', full_name='messages.DataAnswer.a', index=0,
      number=1, type=2, cpp_type=6, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='b', full_name='messages.DataAnswer.b', index=1,
      number=2, type=2, cpp_type=6, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='c', full_name='messages.DataAnswer.c', index=2,
      number=3, type=2, cpp_type=6, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=64,
  serialized_end=109,
)

DESCRIPTOR.message_types_by_name['DataMsg'] = _DATAMSG
DESCRIPTOR.message_types_by_name['DataAnswer'] = _DATAANSWER

DataMsg = _reflection.GeneratedProtocolMessageType('DataMsg', (_message.Message,), dict(
  DESCRIPTOR = _DATAMSG,
  __module__ = 'msg_pb2'
  # @@protoc_insertion_point(class_scope:messages.DataMsg)
  ))
_sym_db.RegisterMessage(DataMsg)

DataAnswer = _reflection.GeneratedProtocolMessageType('DataAnswer', (_message.Message,), dict(
  DESCRIPTOR = _DATAANSWER,
  __module__ = 'msg_pb2'
  # @@protoc_insertion_point(class_scope:messages.DataAnswer)
  ))
_sym_db.RegisterMessage(DataAnswer)


_DATAMSG.fields_by_name['a'].has_options = True
_DATAMSG.fields_by_name['a']._options = _descriptor._ParseOptions(descriptor_pb2.FieldOptions(), _b('\020\001'))
_DATAMSG.fields_by_name['b'].has_options = True
_DATAMSG.fields_by_name['b']._options = _descriptor._ParseOptions(descriptor_pb2.FieldOptions(), _b('\020\001'))
# @@protoc_insertion_point(module_scope)
