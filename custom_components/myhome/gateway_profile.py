"""Gateway profiles representing capabilities and constraints of MyHOME hardware."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional, Set, Tuple, Type


# OpenWebNet WHO Subsystem constants
WHO_LIGHTING = 1
WHO_AUTOMATION = 2
WHO_HEATING = 4
WHO_CEN = 15
WHO_SOUND = 16
WHO_ENERGY = 18
WHO_LOAD_CONTROL = 22
WHO_CEN_PLUS = 25

DEFAULT_SUPPORTED_WHO: Tuple[int, ...] = (
    WHO_LIGHTING,
    WHO_AUTOMATION,
    WHO_HEATING,
    WHO_CEN,
    WHO_SOUND,
    WHO_ENERGY,
    WHO_LOAD_CONTROL,
    WHO_CEN_PLUS,
)


@dataclass
class GatewayProfile:
    """Base profile describing gateway characteristics."""
    model_name: str
    max_workers: int = 1
    default_workers: int = 1
    supports_hmac: bool = False
    requires_password: bool = True
    supports_native_transitions: bool = False
    recommended_transition_mode: str = "software_stepped"
    default_port: int = 20000
    supports_energy_instant_power: bool = True
    supports_audio: bool = True
    max_queue_size: int = 250
    command_queue_delay: float = 0.05
    supports_extended_frames: bool = False
    supported_who: Tuple[int, ...] = DEFAULT_SUPPORTED_WHO

    @property
    def max_command_workers(self) -> int:
        """Alias for max_workers representing concurrent command session capacity."""
        return self.max_workers

    @property
    def display_name(self) -> str:
        return f"{self.model_name} Gateway"

    def supports_who(self, who: int) -> bool:
        """Check if a specific OpenWebNet WHO subsystem is supported."""
        return who in self.supported_who

    def can_support_workers(self, count: int) -> bool:
        """Validate whether the gateway model supports the requested worker count."""
        return 1 <= count <= self.max_workers


class F454Profile(GatewayProfile):
    """Profile for BTicino F454 IP web server / gateway."""
    def __init__(self):
        super().__init__(
            model_name="F454",
            max_workers=4,
            default_workers=1,
            supports_hmac=True,
            requires_password=True,
            supports_native_transitions=True,
            recommended_transition_mode="software_stepped",
            default_port=20000,
            supports_energy_instant_power=True,
            supports_audio=True,
            max_queue_size=250,
            command_queue_delay=0.05,
            supports_extended_frames=True,
            supported_who=DEFAULT_SUPPORTED_WHO,
        )


class F455Profile(GatewayProfile):
    """Profile for BTicino F455 audio/video web server."""
    def __init__(self):
        super().__init__(
            model_name="F455",
            max_workers=4,
            default_workers=1,
            supports_hmac=True,
            requires_password=True,
            supports_native_transitions=True,
            recommended_transition_mode="software_stepped",
            default_port=20000,
            supports_energy_instant_power=True,
            supports_audio=True,
            max_queue_size=250,
            command_queue_delay=0.05,
            supports_extended_frames=True,
            supported_who=DEFAULT_SUPPORTED_WHO,
        )


class MH200NProfile(GatewayProfile):
    """Profile for Legrand/BTicino MH200N scenario programmer."""
    def __init__(self):
        super().__init__(
            model_name="MH200N",
            max_workers=1,
            default_workers=1,
            supports_hmac=False,
            requires_password=True,
            supports_native_transitions=False,
            recommended_transition_mode="software_stepped",
            default_port=20000,
            supports_energy_instant_power=False,
            supports_audio=False,
            max_queue_size=100,
            command_queue_delay=0.15,
            supports_extended_frames=False,
            supported_who=(
                WHO_LIGHTING,
                WHO_AUTOMATION,
                WHO_HEATING,
                WHO_CEN,
                WHO_CEN_PLUS,
            ),
        )


class MH202Profile(GatewayProfile):
    """Profile for Legrand/BTicino MH202 scenario programmer."""
    def __init__(self):
        super().__init__(
            model_name="MH202",
            max_workers=2,
            default_workers=1,
            supports_hmac=True,
            requires_password=True,
            supports_native_transitions=False,
            recommended_transition_mode="software_stepped",
            default_port=20000,
            supports_energy_instant_power=True,
            supports_audio=True,
            max_queue_size=200,
            command_queue_delay=0.10,
            supports_extended_frames=True,
            supported_who=DEFAULT_SUPPORTED_WHO,
        )


class MyHomeServer1Profile(GatewayProfile):
    """Profile for BTicino MyHomeServer1 (MHS1)."""
    def __init__(self):
        super().__init__(
            model_name="MyHomeServer1",
            max_workers=4,
            default_workers=2,
            supports_hmac=True,
            requires_password=True,
            supports_native_transitions=True,
            recommended_transition_mode="software_stepped",
            default_port=20000,
            supports_energy_instant_power=True,
            supports_audio=True,
            max_queue_size=300,
            command_queue_delay=0.02,
            supports_extended_frames=True,
            supported_who=DEFAULT_SUPPORTED_WHO,
        )


class GenericGatewayProfile(GatewayProfile):
    """Fallback profile for unknown or unlisted OpenWebNet gateways."""
    def __init__(self, model_name: str = "Generic"):
        super().__init__(
            model_name=model_name,
            max_workers=2,
            default_workers=1,
            supports_hmac=False,
            requires_password=True,
            supports_native_transitions=False,
            recommended_transition_mode="software_stepped",
            default_port=20000,
            supports_energy_instant_power=True,
            supports_audio=True,
            max_queue_size=200,
            command_queue_delay=0.05,
            supports_extended_frames=False,
            supported_who=DEFAULT_SUPPORTED_WHO,
        )


_PROFILES: Dict[str, Type[GatewayProfile]] = {
    "f454": F454Profile,
    "f455": F455Profile,
    "mh200n": MH200NProfile,
    "mh200": MH200NProfile,
    "mh202": MH202Profile,
    "myhomeserver1": MyHomeServer1Profile,
    "mhs1": MyHomeServer1Profile,
}


def get_gateway_profile(model_name: Optional[str]) -> GatewayProfile:
    """Resolve a GatewayProfile by gateway model name or return a generic profile."""
    if not model_name:
        return GenericGatewayProfile()
    cleaned = model_name.lower().replace(" ", "").replace("-", "").replace("_", "")
    profile_cls = _PROFILES.get(cleaned)
    if profile_cls:
        return profile_cls()
    return GenericGatewayProfile(model_name=model_name)
