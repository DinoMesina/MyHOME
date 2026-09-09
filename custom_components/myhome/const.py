"""Constants for the MyHome component."""
import logging

LOGGER = logging.getLogger(__package__)
DOMAIN = "myhome"

ATTR_GATEWAY = "gateway"
ATTR_MESSAGE = "message"
INTEGRATION_VERSION = "1.0.0-beta"

CONF = "config"
CONF_ENTITY = "entity"
CONF_ENTITIES = "entities"
CONF_ENTITY_NAME = "entity_name"
CONF_ICON = "icon"
CONF_ICON_ON = "icon_on"
CONF_PLATFORMS = "platforms"
CONF_ADDRESS = "address"
CONF_OWN_PASSWORD = "password"
CONF_FIRMWARE = "firmware"
CONF_SSDP_LOCATION = "ssdp_location"
CONF_SSDP_ST = "ssdp_st"
CONF_DEVICE_TYPE = "deviceType"
CONF_DEVICE_MODEL = "model"
CONF_MANUFACTURER = "manufacturer"
CONF_MANUFACTURER_URL = "manufacturerURL"
CONF_UDN = "UDN"
CONF_WORKER_COUNT = "command_worker_count"
CONF_FILE_PATH = "config_file_path"
CONF_GENERATE_EVENTS = "generate_events"
CONF_PARENT_ID = "parent_id"
CONF_WHO = "who"
CONF_WHERE = "where"
CONF_BUS_INTERFACE = "interface"
CONF_ZONE = "zone"
CONF_DIMMABLE = "dimmable"
CONF_GATEWAY = "gateway"
CONF_DEVICE_CLASS = "class"
CONF_INVERTED = "inverted"
CONF_ADVANCED_SHUTTER = "advanced"
CONF_HEATING_SUPPORT = "heat"
CONF_COOLING_SUPPORT = "cool"
CONF_FAN_SUPPORT = "fan"
CONF_STANDALONE = "standalone"
CONF_CENTRAL = "central"
CONF_SHORT_PRESS = "pushbutton_short_press"
CONF_SHORT_RELEASE = "pushbutton_short_release"
CONF_LONG_PRESS = "pushbutton_long_press"
CONF_LONG_RELEASE = "pushbutton_long_release"
CONF_ROTARY_CW_SLOW = "rotary_cw_slow"
CONF_ROTARY_CW_FAST = "rotary_cw_fast"
CONF_ROTARY_CCW_SLOW = "rotary_ccw_slow"
CONF_ROTARY_CCW_FAST = "rotary_ccw_fast"
CONF_TRAVEL_TIME = "travel_time"
DEFAULT_TRAVEL_TIME = 25
WHO_BURGLAR_ALARM = "5"
PLATFORM_ALARM = "alarm_control_panel"

# ── Decoder pool (Dynamic Proxy for Music Assistant / Spotify) ──────────────
# Up to 4 decoder slots, one per BTicino physical source input.
# Keys follow the pattern: decoder_{n}_{field}, n = 1..4
CONF_DECODER_ENTITY = "decoder_{}_entity"     # HA media_player entity_id
CONF_DECODER_SOURCE = "decoder_{}_source"     # BTicino source number (int 1-4)
CONF_DECODER_PRE_GAIN = "decoder_{}_pre_gain" # Volume offset % added to decoder (0-50)
CONF_DECODER_SLOTS = 4                        # Maximum number of decoder slots

# ── Light transition modes (software stepped dimming) ─────────────────────
CONF_TRANSITION_MODE = "transition_mode"
TRANSITION_MODE_NATIVE = "native"
TRANSITION_MODE_SOFTWARE = "software_stepped"
TRANSITION_MODE_AUTO = "auto"  # back-compat alias → software_stepped
TRANSITION_MODES = [TRANSITION_MODE_SOFTWARE, TRANSITION_MODE_NATIVE, TRANSITION_MODE_AUTO]
DEFAULT_TRANSITION_MODE = TRANSITION_MODE_SOFTWARE

# Tuning for software stepped fades (best-effort)
SOFTWARE_TRANSITION_STEP_INTERVAL = 0.3   # target seconds between steps
SOFTWARE_TRANSITION_MIN_STEPS = 2
SOFTWARE_TRANSITION_MAX_STEPS = 25
