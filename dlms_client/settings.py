from gurux_dlms.enums import InterfaceType, Authentication, Security, Standard, Conformance
from gurux_dlms.secure import GXDLMSSecureClient
from gurux_dlms.GXByteBuffer import GXByteBuffer

from gurux_common.enums import TraceLevel
from gurux_common.io import Parity, StopBits, BaudRate

from gurux_serial.GXSerial import GXSerial

class Settings:
  def __init__(self):
    self.media = None
    self.trace: TraceLevel = TraceLevel.INFO
    self.invocationCounter = None
    self.client: GXDLMSSecureClient = GXDLMSSecureClient(True)
    self.readObjects = []
    self.outputFile = None

  def setClient(self):
    # Media setup (This case, serial communication)
    self.media = GXSerial(None)
    self.media.port = 'COM5'
    self.media.baudRate = BaudRate.BAUD_RATE_9600
    self.media.dataBits = 8
    self.media.parity = Parity.NONE
    self.media.stopBits = StopBits.ONE

    # Client setup
    self.client.clientAddress = 17
    self.client.interfaceType = InterfaceType.HDLC
    self.client.useLogicalNameReferencing = True
    self.client.authentication = Authentication.LOW
    self.client.ciphering.authenticationKey = GXByteBuffer.hexToBytes("D0D1D2D3D4D5D6D7D8D9DADBDCDDDEDF")
    self.client.password = "Gurux"
    self.client.standard = Standard.DLMS
    self.client.negotiatedConformance = Conformance.GET | Conformance.SELECTIVE_ACCESS

    # etc
    self.trace = TraceLevel.INFO

    if not self.media:
      return 1
    return 0

  def selectObject(self, obis: str, attribute: int):
    self.readObjects.append((obis.strip(), attribute))
