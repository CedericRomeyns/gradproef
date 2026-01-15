
from typing import Dict
from io_controller.drivers.baseDriverV2 import BaseModbusDriverV2
from io_controller.drivers.formats import SendCommandResponse
from io_controller.drivers.socketDrivers.modbus.ModbusBaseClasses import ModbusClient
from io_controller.drivers.socketDrivers.modbus.ModbusRegisterDefinitions import ENUM_Register, RegisterMap, Register, INT_Register
from io_controller.drivers.socketDrivers.modbus.ModbusClient import ModbusSocketFramer
from io_controller.drivers.baseDeviceV2 import ModbusBattery, ModbusBatteryTotal, ModbusEnergyMeter, ModbusHybridInverter

import enirislib.standardKeys as SK

import common.constants as constants
import common.status as status


class WattsNextBattery(ModbusBattery):
    
    def _getOffset(self) -> int:
        return 12222 + 512 * (self.childDeviceCategoryModuleNumber)

    @classmethod
    def isValid(cls, modbusClient: "ModbusClient", busAddress: int, userInputs: "Dict[str, str|float|int|bool]", **kwargs):
        moduleNumber = kwargs.get("moduleNumber")
        if moduleNumber is None:
            return False
# (offset), reg_number, SK ,1 = 16bit 2 = 32bit ,  type, scalefactor
        offset = 12222 + 512 * moduleNumber
        stateOfHealth = INT_Register(offset + 58, SK.stateOfHealth_frac.name, 2, [Register.R_INPUT], 0.001).read(busAddress, modbusClient)
        return stateOfHealth is not None and 0 < stateOfHealth <= 1
    
    @staticmethod
    def getMaxInstanceCount(modbusClient: ModbusClient, busAddress: int, **kwargs) -> int:
        return 5
    
    def getRegisterMaps(self) -> "RegisterMap | list[RegisterMap]":
        regMap = RegisterMap(self.busAddress)
        regMap.append(INT_Register(self._getOffset() + 76, SK.batteryVoltage_V.name, 2, [Register.R_INPUT], 0.1, signed=True))
        regMap.append(INT_Register(self._getOffset() + 78, SK.batteryCurrent_A.name, 2, [Register.R_INPUT], -0.1, signed=True))
        regMap.append(INT_Register(self._getOffset() + 80, SK.stateOfHealth_frac.name, 2, [Register.R_INPUT], 0.001))
        regMap.append(INT_Register(self._getOffset() + 82, SK.stateOfCharge_frac.name, 2, [Register.R_INPUT], 0.001))
        return regMap


class WattsNextBatteryTotal(ModbusBatteryTotal):

    CHILD_CLASSES = {
        "Battery": WattsNextBattery,
    }

    @classmethod
    def isValid(cls, modbusClient: "ModbusClient", busAddress: int, userInputs: "Dict[str, str|float|int|bool]", **kwargs):
        return True

    def getRegisterMaps(self) -> "RegisterMap | list[RegisterMap]":
        regMap = RegisterMap(self.busAddress)
        regMap.append(INT_Register(1, SK.stateOfCharge_frac.name, 2, [Register.R_INPUT], 0.01))
        return regMap


