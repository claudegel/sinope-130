## Home Assistant Neviweb130 Custom Components

Here is a custom components to suport [Neviweb](https://neviweb.com/) in [Home Assistant](http://www.home-assistant.io). 
Neviweb is a platform created by Sinopé Technologies to interact with their smart devices like thermostats, light switches/dimmers , load controllers, plug and water leak detector etc. 

Neviweb130 will manage the devices connected to Neviweb via the GT130 gateway and the new wifi devices. It is presently in pre-release stage as some information are still missing from Sinopé.

## Supported Devices
Here is a list of currently supported devices. Basically, it's everything that can be added in Neviweb.
- Zigbee thermostats
  - Sinopé TH1124ZB 3000W Line voltage thermostat
  - Sinopé TH1124ZB 4000W Line voltage thermostat
  - Sinopé TH1124ZB 3000W Thermostat for public areas
  - Sinopé TH1124ZB 4000W Thermostat for public areas
  - Sinopé TH1300ZB 3600W Floor heating thermostat
  - Sinopé TH1400ZB Low voltage thermostat
  - Sinopé TH1500ZB 3600W double pole thermostat
  - Ouellet OTH4000-ZB 4000W Line voltage thermostat
  - Ouellet OTH3600-GA-ZB Floor thermostat
- Wifi thermostats (no need for GT130)
  - Sinopé TH1124WF wifi 4000W Line voltage thermostat
  - Sinopé TH1123WF wifi 3000W Line voltage thermostat
  - Sinopé TH1400WF wifi low voltage thermostat
  - Sinopé TH1300WF wifi 3600W floor thermostat
  - Sinopé TH1310WF wifi 3600W floor thermostat
- Zigbee lighting
  - Sinopé SW2500ZB Light switch
  - Sinopé DM2500ZB Dimmer 
- Zigbee specialized Control
  - Sinopé RM3250ZB Load controller 50A
  - Sinopé SP2610ZB in-wall outlet
  - Sinopé SP2600ZB smart portable plug
- Water leak detector
  - Sinopé VA4201WZ, VA4221WZ, sedna valve 1 inch
  - Sinopé VA4200WZ, VA4220WZ, sedna valve 3/4 inch wifi
  - Sinopé VA4200ZB, VA4220ZB, sedna valve 3/4 inch zigbee
  - Sinopé WL4200,   water leak detector
  - Sinopé WL4200S,  water leak detector with sensor
- Tank level monitor
  - Sinopé LM4110-ZB, level monitor

## Prerequisite
You need to connect your devices to a GT130 web gateway and add them in your Neviweb portal before being able to interact with them within Home Assistant. Please refer to the instructions manual of your device or visit [Neviweb support](https://www.sinopetech.com/blog/support-cat/plateforme-nevi-web/).

For wifi thermostats you need to connect your devices to Neviweb and add them in the same network then the GT130 zigbee devices. Later I'll add support to add them in the GT125 network.

There are two custom component giving you the choice to manage your devices via the neviweb portal or directly via your GT130 gateway:
- [Neviweb130](https://github.com/claudegel/sinope-130) custom component to manage your devices via neviweb portal
- Buy a zigbee gateway like Dresden Conbe II usb dongle and manage directly your zigbee device via ZHA component. I'm adding support for Sinopé zigbee there

You need to install only one of them but both can be used at the same time on HA. Zigbee devices managed directly via Conbe II must be removed from Neviweb.

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
```
Networks names are the names found on top of first page after loging into Neviweb. If you have more then one network, just click on icon on top to find all networks names. Select the one used for GT130 or wifi devices. Both device type must be on same network to work in neviweb130.

**Configuration options:**  

| key | required | default | description
| --- | --- | --- | ---
| **username** | yes |  | Your email address used to log in Neviweb.
| **password** | yes |  | Your Neviweb password.
| **network** | yes | if not specified, 1st location found is used. Write the name of the GT130 location you want to control.
| **scan_interval** | no | 540 | The number of seconds between each access to Neviweb to update device state. Sinopé asked for a minimum of 5 minutes between polling now so you can reduce scan_interval to 300. Don't go over 600, the session will expire.

## Sedna valve
For Sedna valve there is two way to connect it to Neviweb:
- Via wifi direct connection. This way leak sensor are connected directly to the Sedna valve which will close if leak is detected.
- via GT130 in zigbee mode. This  way leak sensor are also connected to the GT130 but on leak detection nothing is passed to the valve. You'll need to set some automation rule to have the sedna valve close if leak is detected by sensor.
Both mode are supported by this custom component. 

## Custom services
Automations require services to be able to send commande. Ex. light.turn_on. For the Sinopé devices connected via neviweb130, it is possible to use custom services to send specific information to devices or to change some devices parameters. Those custom services can be accessed via development tool/services or can be used in automation:
- neviweb130.set_second_display, allow to change setting of the thermostats second display from setpoint temperature to outdoor temperature. This need to be sent only once to each devices.
- neviweb130.set_climate_keypad_lock, allow to lock the keypad of the climate device.
- neviweb130.set_light_keypad_lock, allow to lock the keypad of the light device.
- neviweb130.set_switch_keypad_lock, allow to lock the keypad of the switch device.
- neviweb130.set_light_timer, this is used to set a timer in seconds (0 to 10800) to the light devices to turn_off after that delay.
- neviweb130.set_switch_timer, this is used to set a timer in seconds (0 to 10800) to the switch devices to turn_off after that delay.
- neviweb130.set_led_indicator, this allow to change led indicator color and intensity on light devices for «on» and «off» state. you can send any color in the RGB list via the three color parameters red, green and blue and you can set intensity of the led indicator.
- neviweb130.set_time_format to display time in 12h or 24h on thermostats.
- neviweb130.set_temperature_format to disply temperature in celsius or fahrenheit format on thermostats.
- neviweb130.set_backlight to set bakclight intensity in state «on» or «off» for thermostats.
- neviweb130.set_wattage to set wattageOverload for light devices.
- neviweb130.set_setpoint_min to set minimum setpoint temperature for thermostats.
- neviweb130.set_setpoint_max to set maximum setpoint temperature for thermostats.
- neviweb130.set_sensor_alert to set all alert for water leak sensor, temperature, battery, leak, status and set action on valve
- neviweb130.set_valve_alert to set low battery alert status
- neviweb130.set_valve_temp_alert to set low temperature alert on sedna valve

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
   ```
This will set default log level to warning for all your components, except for Neviweb which will display more detailed messages.

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

Same as above. For each leak detector add this to your `customize.yaml`
```yaml
sensor.neviweb130_sensor_spa:
  templates:
    entity_picture: 'if (attributes.Battery < 20) return ''/local/battery-2.png'';
      if (attributes.Leak_status == "ok") return ''/local/drop.png'';
      return ''/local/leak.png'';'
```
Icons are availables from www directory.


If you find a bug it's very new release without all the doc from Sinopé.

## TO DO
- when this component will be stable. Merge it with The Neviweb component to poll all devices from only one component.
