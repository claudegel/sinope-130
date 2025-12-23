# Changelog

All modification for this custom_component will be added in this file.

## [v4.0.1] - 2025-12-__
### Added
- Add support for DRStatus and DrSetpoint for TH6250WF and TH6250WF-PRO.
- Add CycleLength attribute to TH6xxxWF.
- Add BackLight attribute to TH6xxxWF.
- Add temperature error detection for TH6xxxWF.
- Add roomTemperature attribute error for HP6000WF.
- Add DrStatus onOff attribute for HP6000WF.
- Add missing STATE_WATER_LEAK attribute for RM3500xx.
- Add HP_FAN_SPEED list for HP6000WF-xx devices.
- Add specific property for HP6000WF-xx.
  - is_on
  - turn_on
  - turn_off
  - hvac_action
  - target_temperature
  - min_temp
  - max_temp
- define a dict for fan mode convertion for HP6000WF-xx.
- Add thermostat model number for Wi-Fi lite
- Add fan_speed_values_5 list for fanSpeed
- Add model number for gateway GT4220WF
- Add model number for RM3510WF
- Add specific set_hvac_mode for HP6000WF
- Add set_temperature for HP6000WF-xx

### Fix
- Fix TH1400ZB PumpProtectDuration value when status is off.
- Remove Rssi for TH6xxxWF.
- Fix message when sensor probe is disconnected for RM3500xx.
- Change log level to warning for STARTUP_MESSAGE.
- Fix roomTemperatureDisplay value and status for HP6000WF-xx.
- Fix roomTemperature attribute value for HP6000WF-xx.
- Fix fan_modes for HP6000WF-xx devices
- Fix Hvac_modes for HP6000WF-xx devices.
- Fix method set_hvac_mode for HP6000WF.
- Fix set_fan_mode for HP6000WF-xx.
- Fix set_keypad_lock service for thermostats
- Fix room_temp_error
- Fix valve flow meter divisor.
- Fix mapping value for FAN_SPEED_VALUES for HP6000WF.
- Fix value error in set_fan_mode for HP6000WF
- Change fan speed values names to lower()
- Remove extra logging for debug
- Fix set_heat_lockout action for TH112xZB-G2 and other heat-cool devices.

### Doc
- Review documentation in readme.md
- Update ACCDAYREQMAX error message description.

## [v4.0.0] - 2025-12-09
### Added
- Add log file neviweb130_log.txt to replace the home-assistant.log that was removed.
  The log is limited to 2 meg with a log rotation up to 3 files.
- Add support for TH6250WF-PRO thermostat.
- Add support for Wi-Fi lite thermostat, TH1143WF, TH1144WF.
- Add support for HP6000WF-xx thermostat.
- Add service set_air_ex_min_time_on for TH6500WF.
- Set default name.
- Add missing support for mode with TH1143WF and TH1144WF
- Add Neviweb global occupancy status management.
- Add New services for Wi-Fi and TH6xxxWF devices.

### Fix
- Fix HA warning about device numeric unique_id.
- Fix bug for leak sensor connected directly to sedna valve.
- Fix sensor error code notification that send excessive notification when an error code is received.
- Refactor set_humidity method to accept humidity parameter from climate service.
- Fix slow update when changing hvac mode on card.
- Code cleanup in devices services.
- Fix HA recorder warning.
- Fix accessory/humidity services by @bassdr.
- Fix temperature unit display by @bassdr
- Review and fix services by @bassdr.
- Fix valve support.
- Fix ATTR_FLOW_ALARM1_LENGHT name, ATTR_FLOW_ALARM1_LENGTH.

### Doc
- Add documentation for the TH6xxxWF services

## [v3.0.8] - 2025-08-11
### Added
- Add service set_flow_alarm_timer for valve with flow meter. This set a timer to stop flow alarm action for up to 24 hrs.
  Flow alarm action is automatically reactivated after the timer end.

### Fix
- Fix service description for valve.
- Code reformat for services in valve.
- Fix flow meter water statistic.

### Doc
- Add documentation for set_flow_alarm_timer.

## [v3.0.7] - 2025-07-28
### Added

### Fix
- Reduce logging for energy stat and switch to log level debug instead of warning.
