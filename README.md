## Home Assistant Neviweb130 Custom Components

Here is a custom components to suport [Neviweb](https://neviweb.com/) in [Home Assistant](http://www.home-assistant.io). 
Neviweb is a platform created by Sinopé Technologies to interact with their smart devices like thermostats, light switches/dimmers , load controllers, plug and water leak detector etc. 

Neviweb130 will manage the devices connected to Neviweb via the GT130 gateway and the new wifi devices. It is presently almost up to date with Neviweb but some informations are still missing from Sinopé. As new devices are launched by Sinopé, they are added to this custom-component. If you have a device that is not supported yet, please open an issue and I'll add it rapidly.

## Supported Devices
Here is a list of currently supported devices. Basically, it's everything that can be added in Neviweb.
- Zigbee thermostats:
  - Sinopé TH1123ZB 3000W Line voltage thermostat
  - Sinopé TH1124ZB 4000W Line voltage thermostat
  - Sinopé TH1123ZB 3000W Thermostat for public areas
  - Sinopé TH1124ZB 4000W Thermostat for public areas
  - Sinopé TH1123ZB-G2 3000W Thermostat second generation
  - Sinopé TH1124ZB-G2 4000W Thermostat second generation
  - Sinopé TH1134ZB-HC for control of heating/cooling interlocking
  - Sinopé TH1300ZB 3600W Floor heating thermostat
  - Sinopé TH1400ZB Low voltage thermostat
  - Sinopé TH1500ZB 3600W double pole thermostat
  - Ouellet OTH3600-GA-ZB Floor thermostat
  - Ouellet OTH4000-ZB 4000W Line voltage thermostat
- Wifi thermostats (no need for GT130):
  - Sinopé TH1124WF wifi 4000W Line voltage thermostat
  - Sinopé TH1123WF wifi 3000W Line voltage thermostat
  - Sinopé TH1300WF wifi 3600W floor thermostat
  - Sinopé TH1310WF wifi 3600W floor thermostat
  - Sinopé TH1400WF wifi low voltage thermostat
  - Sinopé TH1500WF wifi 3600W double pole thermostat
  - Flextherm concerto connect FLP55 floor thermostat (sku FLP55 do not provide energy stats in Neviweb)
- Zigbee lighting:
  - Sinopé SW2500ZB Light switch
  - Sinopé DM2500ZB Dimmer
  - Sinopé DM2550ZB Dimmer
- Zigbee specialized Control:
  - Sinopé RM3250ZB Load controller 50A
  - Sinopé RM3500ZB Calypso load controller 20,8A for water heater
  - Sinopé SP2610ZB in-wall outlet
  - Sinopé SP2600ZB smart portable plug
  - Sinopé MC3100ZB Sedna valve multi-controller for allarm system
- Wifi specialized control:
  - Sinopé RM3500WF Load controller for water heater
- Water leak detector and valves:
  - Sinopé VA4201WZ, VA4221WZ, sedna valve 1 inch
  - Sinopé VA4200WZ, VA4220WZ, sedna valve 3/4 inch wifi
  - Sinopé VA4200ZB, sedna valve 3/4 inch zigbee
  - Sinopé VA4220WZ, sedna 2e gen 3/4 inch
  - Sinopé VA4220WF, sedna 2e gen 3/4 inch, wifi
  - Sinopé VA4220ZB, sedna 2e gen 3/4 inch, zigbee
  - Sinopé VA4221WZ, sedna 2e gen 1 inch
  - Sinopé VA4221WF, sedna 2e gen 1 inch, wifi
  - Sinopé VA4221ZB, sedna 2e gen 1 inch, zigbee
  - Sinopé WL4200,   water leak detector
  - Sinopé WL4200S,  water leak detector with sensor
  - Sinopé WL4200C,  perimeter cable water leak detector
  - Sinopé WL4200ZB, water leak detector
  - Sinopé ACT4220WF-M, VA4220WF-M, sedna multi-residential master valve 2e gen 3/4 inch, wifi
  - Sinopé ACT4220ZB-M, VA4220ZB-M, sedna multi-residential slave valve 2e gen 3/4 inch, zigbee
  - Sinopé ACT4221WF-M, VA4221WF-M, sedna multi-residential master valve 2e gen. 1 inch, wifi
  - Sinopé ACT4221ZB-M, VA4221ZB-M, sedna multi-residential slave valve 2e gen. 1 inch, zigbee
- Flow sensor: (supported as attribute for the 2e gen Sedna valves)
  - Sinopé FS4220, 3/4 inch flow sensor
  - Sinopé FS4221, 1 inch flow sensor
- Tank level monitor:
  - Sinopé LM4110-ZB, Propane tank level monitor
- Gateway
  - GT130
  - GT4220WF-M, mesh gateway

## Prerequisite
You need to connect your devices to a GT130 web gateway and add them in your Neviweb portal before being able to interact with them within Home Assistant. Please refer to the instructions manual of your device or visit [Neviweb support](https://www.sinopetech.com/blog/support-cat/plateforme-nevi-web/).

For wifi thermostats you need to connect your devices to Neviweb and add them in the same network then the GT130 zigbee devices.

There are two custom component giving you the choice to manage your devices via the neviweb portal or directly via your GT130 gateway:
- [Neviweb130](https://github.com/claudegel/sinope-130) custom component to manage your devices via neviweb portal
- Buy a zigbee gateway like Dresden Conbe II usb dongle and manage directly your zigbee device via ZHA component. I'm adding support for Sinopé zigbee in zha-device-handlers. You can test new Sinopé devices quirks in [sinope-zha](https://github.com/claudegel/sinope-zha) where I put all new quirks before they are merged into zha-device-handlers.

You need to install only one of them but both can be used at the same time on HA. Zigbee devices managed directly via Conbe II must be removed from Neviweb as they cannot be on two networks at the same time.

## Neviweb custom component to manage your device via Neviweb portal:
## Installation
There are two methods to install this custom component:
- via HACS component:
  - This repository is compatible with the Home Assistant Community Store ([HACS](https://community.home-assistant.io/t/custom-component-hacs/121727)).
  - After installing HACS, install 'sinope-130' from the store, and use the configuration.yaml example below.
- Manually via direct download:
  - Download the zip file of this repository using the top right, green download button.
  - Extract the zip file on your computer, then copy the entire `custom_components` folder inside your Home Assistant `config` directory (where you can find your `configuration.yaml` file).
  - Your config directory should look like this:

    ```
    config/
      configuration.yaml
      custom_components/
        neviweb130/
          __init__.py
          light.py
          const.py
          switch.py
          climate.py
          sensor.py
          services.yaml
      ...
    ```
## Configuration

To enable Neviweb130 management in your installation, add the following to your `configuration.yaml` file, then restart Home Assistant.

```yaml
# Example configuration.yaml entry
neviweb130:
  username: '<your Neviweb username>'
  password: '<your Neviweb password>'
  network: '<your gt130 location name in Neviweb>' (gt130 emplacement dans Neviweb)
  scan_interval: 360
  homekit_mode: False
  stat_interval: 1800
```
Networks names are the names found on top of first page after loging into Neviweb. If you have more then one network, just click on icon on top to find all networks names. Select the one used for GT130 or wifi devices. Both device type must be on same network to work in neviweb130.

**Configuration options:**  

| key | required | default | description
| --- | --- | --- | ---
| **username** | yes |  | Your email address used to log in Neviweb.
| **password** | yes |  | Your Neviweb password.
| **network** | no | if not specified, 1st location found is used. Write the name of the GT130 location in Neviweb you want to control.|Network name is the location name in Neviweb written on top center of first page, where your wifi or zigbee devices are registered.
| **scan_interval** | no | 540 | The number of seconds between each access to Neviweb to update device state. Sinopé asked for a minimum of 5 minutes between polling now so you can reduce scan_interval to 300. Don't go over 600, the session will expire.
| **homekit_mode** | no | False | Add support for Homekit specific values.
| **stat_interval** | no | 1800 | The number of seconds between each access to Neviweb for energy statistic update. Scan will start after 5 minutes from HA startup and will be updated at every 300 to 1800 seconds.

## Sedna valve
For Sedna valve there is two way to connect it to Neviweb:
- Via wifi direct connection. This way leak sensor are connected directly to the Sedna valve which will close if leak is detected.
- via GT130 in zigbee mode. This  way leak sensor are also connected to the GT130 but on leak detection nothing is passed to the valve. You'll need to set some automation rule in Neviweb or HA, to have the Sedna valve close if leak is detected by sensor.

Both mode are supported by this custom component. 

## Gateway GT130
It is now possible to know if your GT130 is still online of offline with Neviweb via the gateway_status attribute. The GT130 is detected as sensor.neviweb130_sensor_gt130

## Custom services
Automations require services to be able to send commande. Ex. light.turn_on. For the Sinopé devices connected via neviweb130, it is possible to use custom services to send specific information to devices or to change some devices parameters. Those custom services can be accessed via development tool/services or can be used in automation:
- neviweb130.set_second_display, allow to change setting of the thermostats second display from setpoint temperature to outdoor temperature. This need to be sent only once to each devices.
- neviweb130.set_climate_keypad_lock, allow to lock the keypad of the climate device.
- neviweb130.set_light_keypad_lock, allow to lock the keypad of the light device.
- neviweb130.set_switch_keypad_lock, allow to lock the keypad of the switch device.
- neviweb130.set_light_timer, this is used to set a timer in seconds (0 to 10800) to the light devices to turn_off after that delay.
- neviweb130.set_switch_timer, this is used to set a timer in seconds (0 to 10800) to the switch devices and multi controller device to turn_off after that delay.
- neviweb130.set_switch_timer2, this is used to set the timer2 in seconds (0 to 10800) to the switch multi controller device to turn_off after that delay.
- neviweb130.set_led_indicator, this allow to change led indicator color and intensity on light devices for «on» and «off» state. you can send any color in the RGB list via the three color parameters red, green and blue and you can set intensity of the led indicator.
- neviweb130.set_time_format to display time in 12h or 24h on thermostats.
- neviweb130.set_temperature_format to disply temperature in celsius or fahrenheit format on thermostats.
- neviweb130.set_backlight to set bakclight intensity in state «on» or «off» for thermostats.
- neviweb130.set_wattage to set wattageOverload for light devices.
- neviweb130.set_auxiliary_load to set status and load of the auxilary heating.
- neviweb130.set_setpoint_min to set minimum setpoint temperature for thermostats.
- neviweb130.set_setpoint_max to set maximum setpoint temperature for thermostats.
- neviweb130.set_cool_setpoint_min to set minimum cooling setpoint for TH1134ZB-HC.
- neviweb130.set_cool_setpoint_max to set maximum cooling setpoint for TH1134ZB-HC.
- neviweb130.set_sensor_alert to set all alert for water leak sensor, temperature, battery, leak, status and set action on valve.
- neviweb130.set_valve_alert to set low battery alert status.
- neviweb130.set_valve_temp_alert to set low temperature alert on sedna valve.
- neviweb130.set_early_start to set early heating on/off for wifi thermostats.
- neviweb130.set_air_floor_mode to switch between floor or ambiant temperature sensor to control room temperature.
- neviweb130.set_floor_air_limit to set floor thermostat max air limit temperature.
- neviweb130.set_phase_control to set phase control mode for DM2550ZB dimmer (reverse or forward).
- neviweb130.set_hvac_dr_options to set or reset DR period option in Neviweb for thermostats.
- neviweb130.set_hvac_dr_setpoint to adjust thermostat setpoint reduction during DR period, 0 to -10 oC.
- neviweb130.set_load_dr_options to set or reset DR period options in Neviweb for load controler.
- neviweb130.set_cycle_output to set main cycle length of low voltage thermostat in minutes.
- neviweb130.set_aux_cycle_output to set auxiliary cycle length of low voltage thermostats in minutes.
- neviweb130.set_control_onOff change status of output 1 and 2 on alarm multi-controller for sedna valve.
- neviweb130.set_battery_type set battery type, alkaline or lithium, for the water leak sensor
- neviweb130.set_tank_size to set the water heater tank capacity for Calypso RM3500ZB
- neviweb130.set_low_temp_protection to activate or not the water heater protection for water temperature. Below 45 oC heating is auto restarted.
- neviweb130.set_controlled_device to change the name of the device controled by the RM3250ZV load controler

## Catch Éco Sinopé signal for peak period
If you have at least on thermostat or one load controler registered with Éco Sinopé program, it is now possible to catch when Neviweb send the signal for pre-heating start period for thermostats or start signal for the load controler. Three attributes have been added to know that peak period is comming:

- For thermostats and load controler:
  - eco_status: set to «off» during normal operation, to «on» during peak period.
  - eco_power: set to «off» during normal operation, to «on» during peak period.
  - eco_optout: set to «off» during normal operation during peak period, to «on» if somebody turn on the load controler during peak period.

It is then possible to make an automation to set all devices ready for peak period.

## Statistic for energy
Six attributes are added to track energy usage for devices:
- hourly_kwh_count: total count of kwh hourly usage
- daily_kwh_count: total count of kwh daily usage
- monthly_kwh_count: total count of kwh monthly usage
- hourly_kwh: kwh used for last hour
- daily_kwh: kwh used for last day
- monthly_kwh: kwh used for last month

They are polled from Neviweb every 30 minutes. The first polling start 5 minutes after HA restart.

### Track energy consumption in HA Energy dashboard
When energy attributes are available, it is possible to track energy consumption of individual devices in Home Assistant energy dashboard by creating a [Template sensor](https://www.home-assistant.io/integrations/template/) in configuration.yaml:
```yaml
template:
  - sensor:
      - name: "Basement energy usage"
        unit_of_measurement: "kWh"
        device_class: energy
        state_class: total_increasing
        state: >-
          {{ state_attr("climate.neviweb130_th1124zb_basement","hourly_kwh_count") }}
```
or:
```yaml
template:
  - sensor:
      - name: "Basement energy usage"
        unit_of_measurement: "kWh"
        device_class: energy
        state_class: total
        state: >-
          {{ state_attr("climate.neviweb130_th1124zb_basement","hourly_kwh") }}
```

## Statistic for Sedna flow sensor
Six attributes are added to track water usage for Sedna valve. They are shown as m³ (cubic meeter) which is what energy module is looking for:
- hourly_flow_count: total count of kwh hourly usage
- daily_flow_count: total count of kwh daily usage
- monthly_flow_count: total count of kwh monthly usage
- hourly_flow: kwh used for last hour
- daily_flow: kwh used for last day
- monthly_flow: kwh used for last month

They are polled from Neviweb every 30 minutes. The first polling start 5 minutes after HA restart.

### Track water consumption in HA Energy dashboard
When flow attributes are available, it is possible to track water consumption of sedna valve in Home Assistant energy dashboard by creating a [Template sensor](https://www.home-assistant.io/integrations/template/) in configuration.yaml:
```yaml
template:
  - sensor:
      - name: "Sedna Water Flow"
        unit_of_measurement: "m³"
        device_class: water
        state_class: total_increasing
        state: >-
          {{ state_attr("switch.neviweb130_water_valve","hourly_flow_count") }}
```
or:
```yaml
template:
  - sensor:
      - name: "Sedna Water Flow"
        unit_of_measurement: "m³"
        device_class: water
        state_class: total
        state: >-
          {{ state_attr("switch.neviweb130_water_valve","hourly_flow") }}
```

## Troubleshooting
if you see your device in the log but it do not apear in entity list you need to add the device model number in the code. Or you can send the model number to me so I can add it in the code.

In the log look for lines:
```yaml
[custom_components.neviweb130] Received gateway data: [{'id': 100225, 'identifier': '500b91400001f750', 'name': 'Chargeur auto', 'family': '2506',...
[custom_components.neviweb130] Received signature data: {'signature': {'model': 2506, 'modelCfg': 0, 'softBuildCfg': 0, 'softVersion': {'minor': 9, 'middle': 2, 'major': 1}, 'hardRev': 2, 'protocol': 'sinopcom'}}
```
'family': '2506' and 'model': 2506 is what you need to find the model number of your device. It should be added in climate.py, light.py, switch.py or sensor.py near line 132 to 136 (climate.py) depending on device type. Than restart HA and your device will be listed in entity list.

If you get a stack trace related to a Neviweb130 component in your `home-assistant.log` file, you can file an issue in this repository.

You can also post in one of those threads to get help:
- https://community.home-assistant.io/t/sinope-line-voltage-thermostats/17157
- https://community.home-assistant.io/t/adding-support-for-sinope-light-switch-and-dimmer/38835

### Turning on Neviweb130 debug messages in `home-assistant.log` file

To have a maximum of information to help you, please provide a snippet of your `home-assistant.log` file. I've added some debug log messages that could help diagnose the problem.

Add thoses lines to your `configuration.yaml` file
   ```yaml
   logger:
     default: warning
     logs:
       custom_components.neviweb130: debug
       homeassistant.service: debug
       homeassistant.config_entries: debug
   ```
This will set default log level to warning for all your components, except for Neviweb which will display more detailed messages.

### Error messages received from Neviweb
In you log you can get those messages from Neviweb:
- VALINVLD : Invalid value sent to Neviweb.
- SVCINVREQ: Invalid request sent to Neviweb, service do not exist or malformed request.
- DVCCOMMTO: Device Communication Timeout: device do not respond fast enough or you are polling that device too frequently.
- DVCACTNSPTD: Device action not supported. Service call is not supported for that specific device.
- USRSESSEXP: User session expired. Reduce your scan_intervall below 6 minutes or your session will be terminated.
- ACCSESSEXC: To many open session at the same time. This is common if you restart Home Assistant many time and/or you also have an open session on Neviweb. 
- DVCUNVLB: Device unavailable. Neviweb is unable to connect with specific device, mostly wifi devices.
- SVCERR: Service error. Service unavailable. Try later.
- DVCATTRNSPTD: Device sttribute not supported, The device you have installed have and older firmware and do not support som attributes. Wait for firmware update in Neviweb and the error should dissapear or file an issue so we can put an exception in the code. 
- USRBADLOGIN: your login and/or password provided in configuration for Neviweb is no good.
- ReadTimeout: Request was sent to the device but no answer came back. Network problem.

## Customization
Install  [Custom-Ui](https://github.com/Mariusthvdb/custom-ui) custom_component via HACS and add the following in your code:

Icons for heat level: create folder www in the root folder .homeassistant/www
copy the six icons there. You can find them under local/www
feel free to improve my icons and let me know. (See icon_view2.png)

For each thermostat add this code in `customize.yaml`
```yaml
climate.neviweb_climate_thermostat_name:
  templates:
    entity_picture: >
      if (attributes.heat_level < 1) return '/local/heat-0.png';
      if (attributes.heat_level < 21) return '/local/heat-1.png';
      if (attributes.heat_level < 41) return '/local/heat-2.png';
      if (attributes.heat_level < 61) return '/local/heat-3.png';
      if (attributes.heat_level < 81) return '/local/heat-4.png';
      return '/local/heat-5.png';
 ```  
 In `configuration.yaml` add this
```yaml
homeassistant:
  customize: !include customize.yaml
``` 
## Customization for leak sensor

Same as above. 
-Create a sensor:
```yaml
battery_spa:
        friendly_name: "Batterie spa"
        unit_of_measurement: "%"
        value_template: "{{ state_attr('sensor.neviweb130_sensor_spa', 'Battery_level') }}"
```        
-For each leak detector add this to your `customize.yaml` file
```yaml
sensor.battery_spa:
  templates:
    entity_picture: >
      if (entity.state < 10) return '/local/battery-1.png';
      if (entity.state < 30) return '/local/battery-2.png';
      if (entity.state < 50) return '/local/battery-3.png';
      if (entity.state < 70) return '/local/battery-4.png';
      return '/local/battery-5.png';
sensor.neviweb130_sensor_spa:    
      if (attributes.Leak_status == "ok") return ''/local/drop.png'';
      return ''/local/leak.png'';'
```
Icons are availables from www directory. copy them in config/www


If you find a bug it's very new release without all the doc from Sinopé.

## TO DO
- when this component will be stable. Merge it with The Neviweb component to poll all devices from only one component.
