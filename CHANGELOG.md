# Changelog

All modification for this custom_component will be added in this file.

## [v4.0.2] - 2026-01-19
### Added
- Add preliminary support for energy stat for TH6xxxWF devices.

### Fix
- Fix blocking calls in update.py
- Improve backup system
- Fix monthly, daily and hourly stat for TH6xxxWF devices.
- Improve logging for TH6xxxWF stat devices

### Doc
- Add issues templates for bug report and feature request in French and English.

## [v4.0.1] - 2026-01-17
### Added
- Add Neviweb requests counter, sensor.neviweb130_daily_requests
- Add neviweb130 updater. Please read the documentation.
- Add notification methods in helpers.py

### Fix
- Fix update version check.
- remove auto reload of neviweb130.
- Fix notification when Neviweb requests counter reach the limit.
- Refactor update.py to get proper available version from Github.

### Doc
- Documentation for updater.
- Documentation for neviweb requests counter.

## [v4.0.1b3] - 2026-01-10
### Added
- Test for workflows.

### Fix
- Fix release.yml in .github/workflows.
- Code cleaning in update.py.

### Doc

## [v4.0.1b2] - 2026-01-09
### Added
- Add async_reload_integration to reload neviweb130 after update.

### Fix
- Fix update.py to download the wright zip file with sha-256 file.
- Fix .gihub/workflows/release.yml to get the ZIP file and associated SHA-256.
- Remove default values for updater.
- Refactor update.py.

### Doc
- Update documentation for updater.

## [v4.0.1b1] - 2026-01-08
### Added
- Add update platform.
- Activate Update platform.
- Retrieve update version form GitHub.
- Add Neviweb request daily counter.
- Add daily request counter helper.
- Add dummy class NeviwebDailyRequestSensor, to create sensor.neviweb_daily_request.
- Add progress bar in update page.

### Fix
- Updated device statistics methods to include an HC parameter for energy consumption.
- Refactor energy stat to add support for TH6xxxWF energy stat.
- Add functions to extract version notes and build update summary for update platform.
- Update each platform for TH6xxxWF energy stat retrieval.
- Updated default values for update platform in const.py.
- Refactor update method in helpers.py.
- Refactor update.py method for update platform to add many options.
- Fix hass.data[DOMAIN] dictionary for request counter in all platforms.
- Improve updater format for better visibility.

### Doc
- Add documentation for update platform.
- Add documentation for daily request counter.

## [v4.0.1b0] - 2026-01-03
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
- define a dict for fan mode conversion for HP6000WF-xx.
- Add thermostat model number for Wi-Fi lite
- Add fan_speed_values_5 list for fanSpeed
- Add model number for gateway GT4220WF
- Add model number for RM3510WF
- Add specific set_hvac_mode for HP6000WF
- Add set_temperature for HP6000WF-xx

### Fix
- Fix Readme.md for configuration by @pepsiflat
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
- Fix set_heat_lockout_temperature services schema.
- Change set_heat_lockout_temperature service description.
- Refactor target_temperature logic to handle all HVAC modes and apply temperature limits for HP6000WF-xx.
- Fix translation to HVAC Modes for HP6000WF-xx
- Refactor hvac_mode and hvac_action properties for HP6000WF-xx
- Fix hvac_action to manage source type auxHeating for TH6xxxWF

### Doc
- Review documentation in readme.md
- Update ACCDAYREQMAX error message description.
- Update doc for set_heat_lockout_temperature service.

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
