```python
def read(self, item, attributeIndex):
  data = self.client.read(item, attributeIndex)[0]
  reply = GXReplyData()

  self.readDataBlock(data, reply)

  # ...

  return self.client.updateValue(item, attributeIndex, reply.value)
```

```python
# GXDLMSClient.py

def read(self, item, attributeOrdinal):
  return self._read(item.name, item.objectType, attributeOrdinal)
```

```python
# GXDLMSClient.py

def _read(self, name, objectType, attributeOrdinal, data=None):
  attributeDescriptor = GXByteBuffer()
  reply = None
  self.settings.resetBlockIndex()

  # if use LN Referencing
  attributeDescriptor.setUInt16(int(objectType))
  attributeDescriptor.set(_GXCommon.logicalNameToBytes(str(name)))
  attribute.setUInt8(attributeOrdinal)

  if not data:
    attributeDescriptor.setUInt8(0)
  else:
    attributeDescriptor.setUInt8(1)
  
  p = GXDLMSLNParameters(
    self.settings,          # settings
    0,                      # invoke id
    Command.GET_REQUEST,    # Command
    GetCommandType.NORMAL,  # Get Command Type
    attributeDescriptor,    # ByteBuffer
    data,                   # data
    0xFF,                   # status
  )

  reply = GXDLMS.getLnMessages(p)
```



```python

obisCode = "1.1.21.25.0.255"
attributeIndex = 3

settings.selectObject(obisCode, attributeIndex)

if settings.readObjects:
  selectedObject = settings.client.objects.findByLN(
    ObjectType.REGISTER,
    obisCode)
  
  if selectedObject is None:
    # exception handle
  
  receivedValue = reader.read(selectedObject, attributeIndex)
  
  # ...

```


```python

def getInitiateRequest(cls, settings, data):
  data.setUInt8(Command.INITIATE_REQUEST)   # 0x01
  data.setUInt8(0x00)                       # dedicated-key not used
  data.setUInt8(0x00)
  data.setUInt8(0x00)                       # quality of service = 0
  data.setUInt8(settings.dlmsVersion) 

  # Tag for Conformance Block
  data.setUInt8(0x5F)
  data.setUInt8(0x1F)

  # Length of the Conformance Block
  data.setUInt8(0x04)

  # Encoding the number of unused bits in the bit string
  data.setUInt8(0x00)

  cls.setConformanceToArray(settings.proposedConformance, data)

  data.setUInt16(settings.maxPduSize)

```