""" Dutch Energy Cap sensor integration """

from __future__ import annotations

import datetime
import hashlib
import logging
import requests
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.backports.functools import cached_property
from homeassistant.components.sensor import (
    PLATFORM_SCHEMA,
    SensorDeviceClass,
    SensorEntity,
)
from homeassistant.const import (
    UnitOfEnergy,
    UnitOfVolume,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

_LOGGER = logging.getLogger(__name__)

CONF_POWER_ENABLED = "power"
CONF_GAS_ENABLED = "gas"
CONF_DAY_VALUE_ENABLED = "day_value"
CONF_MONTH_VALUE_ENABLED = "month_value"
CONF_URL = "https://www.rijksoverheid.nl/binaries/rijksoverheid/documenten/publicaties/2023/01/17/hoeveelheden-gas-en-stroom-tegen-de-tarieven-van-het-prijsplafond-per-dag/Hoeveelheden+gas+en+stroom+onder+prijsplafond+per+dag.csv"


# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_POWER_ENABLED, default='true'): cv.boolean,
    vol.Optional(CONF_GAS_ENABLED, default='true'): cv.boolean,
    vol.Optional(CONF_DAY_VALUE_ENABLED, default='true'): cv.boolean,
    vol.Optional(CONF_MONTH_VALUE_ENABLED, default='true'): cv.boolean,
})


# Setup intervals
FETCH_INTERVAL = datetime.timedelta(hours=1)
SCAN_INTERVAL = datetime.timedelta(seconds=5)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None
) -> None:
    """ Set up the sensor platforms """

    # Get config variables
    power_enabled = config[CONF_POWER_ENABLED]
    gas_enabled = config[CONF_GAS_ENABLED]
    day_value_enabled = config[CONF_DAY_VALUE_ENABLED]
    month_value_enabled = config[CONF_MONTH_VALUE_ENABLED]

    # Setup entities
    entities = []

    if power_enabled and (day_value_enabled or month_value_enabled):
        energy_type = "Power"
        _LOGGER.debug(f'Setting up Energy Cap {energy_type} sensor.')
        if day_value_enabled:
            entities.append(EnergyCapSensor(energy_type, "day"))
        if month_value_enabled:
            entities.append(EnergyCapSensor(energy_type, "month"))

    if gas_enabled and (day_value_enabled or month_value_enabled):
        energy_type = "Gas"
        _LOGGER.debug(f'Setting up Energy Cap {energy_type} sensor.')
        if day_value_enabled:
            entities.append(EnergyCapSensor(energy_type, "day"))
        if month_value_enabled:
            entities.append(EnergyCapSensor(energy_type, "month"))

    async_add_entities(entities)


class EnergyCapSensor(SensorEntity):
    """ Energy Cap Sensor """

    def __init__(self, energy_type: str, value_timeframe: str) -> None:
        """ Initialize the sensor """

        self._name = f"Dutch Energy {energy_type} Cap {'Today' if value_timeframe == 'day' else 'This Month' if value_timeframe == 'month' else ''}"
        self._state = None
        self._type = energy_type
        self._timeframe = value_timeframe
        self._unique_id = hashlib.sha1(self._name.lower().replace(" ", "_").encode("utf-8")).hexdigest()

    @property
    def name(self) -> str:
        """ Return the display name of the sensor """
        return self._name

    @property
    def unique_id(self):
        """ Return the unique id of the sensor """
        return self._unique_id

    @property
    def state(self):
        """ Return the state of the sensor """
        return self._state

    @property
    def unit_of_measurement(self):
        """ Return the unit of measurement of the sensor """
        _uom = None

        if self._type == "Power":
            _uom = UnitOfEnergy.KILO_WATT_HOUR
        elif self._type == "Gas":
            _uom = UnitOfVolume.CUBIC_METERS

        return _uom

    @cached_property
    def device_class(self) -> str:
        """ Return the device class of the sensor """
        _class = None

        if self._type == "Power":
            _class = SensorDeviceClass.ENERGY
        elif self._type == "Gas":
            _class = SensorDeviceClass.GAS

        return _class

    def update(self) -> None:
        """ Fetch new state data for the cap value """

        energy_type = self._type
        value_timeframe = self._timeframe

        energy_types = ["Power", "Gas"]
        value_timeframes = ["day", "month"]

        if energy_type not in energy_types:
            energy_types_string = '" and "'.join(energy_types)
            _LOGGER.error(f'Requested energy type "{energy_type}" not valid. Valid types are: "{energy_types_string}".')

        if value_timeframe not in value_timeframes:
            energy_types_string = '" and "'.join(energy_types)
            _LOGGER.error(f'Requested timeframe "{value_timeframe}" not valid. Valid timeframes are: "{energy_types_string}".')

        try:
            response = requests.get(CONF_URL, timeout=10)
        except requests.exceptions.RequestException as err:
            raise ValueError(err) from err

        if response.status_code != 200:
            _LOGGER.error('Cannot get data from URL.')

        cap_data = [x.split(";") for x in response.text.split('\r\n') if len(x) > 0]

        type_index = energy_types.index(energy_type) + 1
        data_dict = {datetime.datetime.strptime(i[0], '%d-%m-%Y').date(): float(i[type_index].replace(",", ".")) for i in cap_data[1:]}

        today = datetime.date.today()

        if value_timeframe == "day":
            if today in data_dict:
                self._state = round(data_dict[today], 3)
            else:
                _LOGGER.error(f'Cannot get {energy_type} data from today')
        elif value_timeframe == "month":
            month_start = today.replace(day=1)
            month_end = month_start.replace(year=month_start.year + (1 if month_start.month == 12 else 0), month=(month_start.month + 1 if month_start.month < 12 else 1)) - datetime.timedelta(days=1)

            month_value = sum([value for date, value in data_dict.items() if date >= month_start and date <= month_end])
            self._state = round(month_value, 3)
