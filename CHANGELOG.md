# Changelog

All modification for this custom_component will be added in this file.

## [v4.0.0] - 2025-12-08
### Added
- Add log file neviweb130_log.txt to replace the home-assistant.log that was removed.
  The log is limited to 2 meg with a log rotation up to 3 files.
- Add support for TH6250WF-PRO thermostat.
- Add support for Wi-Fi lite thermostat, TH1143WF, TH1144WF.
- Add support for HP6000WF-xx thermostat.

### Fix
- Fix HA warning about device numeric unique_id.
- Fix bug for leak sensor connected directly to sedna valve.
- Fix sensor error code notification that send excessive notification when an error code is received.
- Refactor set_humidity method to accept humidity parameter from climate service.
- Fix slow update when changing hvac mode on card.
- Code cleanup in devices services.
- Fix HA recorder warning.

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