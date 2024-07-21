import datetime
import traceback

from gurux_common.enums import TraceLevel
from gurux_common.io import Parity, StopBits
from gurux_common import ReceiveParameters, TimeoutException

from gurux_dlms import GXByteBuffer, GXReplyData, GXDLMSException, GXDLMSAccessItem
from gurux_dlms.enums import ObjectType, Conformance, DataType, AccessServiceCommandType
from gurux_dlms.objects import GXDLMSObject, GXDLMSRegister, GXDLMSProfileGeneric, GXDLMSExtendedRegister

class Reader:
  def __init__(self, client, media, trace, invocationCounter):
    self.replyBuffer = bytearray(8 + 1024)
    self.waitTime = 5000
    self.logFile = open("log_file.txt", "w")
    self.trace = trace
    self.media = media
    self.invocationCounter = invocationCounter
    self.client = client

  def disconnect(self):
    if self.media and self.media.isOpen():
      print("Disconnect Request")
      reply = GXReplyData()
      self.readDLMSPacket(self.client.disconnectRequest(), reply)
  
  def close(self):
    if self.media and self.media.isOpen():
      print("Close Request")
      reply = GXReplyData()
      reply.clear()
      self.readDLMSPacket(self.client.disconnectRequest(), reply)
      self.media.close()
  
  def readDLMSPacket(self, data, reply=None):
    if not reply:
      reply = GXReplyData()
    
    if isinstance(data, bytearray):
      self.readDLMSPacket2(data, reply)
    elif data:
      for it in data:
        reply.clear()
        self.readDLMSPacket2(it, reply)

  def readDLMSPacket2(self, data, reply):
    if not data:
      return
    
    reply.error = 0
    eop = 0x7E

    p = ReceiveParameters()
    p.eop = eop
    p.allData = True
    p.waitTime = self.waitTime
    p.count = 5
    
    self.media.eop = eop
    rd = GXByteBuffer()

    with self.media.getSynchronous():
      # if not reply.isStreaming():
      self.writeTrace("TX: " + self.now() + "\t" + GXByteBuffer.hex(data), TraceLevel.VERBOSE)
      self.media.send(data)

      pos = 0

      try:
        while not self.client.getData(rd, reply):
          if not p.eop:
            p.count = self.client.getFrameSize(rd)

          # Checking timeout
          while not self.media.receive(p):
            pos += 1
            if pos == 3:
              raise TimeoutException("Failed to receive reply from the device in given time.")
            print("Data send failed. Try to resend " + str(pos) + "/3")
            self.media.send(data, None)
          
          rd.set(p.reply)
          p.reply = None

      except Exception as e:
        self.writeTrace("RX: " + self.now() + "\t" + str(rd), TraceLevel.ERROR)
        raise e
      
      self.writeTrace("RX: " + self.now() + "\t" + str(rd), TraceLevel.VERBOSE)

      if reply.error != 0:
        raise GXDLMSException(reply.error)
      
  def readDataBlock(self, data, reply):
    if data:
      if isinstance(data, list):
        for it in data:
          reply.clear()
          self.readDataBlock(it, reply)
        return reply.error == 0
      else:
        self.readDLMSPacket(data, reply)
        while reply.isMoreData():
          data = self.client.receiverReady(reply)
          self.readDLMSPacket(data, reply)

  def initializeConnection(self):
    print(str(self.client.standard))

    reply = GXReplyData()

    data = self.client.snrmRequest()    # For open connection

    if data:
      self.readDLMSPacket(data, reply)
      self.client.parseUAResponse(reply.data)
      size = self.client.hdlcSettings.maxInfoTX + 40
      self.replyBuffer = bytearray(size)

    reply.clear()

    self.readDataBlock(self.client.aarqRequest(), reply)  ## AA 
    self.client.parseAareResponse(reply.data)

    reply.clear()

  def read(self, item, attributeIndex):
    data = self.client.read(item, attributeIndex)[0]
    reply = GXReplyData()
    
    self.readDataBlock(data, reply)

    if item.getDataType(attributeIndex) == DataType.NONE:
      item.setDataType(attributeIndex, reply.valueType)
    
    return self.client.updateValue(item, attributeIndex, reply.value)
  
  def write(self, item, attributeIndex):
    data = self.client.write(item, attributeIndex)
    self.readDLMSPacket(data)

  def readRowsByEntry(self, pg, index, count):
    data = self.client.readRowsByEntry(pg, index, count)
    reply = GXReplyData()
    self.readDataBlock(data, reply)

    return self.client.updateValue(pg, 2, reply.value)
  
  def readRowsByRange(self, pg, start, end):
    reply = GXReplyData()
    data = self.client.readRowsByRange(pg, start, end)
    self.readDataBlock(data, reply)

    return self.client.updateValue(pg, 2, reply.value)

  def readByAccess(self, list_):
    if list_:
      reply = GXReplyData()
      data = self.client.accessRequest(None, list_)
      self.readDataBlock(data, reply)
      self.client.parseAccessResponse(list_, reply.data)
  
  def showValue(self, pos, val):
    if isinstance(val, (bytes, bytearray)):
      val = GXByteBuffer(val)
    elif isinstance(val, list):
      str_ = ""
      for tmp in val:
        if str_:
          str_ += ", "
        if isinstance(tmp, bytes):
          str_ += GXByteBuffer.hex(tmp)
        else:
          str_ += str(tmp)
      
      val = str_

    self.writeTrace("Index: " + str(pos) + " Value: " + str(val), TraceLevel.INFO)
  
  def getAssociationView(self):
    reply = GXReplyData()

    self.readDataBlock(self.client.getObjectsRequest(), reply)
    self.client.parseObjects(reply.data, True, False)

  @classmethod
  def now(cls):
    return datetime.datetime.now().strftime("%H:%M:%S")
  
  def writeTrace(self, line, level):
    if self.trace >= level:
      print(line)
    self.logFile.write(line + "\n")