class WattsNextStorageCabinet(ModbusHybridInverter):
    
    AC_CONTROL = "setpoint"
    BATTERY_CONTROL = "unavailable"
    PV_CONTROL = "unavailable"

    CHILD_CLASSES = {
        "BatteryTotal": WattsNextBatteryTotal,
    }
    
    def getModel(self) -> str:
        return "ES232/115K-A/EU"
        
    @classmethod
    def isValid(cls, modbusClient: "ModbusClient", busAddress: int, userInputs: "Dict[str, str|float|int|bool]", **kwargs) -> bool:

        # there is no frequency or voltage available of the whole system, 
        # read out PCS number and check if it is between 1 and 5
        PCSNumberReg = INT_Register(548, "PCS number", 2, [Register.R_INPUT], 1)
        PCSNummber = PCSNumberReg.read(busAddress, modbusClient)
        return PCSNummber is not None and 1 <= PCSNummber <= 5

    def getRegisterMaps(self) -> "RegisterMap | list[RegisterMap]":
        regMap = RegisterMap(self.busAddress)
        regMap.append(ENUM_Register(560, SK.status.name, 2, [Register.R_INPUT], {
            0: status.DeviceStatusInfo("No warning", self.nodeId),
            1: status.DeviceStatusWarning("Warning prompt", self.nodeId),
            2: status.DeviceStatusWarning("Single battery pack shutdown", self.nodeId),
            3: status.DeviceStatusWarning("Single energy storage cabinet shutdown", self.nodeId),
            4: status.DeviceStatusWarning("System shutdown", self.nodeId),
            5: status.DeviceStatusWarning("System shutdown and emergency stop", self.nodeId),
        }))
        regMap.append(ENUM_Register(2, SK.operationMode.name, 2, [Register.R_INPUT], {
            -1: status.DeviceStatusError("Fault", self.nodeId),
            0: status.DeviceStatusInfo("Standby", self.nodeId),
            1: status.DeviceStatusInfo("Charging", self.nodeId),
            2: status.DeviceStatusInfo("Discharging", self.nodeId),
            3: status.DeviceStatusInfo("Working", self.nodeId),
            4: status.DeviceStatusInfo("Power-off", self.nodeId),
        }))
        regMap.append(INT_Register(822, SK.actualPowerTot_W.name, 2, [Register.R_INPUT], 1000, signed=True))
        return regMap
    
    def sendCommand(self, nodeId, smartgridMode: bool, powerSetpoint_W: float, **kwargs) -> tuple[SendCommandResponse, status.StatusMsgList]:
        targetActivePower = INT_Register(785,"TargetTotalActivePower", 2, [Register.W_MUL_HOLDING], -100, signed=True)
        if not smartgridMode:
            return SendCommandResponse(
                nodeId, smartgridMode, powerSetpoint_W,
                SendCommandResponse.SUCCESS,
                msg=SendCommandResponse.MSG_DISABLED
            ), [status.DeviceUncontrolled(self.nodeId)]
        
        targetActivePower.write(self.busAddress, self.modbusClient, powerSetpoint_W)

        return SendCommandResponse(nodeId, smartgridMode, powerSetpoint_W, SendCommandResponse.SUCCESS, msg=SendCommandResponse.MSG_APPLIED), [
            status.MethodSuccessMsg(self.nodeId)
        ]


class WattsNextStorageEnergyMeter(ModbusEnergyMeter):

    @classmethod
    def isValid(cls, modbusClient: "ModbusClient", busAddress: int, userInputs: "Dict[str, str|float|int|bool]", **kwargs) -> bool:
        # there is no frequency or voltage available of the whole system, 
        # read out PCS number and check if it is between 1 and 5
        PCSNumberReg = INT_Register(520, "PCS number", 2, [Register.R_INPUT], 1)
        PCSNummber = PCSNumberReg.read(busAddress, modbusClient)
        return PCSNummber is not None and 1 <= PCSNummber <= 5
    
    def getModel(self) -> str:
        return "ES232/115K-A/EU"
        
    def getSerialNo(self) -> str:
        # return something else then the default empty string, 
        # because otherwise the energy meter will get skipped duiring scanning, 
        # because double serial number get skipped, and the serial number of the storage cabinet is also empty
        return "EM"

    def getRegisterMaps(self) -> "RegisterMap | list[RegisterMap]":
        regMap = RegisterMap(self.busAddress)
        regMap.append(INT_Register(78, SK.power_W.name, 2, [Register.R_INPUT], 1000, signed=True))
        regMap.append(INT_Register(80, SK.importedEnergyDeltaTot_Wh.name, 2, [Register.R_INPUT], 1))
        return regMap


class WattsNextStorageCabinetTCPProtocol(BaseModbusDriverV2):
    """
    Protocol documentation:
    - Document file name: Energy_Management_System__EMS__Northbound_Interfac.pdf
    - Document title: Energy Management System (EMS) Northbound Interface Protocol
    - Document version: v2.2
    - Document publish date: December 16, 2024
    - Google drive link: https://drive.google.com/
    - Manufacturer technical contact person: info@dummy.com
    """

    PROTOCOL_NAME = f"WattsNext EMS Protocol (TCP)"
    MANIFEST = {
        "frontendName": f"WattsNext EMS Protocol (TCP)",
        "categories": [constants.HOME_BATTERY],
        "brands": ["wattsNext"],
        "connModes": [constants.TCP],
        "addressInfo": {"minBusAddress": 1, "maxBusAddress": 247},
        "tcpInfo": {"tcpPorts": [502]},
        "deviceTypes": {"Wattsnext All-in-one Cabinet ES232/115K-A/EU": ("N/A", "https://docs.eniris.be/Devices/PV-hybrid-and-battery-inverters/WattsNext/")},
        "compatible": [constants.SMART_GRID_CONTROLLER],
        "userInputs": [],
    }

    PARENT_DEVICE_CLASSES = {
        "Cabinet": WattsNextStorageCabinet,
        "EnergyMeter": WattsNextStorageEnergyMeter,
    }

    MODBUS_FRAMER = ModbusSocketFramer
    DEFAULT_BUS_ADDRESS: int = 1
    SCAN_ADDRESSES = BaseModbusDriverV2.SCAN_ADDRESSES

