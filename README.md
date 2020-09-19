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
- Wifi thermostats
  - Sinopé TH1124WF wifi 4000W Line voltage thermostat
  - Sinopé TH1123WF wifi 3000W Line voltage thermostat
  - Sinopé TH1400WF wifi low voltage thermostat
  - Sinopé TH1300WF wifi 3600W floor thermostat
- Zigbee lighting
  - Sinopé SW2500ZB Light switch
  - Sinopé DM2500ZB Dimmer 
- Zigbee specialized Control
  - Sinopé RM3250ZB Load controller 50A
  - Sinopé SP2610ZB in-wall outlet
  - Sinopé SP2600ZB smart portable plug
- Water leak detector
  - Sinopé VA4201WZ, sedna valve 1 inch
  - Sinopé VA4200WZ, sedna valve 3/4 inch
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
      ...
    ```
## Configuration

To enable Neviweb130 management in your installation, add the following to your `configuration.yaml` file, then restart Home Assistant.

```yaml
# Example configuration.yaml entry
neviweb130:
  username: '<your Neviweb username>'
  password: '<your Neviweb password>'
  network: '<your gt130 network name in Neviweb>'
  scan_interval: 360
```

**Configuration options:**  

| key | required | default | description
| --- | --- | --- | ---
| **username** | yes |  | Your email address used to log in Neviweb.
| **password** | yes |  | Your Neviweb password.
| **network** | yes | if not specified, 1st network found is used. Write the name of the GT130 network you want to control.
| **scan_interval** | no | 540 | The number of seconds between each access to Neviweb to update device state. Sinopé asked for a minimum of 5 minutes between polling now so you can reduce scan_interval to 300. Don't go over 600, the session will expire.

## Troubleshooting
if you see your device in the log but it do not apear in entity list you need to add the device model number in the code. Or you can send the model number to me so I can add it in the code.

In the log look for lines:
```yaml
[custom_components.neviweb130] Received gateway data: [{'id': 100225, 'identifier': '500b91400001f750', 'name': 'Chargeur auto', 'family': '2506',...
[custom_components.neviweb130] Received signature data: {'signature': {'model': 2506, 'modelCfg': 0, 'softBuildCfg': 0, 'softVersion': {'minor': 9, 'middle': 2, 'major': 1}, 'hardRev': 2, 'protocol': 'sinopcom'}}
```
'family': '2506' and 'model': 2506 is what you need to find the model number of your device. It should be added id climate.py, light.py, switch.py or sensor.py than restart HA and your device will be listed in entity list.

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
