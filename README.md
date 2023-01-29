# Dutch Energy Cap
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)
[![Open Source Love png1](https://badges.frapsoft.com/os/v1/open-source.png?v=103)](https://github.com/ellerbrock/open-source-badges/)

Custom component to create Dutch Energy Cap sensors in Home-Assistant. This custom component can create day values for both power and/or gas caps and can summarize it in month values.

## Installation

1. Using your tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory (folder) there, you need to create it.
3. In the `custom_components` directory (folder) create a new folder called `dutch_energy_cap`.
4. Download _all_ the files from the `custom_components/dutch_energy_cap/` directory (folder) in this repository.
5. Place the files you downloaded in the new directory (folder) you created.
6. Restart Home Assistant before further configuration.
7. Look at the `Example Configuration` section for further configuration.
8. Restart Home Assistant again when configuration is done to activate the configuration.

## Example Configuration
###### SENSOR - CONFIGURATION.YAML
```yaml
  sensor:
    - platform: dutch_energy_cap
      power: true           # (optional, default = true)
      gas: false            # (optional, default = true)
      day_value: true       # (optional, default = true)
      month_value: false    # (optional, default = true)
```
