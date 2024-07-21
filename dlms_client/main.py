import traceback
import time

from gurux_serial import GXSerial
from gurux_dlms.enums import ObjectType
from gurux_dlms import GXDLMSException, GXDLMSExceptionResponse, GXDLMSConfirmedServiceError

from gurux_common.enums import TraceLevel

from settings import Settings
from reader import Reader

try:
  import pkg_resources
except Exception:
  print("pkg_resources not found!")

class Client():
  @classmethod
  def main(cls):
    try:
      print("Gurux.DLMS.version: " + pkg_resources.get_distribution("gurux_dlms").version)
      print("Gurux.Serial version: " + pkg_resources.get_distribution("gurux_serial").version)
    except Exception:
      print("pkg_resources not found!")

    reader: Reader = None
    settings: Settings = Settings()

    try:
      ret = settings.setClient()

      if ret != 0:
        return
      
      if not isinstance(settings.media, GXSerial):
        raise Exception("Unknown media type!")
      
      reader = Reader(
        settings.client, 
        settings.media, 
        settings.trace, 
        settings.invocationCounter)
      
      settings.media.open()

      time.sleep(0.5)
      
      reader.initializeConnection()
      reader.getAssociationView()

      obisCode = "1.1.21.25.0.255"
      attributeIndex = 3

      settings.selectObject(obisCode, attributeIndex)

      if settings.readObjects:
        selectedObject = settings.client.objects.findByLN(
          ObjectType.REGISTER, 
          obisCode)
        
        reader.writeTrace("Object Type: " + str(selectedObject.objectType), TraceLevel.INFO)
        reader.writeTrace("Object Name: " + selectedObject.name, TraceLevel.INFO)
        reader.writeTrace("Object Description: " + selectedObject.description, TraceLevel.INFO)

        if selectedObject is None:
          raise Exception("Unknown logical name: " + obisCode)
        
        receivedValue = reader.read(selectedObject, attributeIndex)
        reader.showValue(attributeIndex, receivedValue)

    except (ValueError, GXDLMSException, GXDLMSExceptionResponse, GXDLMSConfirmedServiceError) as ex:
      print(ex)
    except (KeyboardInterrupt, SystemExit, Exception) as ex:
      traceback.print_exc()
      if settings.media:
        settings.media.close()
      reader = None
    finally:
      if reader:
        try:
          reader.close()
        except Exception:
          traceback.print_exc()
      
      print("Ended!")

if __name__ == '__main__':
  Client.main()
        

