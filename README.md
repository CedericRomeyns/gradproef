# WattsNext EMS Protocol (TCP) Driver

This repository contains a Python driver implementation for the **WattsNext Energy Management System (EMS) Northbound Interface Protocol (TCP)**. The driver supports Modbus-based communication with WattsNext all-in-one battery storage cabinets and associated devices.

## Features

- Modbus TCP communication with WattsNext battery storage systems.
- Register mapping and validation for:
  - Individual battery modules (`WattsNextBattery`)
  - Total battery state (`WattsNextBatteryTotal`)
  - Storage cabinet/inverter (`WattsNextStorageCabinet`)
  - Storage cabinet's energy meter (`WattsNextStorageEnergyMeter`)
- High-level Python abstractions for reading/writing registers, sending setpoints, and status decoding.
- Extensible and integrates with a broader IO controller framework.

## Protocol & Documentation

- **Protocol:** WattsNext EMS Northbound Interface (TCP/Modbus)
- **Version:** 2.2 (December 16, 2024)
- **Technical Contact:** info@dummy.com
- **Cabinet Model:** ES232/115K-A/EU

## Project Structure

- `WattsNextBattery`, `WattsNextBatteryTotal`: Classes for interacting with battery modules and their total state.
- `WattsNextStorageCabinet`: Main cabinet/hybrid inverter interface.
- `WattsNextStorageEnergyMeter`: Class for energy metering.
- `WattsNextStorageCabinetTCPProtocol`: Driver class, protocol manifest, device scanning, and configuration.

## Requirements

- Python 3.x
- `enirislib` and the IO controller framework with Modbus support
- Project-specific constants, status helpers, and register definitions (see `common` and `io_controller` imports).

## Device Types Supported

- WattsNext All-in-one Cabinet ES232/115K-A/EU ([Docs](https://docs.eniris.be/Devices/PV-hybrid-and-battery-inverters/WattsNext/))

## Configuration

- **Connection Modes:** TCP (port 502)
- **Modbus Bus Addresses:** 1-247 supported
- **Device Categories:** Home Battery, Smart Grid Controller

## Development

- Code structure follows base classes for Modbus devices and drivers.
- Register definitions and mappings extend generic Modbus register abstractions.
- Easily extensible for new device types or custom Modbus register maps.



> **Note:** This code is intentionally not production-ready and does not provide real protection of the company’s intellectual property. It is provided solely as an illustrative example. With appropriate modifications and supporting backend logic, it could be adapted for practical use.
