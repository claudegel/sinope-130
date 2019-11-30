## Home Assistant Neviweb130 Custom Components

Here is a custom components to suport [Neviweb](https://neviweb.com/) in [Home Assistant](http://www.home-assistant.io). 
Neviweb is a platform created by Sinopé Technologies to interact with their smart devices like thermostats, light switches/dimmers , load controllers, plug and water leak detector etc. 

Neviweb130 will manage the devices connected to Neviweb via the GT130 gateway. It is presently in pre-release stage as some information are still missing from Sinopé. I need your help to test as I don't have all zigbee device connected to my network yet.

## Supported Devices
Here is a list of currently supported devices. Basically, it's everything that can be added in Neviweb.
- Thermostats
  - Sinopé TH1124ZB-3000 Line voltage thermostat
  - Sinopé TH1124ZB-4000 Line voltage thermostat
  - Sinopé TH1124ZB-3000 Thermostat for public areas
  - Sinopé TH1124ZB-4000 Thermostat for public areas
  - Sinopé TH1300ZB 3600w Floor heating thermostat
  - Sinopé TH1400ZB Low voltage thermostat
- Lighting
  - Sinopé SW2500ZB Light switch
  - Sinopé DM2500ZB Dimmer 
- Specialized Control
  - Sinopé RM3250ZB Load controller 50A
  - Sinopé SP2610ZB in-wall outlet
  - Sinopé SP2600ZB smart plug
- Water leak detector
  - Sinopé VA4201WZ, sedna valve 1 inch
  - Sinopé VA4200WZ, sedna valve 3/4 inch
  - Sinopé WL4200,   water leak detector
  - Sinopé WL4200S,  water leak detector with sensor
- Tank level monitor
  - Sinopé LM4110-ZB, level monitor

## Prerequisite
You need to connect your devices to a GT130 web gateway and add them in your Neviweb portal before being able to interact with them within Home Assistant. Please refer to the instructions manual of your device or visit [Neviweb support](https://www.sinopetech.com/blog/support-cat/plateforme-nevi-web/).

There are two custom component giving you the choice to manage your devices via the neviweb portal or directly via your GT130 gateway:
- [Neviweb](https://github.com/claudegel/sinope-130) custom component to manage your devices via neviweb portal
- [Sinope](https://github.com/claudegel/sinope-gt130) custom component to manage your devices directly via your GT125 web gateway

You need to install only one of them but both can be used at the same time on HA.

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
  network: '<your gt130 network name in neviweb>'
```

**Configuration options:**  

| key | required | default | description
| --- | --- | --- | ---
| **username** | yes |  | Your email address used to log in Neviweb.
| **password** | yes |  | Your Neviweb password.
| **network** | yes | if not specified, 1st network found is used. Write the name of the GT130 network you want to control.
| **scan_interval** | no | 540 | The number of seconds between access to Neviweb to update device state. Sinopé asked for a minimum of 5 minutes between polling now so you can reduce scan_interval to 300. Don't go over 600, the session will expire.

## Troubleshooting
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

If you find a bug it's very new release without all the doc from Sinopé.

## TO DO
- when this component will be stable. Merge it with The Neviweb component to poll all devices from only one component.
