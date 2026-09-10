""" This module handles TCP connections to the OpenWebNet gateway """

import asyncio
import hmac
import hashlib
import string
import random
import logging
from typing import Optional, List, Dict, Tuple, Any
from urllib.parse import urlparse

from .discovery import find_gateways, get_gateway, get_port
from .message import OWNMessage, OWNSignaling


class OWNGateway:
    def __init__(self, discovery_info: dict):
        # Attributes potentially provided by user
        self.address = (
            discovery_info["address"] if "address" in discovery_info else None
        )
        self._password = (
            discovery_info["password"] if "password" in discovery_info else None
        )
        # Attributes retrieved from SSDP discovery
        self.ssdp_location = (
            discovery_info["ssdp_location"]
            if "ssdp_location" in discovery_info
            else None
        )
        self.ssdp_st = (
            discovery_info["ssdp_st"] if "ssdp_st" in discovery_info else None
        )
        # Attributes retrieved from UPnP device description
        self.device_type = (
            discovery_info["deviceType"] if "deviceType" in discovery_info else None
        )
        self.friendly_name = (
            discovery_info["friendlyName"] if "friendlyName" in discovery_info else None
        )
        mfg = discovery_info.get("manufacturer")
        if isinstance(mfg, (list, tuple)):
            self.manufacturer = str(mfg[0]) if mfg else "BTicino S.p.A."
        elif mfg:
            self.manufacturer = str(mfg)
        else:
            self.manufacturer = "BTicino S.p.A."

        mfg_url = discovery_info.get("manufacturerURL")
        self.manufacturer_url = str(mfg_url) if mfg_url else None
        self.model_name = (
            discovery_info["modelName"]
            if "modelName" in discovery_info
            else "Unknown model"
        )
        self.model = self.model_name
        from ..gateway_profile import get_gateway_profile
        self.profile = get_gateway_profile(self.model_name)
        model_num = (
            discovery_info["modelNumber"] if "modelNumber" in discovery_info else None
        )
        if isinstance(model_num, (list, tuple)):
            self.model_number = ".".join(str(x) for x in model_num) if model_num else None
        elif model_num is not None:
            self.model_number = str(model_num)
        else:
            self.model_number = None
        # self.presentationURL = (
        #     discovery_info["presentationURL"]
        #     if "presentationURL" in discovery_info
        #     else None
        # )
        self.serial_number = (
            discovery_info["serialNumber"] if "serialNumber" in discovery_info else None
        )
        self.udn = discovery_info["UDN"] if "UDN" in discovery_info else None
        # Attributes retrieved from SOAP service control
        self.port = discovery_info["port"] if "port" in discovery_info else None

        self._log_id = f"[{self.model_name} gateway - {self.host}]"

    @property
    def unique_id(self) -> str:
        return self.serial_number

    @unique_id.setter
    def unique_id(self, unique_id: str) -> None:
        self.serial_number = unique_id

    @property
    def host(self) -> str:
        return self.address

    @host.setter
    def host(self, host: str) -> None:
        self.address = host

    @property
    def firmware(self) -> str:
        return self.model_number

    @firmware.setter
    def firmware(self, firmware: str) -> None:
        if isinstance(firmware, (list, tuple)):
            self.model_number = ".".join(str(x) for x in firmware) if firmware else None
        elif firmware is not None:
            self.model_number = str(firmware)
        else:
            self.model_number = None

    @property
    def serial(self) -> str:
        return self.serial_number

    @serial.setter
    def serial(self, serial: str) -> None:
        self.serial_number = serial

    @property
    def password(self) -> str:
        return self._password

    @password.setter
    def password(self, password: str) -> None:
        self._password = password

    @property
    def log_id(self) -> str:
        return self._log_id

    @log_id.setter
    def log_id(self, id: str) -> None:
        self._log_id = id

    @classmethod
    async def get_first_available_gateway(cls, password: str = None):
        local_gateways = await find_gateways()
        local_gateways[0]["password"] = password
        return cls(local_gateways[0])

    @classmethod
    async def find_from_address(cls, address: str):
        if address is not None:
            return cls(await get_gateway(address))
        else:
            return await cls.get_first_available_gateway()

    @classmethod
    async def build_from_discovery_info(cls, discovery_info: dict):
        if (
            ("address" not in discovery_info or discovery_info["address"] is None)
            and "ssdp_location" in discovery_info
            and discovery_info["ssdp_location"] is not None
        ):
            discovery_info["address"] = urlparse(
                discovery_info["ssdp_location"]
            ).hostname

        if "port" in discovery_info and discovery_info["port"] is None:
            if (
                "ssdp_location" in discovery_info
                and discovery_info["ssdp_location"] is not None
            ):
                discovery_info["port"] = await get_port(discovery_info["ssdp_location"])
            elif "address" in discovery_info and discovery_info["address"] is not None:
                return await cls.find_from_address(discovery_info["address"])
            else:
                return await cls.get_first_available_gateway(
                    password=discovery_info["password"]
                    if "password" in discovery_info
                    else None
                )

        return cls(discovery_info)


class OWNSession:
    """Connection to OpenWebNet gateway"""

    SEPARATOR = "##".encode()

    def __init__(
        self,
        gateway: OWNGateway = None,
        connection_type: str = "test",
        logger: logging.Logger = None,
        on_state_change: Optional[Any] = None,
    ):
        """Initialize the class
        Arguments:
        logger: instance of logging
        address: IP address of the OpenWebNet gateway
        port: TCP port for the connection
        password: OpenWebNet password
        """

        self._gateway = gateway
        self._type = connection_type.lower()
        self._logger = logger or logging.getLogger(__name__)
        self._on_state_change = on_state_change

        self._stream_reader: Optional[asyncio.StreamReader] = None
        self._stream_writer: Optional[asyncio.StreamWriter] = None

    @property
    def is_connected(self) -> bool:
        """Check if the underlying socket writer is connected."""
        return self._stream_writer is not None and not self._stream_writer.is_closing()

    def _notify_state_change(self, connected: bool) -> None:
        """Notify state change listener if registered."""
        if self._on_state_change is not None:
            try:
                self._on_state_change(connected)
            except Exception as ex:
                self._logger.debug(
                    "%s on_state_change callback error: %s",
                    self._gateway.log_id if self._gateway else "Gateway",
                    ex,
                )

    @property
    def gateway(self) -> OWNGateway:
        return self._gateway

    @gateway.setter
    def gateway(self, gateway: OWNGateway) -> None:
        self._gateway = gateway

    @property
    def password(self) -> str:
        return str(self._password)

    @password.setter
    def password(self, password: str) -> None:
        self._password = password

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @logger.setter
    def logger(self, logger: logging.Logger) -> None:
        self._logger = logger

    @property
    def connection_type(self) -> str:
        return self._type

    @connection_type.setter
    def connection_type(self, connection_type: str) -> None:
        self._type = connection_type.lower()

    @classmethod
    async def test_gateway(cls, gateway: OWNGateway) -> dict:
        connection = cls(gateway)
        return await connection.test_connection()

    async def test_connection(self) -> dict:
        retry_count = 0
        retry_timer = 1

        while True:
            try:
                if retry_count > 2:
                    self._logger.error(
                        "%s Test session connection still refused after 3 attempts.",
                        self._gateway.log_id,
                    )
                    return None
                (
                    self._stream_reader,
                    self._stream_writer,
                ) = await asyncio.open_connection(
                    self._gateway.address, self._gateway.port
                )
                break
            except ConnectionRefusedError:
                self._logger.warning(
                    "%s Test session connection refused, retrying in %ss.",
                    self._gateway.log_id,
                    retry_timer,
                )
                await asyncio.sleep(retry_timer)
                retry_count += 1
                retry_timer *= 2

        try:
            result = await self._negotiate()
            await self.close()
        except ConnectionResetError:
            error = True
            error_message = "password_retry"
            self._logger.error(
                "%s Negotiation reset while opening %s session. Wait 60 seconds before retrying.",
                self._gateway.log_id,
                self._type,
            )

            return {"Success": not error, "Message": error_message}

        return result

    async def connect(self):
        self._logger.debug("%s Opening %s session.", self._gateway.log_id, self._type)

        retry_count = 0
        retry_timer = 1

        while True:
            try:
                if retry_count > 4:
                    self._logger.error(
                        "%s %s session connection still refused after 5 attempts.",
                        self._gateway.log_id,
                        self._type.capitalize(),
                    )
                    return None
                (
                    self._stream_reader,
                    self._stream_writer,
                ) = await asyncio.open_connection(
                    self._gateway.address, self._gateway.port
                )
                return await self._negotiate()
            except (ConnectionRefusedError, asyncio.IncompleteReadError):
                self._logger.warning(
                    "%s %s session connection refused, retrying in %ss.",
                    self._gateway.log_id,
                    self._type.capitalize(),
                    retry_timer,
                )
                await asyncio.sleep(retry_timer)
                retry_count += 1
                retry_timer = min(retry_timer * 2, 60) # Exponential backoff capped at 60s
            except ConnectionResetError:
                self._logger.warning(
                    "%s %s session connection reset, retrying in %ss.",
                    self._gateway.log_id,
                    self._type.capitalize(),
                    retry_timer,
                )
                await asyncio.sleep(retry_timer)
                retry_count += 1
                retry_timer = min(retry_timer * 2, 60) # Exponential backoff capped at 60s
            except TimeoutError:
                self._logger.warning(
                    "%s %s session connection timeout, retrying in %ss.",
                    self._gateway.log_id,
                    self._type.capitalize(),
                    retry_timer,
                )
                await asyncio.sleep(retry_timer)
                retry_count += 1
                retry_timer = min(retry_timer * 2, 60)

    async def close(self) -> None:
        """Closes the connection to the OpenWebNet gateway"""
        if self._stream_writer:
            self._stream_writer.close()
            try:
                await self._stream_writer.wait_closed()
            except (TypeError, AttributeError, Exception):
                pass
        self._logger.debug(
            "%s %s session closed.", self._gateway.log_id, self._type.capitalize()
        )

    async def _negotiate(self) -> dict:
        type_id = 0 if self._type == "command" else 1
        error = False
        error_message = None

        self._logger.debug(
            "%s Negotiating %s session.", self._gateway.log_id, self._type
        )

        self._stream_writer.write(f"*99*{type_id}##".encode())
        await self._stream_writer.drain()

        raw_response = await self._stream_reader.readuntil(OWNSession.SEPARATOR)
        resulting_message = OWNSignaling(raw_response.decode())
        # self._logger.debug("%s Reply: `%s`", self._gateway.log_id, resulting_message)

        if resulting_message.is_nack():
            if self._type == "command":
                # Fallback for newer Legrand gateways (F455, Classe 300) requiring *99*9## (CMD_SESSION_ALT)
                # Credit: Massimo Valla (@mvalla / openwebnet4j)
                self._logger.info(
                    "%s *99*0## was NACKed; attempting *99*9## alternate command session (openwebnet4j fallback by @mvalla).",
                    self._gateway.log_id,
                )
                self._stream_writer.write(b"*99*9##")
                await self._stream_writer.drain()
                raw_response = await self._stream_reader.readuntil(OWNSession.SEPARATOR)
                resulting_message = OWNSignaling(raw_response.decode())

            if resulting_message.is_nack():
                self._logger.error(
                    "%s Error while opening %s session.", self._gateway.log_id, self._type
                )
                return {"Success": False, "Message": "connection_refused"}

        raw_response = await self._stream_reader.readuntil(OWNSession.SEPARATOR)
        resulting_message = OWNSignaling(raw_response.decode())
        if resulting_message.is_nack():
            error = True
            error_message = "negotiation_refused"
            self._logger.debug(
                "%s Reply: `%s`", self._gateway.log_id, resulting_message
            )
            self._logger.error(
                "%s Error while opening %s session.", self._gateway.log_id, self._type
            )
        elif resulting_message.is_sha():
            self._logger.debug(
                "%s Received SHA challenge: `%s`",
                self._gateway.log_id,
                resulting_message,
            )
            if self._gateway.password is None:
                error = True
                error_message = "password_required"
                self._logger.warning(
                    "%s Connection requires a password but none was provided.",
                    self._gateway.log_id,
                )
                self._stream_writer.write("*#*0##".encode())
                await self._stream_writer.drain()
            else:
                if resulting_message.is_sha_1():
                    # self._logger.debug("%s Detected SHA-1 method.", self._gateway.log_id)
                    method = "sha1"
                elif resulting_message.is_sha_256():
                    # self._logger.debug("%s Detected SHA-256 method.", self._gateway.log_id)
                    method = "sha256"
                self._logger.debug(
                    "%s Accepting %s challenge, initiating handshake.",
                    self._gateway.log_id,
                    method,
                )
                self._stream_writer.write("*#*1##".encode())
                await self._stream_writer.drain()
                raw_response = await self._stream_reader.readuntil(OWNSession.SEPARATOR)
                resulting_message = OWNSignaling(raw_response.decode())
                if resulting_message.is_nonce():
                    server_random_string_ra = resulting_message.nonce
                    # self._logger.debug("%s Received Ra.", self._gateway.log_id)
                    key = "".join(random.choices(string.digits, k=56))
                    client_random_string_rb = self._hex_string_to_int_string(
                        hmac.new(key=key.encode(), digestmod=method).hexdigest()
                    )
                    # self._logger.debug("%s Generated Rb.", self._gateway.log_id)
                    hashed_password = f"*#{client_random_string_rb}*{self._encode_hmac_password(method=method, password=self._gateway.password, nonce_a=server_random_string_ra, nonce_b=client_random_string_rb)}##"  # pylint: disable=line-too-long
                    self._logger.debug(
                        "%s Sending %s session password.",
                        self._gateway.log_id,
                        self._type,
                    )
                    self._stream_writer.write(hashed_password.encode())
                    await self._stream_writer.drain()
                    try:
                        raw_response = await asyncio.wait_for(
                            self._stream_reader.readuntil(OWNSession.SEPARATOR),
                            timeout=5,
                        )
                        resulting_message = OWNSignaling(raw_response.decode())
                        if resulting_message.is_nack():
                            error = True
                            error_message = "password_error"
                            self._logger.error(
                                "%s Password error while opening %s session.",
                                self._gateway.log_id,
                                self._type,
                            )
                        elif resulting_message.is_nonce():
                            # self._logger.debug(
                            #     "%s Received HMAC response.", self._gateway.log_id
                            # )
                            hmac_response = resulting_message.nonce
                            if hmac_response == self._decode_hmac_response(
                                method=method,
                                password=self._gateway.password,
                                nonce_a=server_random_string_ra,
                                nonce_b=client_random_string_rb,
                            ):
                                # self._logger.debug(
                                #     "%s Server identity confirmed.", self._gateway.log_id
                                # )
                                self._stream_writer.write("*#*1##".encode())
                                await self._stream_writer.drain()
                            else:
                                self._logger.error(
                                    "%s Server identity could not be confirmed.",
                                    self._gateway.log_id,
                                )
                                self._stream_writer.write("*#*0##".encode())
                                await self._stream_writer.drain()
                                error = True
                                error_message = "negociation_error"
                                self._logger.error(
                                    "%s Error while opening %s session: HMAC authentication failed.",
                                    self._gateway.log_id,
                                    self._type,
                                )
                    except asyncio.IncompleteReadError:
                        error = True
                        error_message = "password_error"
                        self._logger.error(
                            "%s Password error while opening %s session.",
                            self._gateway.log_id,
                            self._type,
                        )
                    except asyncio.TimeoutError:
                        error = True
                        error_message = "password_error"
                        self._logger.error(
                            "%s Password timeout error while opening %s session.",
                            self._gateway.log_id,
                            self._type,
                        )
        elif resulting_message.is_nonce():
            self._logger.debug(
                "%s Received nonce: `%s`", self._gateway.log_id, resulting_message
            )
            if self._gateway.password is not None:
                hashed_password = f"*#{self._get_own_password(self._gateway.password, resulting_message.nonce)}##"  # pylint: disable=line-too-long
                self._logger.debug(
                    "%s Sending %s session password.", self._gateway.log_id, self._type
                )
                self._stream_writer.write(hashed_password.encode())
                await self._stream_writer.drain()
                raw_response = await self._stream_reader.readuntil(OWNSession.SEPARATOR)
                resulting_message = OWNSignaling(raw_response.decode())
                # self._logger.debug("%s Reply: `%s`", self._gateway.log_id, resulting_message)
                if resulting_message.is_nack():
                    error = True
                    error_message = "password_error"
                    self._logger.error(
                        "%s Password error while opening %s session.",
                        self._gateway.log_id,
                        self._type,
                    )
                elif resulting_message.is_ack():
                    self._logger.debug(
                        "%s %s session established.",
                        self._gateway.log_id,
                        self._type.capitalize(),
                    )
            else:
                error = True
                error_message = "password_error"
                self._logger.error(
                    "%s Connection requires a password but none was provided for %s session.",
                    self._gateway.log_id,
                    self._type,
                )
        elif resulting_message.is_ack():
            # self._logger.debug("%s Reply: `%s`", self._gateway.log_id, resulting_message)
            self._logger.debug(
                "%s %s session established.",
                self._gateway.log_id,
                self._type.capitalize(),
            )
        else:
            error = True
            error_message = "negotiation_failed"
            self._logger.debug(
                "%s Unexpected message during negotiation: %s",
                self._gateway.log_id,
                resulting_message,
            )

        return {"Success": not error, "Message": error_message}

    def _get_own_password(self, password, nonce, test=False):
        start = True
        num1 = 0
        num2 = 0
        password = int(password)
        if test:
            print("password: %08x" % (password))
        for character in nonce:
            if character != "0":
                if start:
                    num2 = password
                start = False
            if test:
                print("c: %s num1: %08x num2: %08x" % (character, num1, num2))
            if character == "1":
                num1 = (num2 & 0xFFFFFF80) >> 7
                num2 = num2 << 25
            elif character == "2":
                num1 = (num2 & 0xFFFFFFF0) >> 4
                num2 = num2 << 28
            elif character == "3":
                num1 = (num2 & 0xFFFFFFF8) >> 3
                num2 = num2 << 29
            elif character == "4":
                num1 = num2 << 1
                num2 = num2 >> 31
            elif character == "5":
                num1 = num2 << 5
                num2 = num2 >> 27
            elif character == "6":
                num1 = num2 << 12
                num2 = num2 >> 20
            elif character == "7":
                num1 = (
                    num2 & 0x0000FF00
                    | ((num2 & 0x000000FF) << 24)
                    | ((num2 & 0x00FF0000) >> 16)
                )
                num2 = (num2 & 0xFF000000) >> 8
            elif character == "8":
                num1 = (num2 & 0x0000FFFF) << 16 | (num2 >> 24)
                num2 = (num2 & 0x00FF0000) >> 8
            elif character == "9":
                num1 = ~num2
            else:
                num1 = num2

            num1 &= 0xFFFFFFFF
            num2 &= 0xFFFFFFFF
            if character not in "09":
                num1 |= num2
            if test:
                print("     num1: %08x num2: %08x" % (num1, num2))
            num2 = num1
        return num1

    def _encode_hmac_password(
        self, method: str, password: str, nonce_a: str, nonce_b: str
    ):
        if method == "sha1":
            message = (
                self._int_string_to_hex_string(nonce_a)
                + self._int_string_to_hex_string(nonce_b)
                + "736F70653E"
                + "636F70653E"
                + hashlib.sha1(password.encode()).hexdigest()
            )
            return self._hex_string_to_int_string(
                hashlib.sha1(message.encode()).hexdigest()
            )
        elif method == "sha256":
            message = (
                self._int_string_to_hex_string(nonce_a)
                + self._int_string_to_hex_string(nonce_b)
                + "736F70653E"
                + "636F70653E"
                + hashlib.sha256(password.encode()).hexdigest()
            )
            return self._hex_string_to_int_string(
                hashlib.sha256(message.encode()).hexdigest()
            )
        else:
            return None

    def _decode_hmac_response(
        self, method: str, password: str, nonce_a: str, nonce_b: str
    ):
        if method == "sha1":
            message = (
                self._int_string_to_hex_string(nonce_a)
                + self._int_string_to_hex_string(nonce_b)
                + hashlib.sha1(password.encode()).hexdigest()
            )
            return self._hex_string_to_int_string(
                hashlib.sha1(message.encode()).hexdigest()
            )
        elif method == "sha256":
            message = (
                self._int_string_to_hex_string(nonce_a)
                + self._int_string_to_hex_string(nonce_b)
                + hashlib.sha256(password.encode()).hexdigest()
            )
            return self._hex_string_to_int_string(
                hashlib.sha256(message.encode()).hexdigest()
            )
        else:
            return None

    def _int_string_to_hex_string(self, int_string: str) -> str:
        hex_string = ""
        for i in range(0, len(int_string), 2):
            hex_string += f"{int(int_string[i:i+2]):x}"
        return hex_string

    def _hex_string_to_int_string(self, hex_string: str) -> str:
        int_string = ""
        for i in range(0, len(hex_string), 1):
            int_string += f"{int(hex_string[i:i+1], 16):0>2d}"
        return int_string


class OWNEventSession(OWNSession):
    """Event (MON) session receiving asynchronous bus updates (*99*1##).

    In physical gateways (F454, MH200N), an inactivity watchdog closes MON sessions
    after 105 seconds of silence. Based on openwebnet4j by Massimo Valla (@mvalla),
    we maintain a 90-second keepalive task sending *#*1## to keep the socket alive.
    """

    def __init__(
        self,
        gateway: OWNGateway = None,
        logger: logging.Logger = None,
        on_state_change: Optional[Any] = None,
    ):
        super().__init__(
            gateway=gateway,
            connection_type="event",
            logger=logger,
            on_state_change=on_state_change,
        )
        self._keepalive_task: Optional[asyncio.Task] = None
        self._is_active: bool = False

    @property
    def is_connected(self) -> bool:
        """Check if the event session is actively connected."""
        return self._is_active and super().is_connected

    @classmethod
    async def connect_to_gateway(cls, gateway: OWNGateway):
        connection = cls(gateway)
        await connection.connect()

    async def connect(self):
        self._cancel_keepalive()
        res = await super().connect()
        if res and res.get("Success", False):
            self._is_active = True
            self._notify_state_change(True)
            self._keepalive_task = asyncio.create_task(self._keepalive_loop())
        else:
            self._notify_state_change(False)
        return res

    def _cancel_keepalive(self):
        if self._keepalive_task and not self._keepalive_task.done():
            self._keepalive_task.cancel()
        self._keepalive_task = None

    async def _keepalive_loop(self):
        """Send periodic *#*1## keepalive frames on the event/MON session.

        Physical gateways (F454, MH200N) enforce a 105-second inactivity timeout.
        openwebnet4j (@mvalla) sends *#*1## every 90 seconds to keep the socket alive.
        """
        try:
            while self._is_active:
                await asyncio.sleep(90)
                if (
                    self._is_active
                    and self._stream_writer
                    and not self._stream_writer.is_closing()
                ):
                    self._logger.debug(
                        "%s Sending 90s MON keepalive (*#*1##) [openwebnet4j pattern by @mvalla]",
                        self._gateway.log_id,
                    )
                    self._stream_writer.write(b"*#*1##")
                    await self._stream_writer.drain()
        except asyncio.CancelledError:
            pass
        except Exception as ex:
            self._logger.debug(
                "%s Keepalive loop exception: %s", self._gateway.log_id, ex
            )

    async def close(self) -> None:
        self._is_active = False
        self._cancel_keepalive()
        self._notify_state_change(False)
        await super().close()

    async def get_next(self):
        """Acts as an entry point to read messages on the event bus.
        It will read one frame and return it as an OWNMessage object"""
        try:
            # Implement Watchdog: MH200 gateway emits time signals every ~30s. If we hear nothing for 120s, the socket hung natively.
            data = await asyncio.wait_for(
                self._stream_reader.readuntil(OWNSession.SEPARATOR),
                timeout=120.0
            )
            _decoded_data = data.decode()
            self._logger.debug("%s Event RX: %r", self._gateway.log_id, _decoded_data)
            try:
                _message = OWNMessage.parse(_decoded_data)
            except (ValueError, IndexError, TypeError) as err:
                self._logger.warning(
                    "%s Malformed event frame %r: %s",
                    self._gateway.log_id, _decoded_data, err,
                )
                return _decoded_data
            return _message if _message else _decoded_data
        except asyncio.TimeoutError:
            self._logger.error(
                "%s No heartbeat received for 120 seconds. Event socket likely hung. Severing connection.",
                self._gateway.log_id
            )
            await self.close()
            await asyncio.sleep(2)
            await self.connect()
            return None
        except asyncio.IncompleteReadError:
            self._logger.warning(
                "%s Connection interrupted, reconnecting...", self._gateway.log_id
            )
            await self.connect()
            return None
        except AttributeError:
            self._logger.exception(
                "%s Received data could not be parsed into a message:",
                self._gateway.log_id,
            )
            return None
        except ConnectionError:
            self._logger.exception("%s Connection error:", self._gateway.log_id)
            return None
        except Exception:  # pylint: disable=broad-except
            self._logger.exception("%s Event session crashed.", self._gateway.log_id)
            return None


class OWNCommandSession(OWNSession):
    RESPONSE_TIMEOUT = 30.0
    IDLE_TIMEOUT = 15.0

    def __init__(self, gateway: OWNGateway = None, logger: logging.Logger = None):
        super().__init__(gateway=gateway, connection_type="command", logger=logger)
        self._last_activity: Optional[float] = None

    async def connect(self):
        res = await super().connect()
        if res and res.get("Success", False):
            try:
                self._last_activity = asyncio.get_running_loop().time()
            except RuntimeError:
                self._last_activity = None
        return res

    @classmethod
    async def send_to_gateway(cls, message: str, gateway: OWNGateway):
        connection = cls(gateway)
        await connection.connect()
        await connection.send(message)

    @classmethod
    async def connect_to_gateway(cls, gateway: OWNGateway):
        connection = cls(gateway)
        await connection.connect()

    @classmethod
    async def probe_gateway(cls, gateway: OWNGateway, logger: logging.Logger = None) -> bool:
        """Active watchdog probe sending *#13**15## (requestModel) on command session.

        Credit: Massimo Valla (@mvalla / openwebnet4j GatewayMgmt.requestModel)
        Returns True if gateway responds with ACK.
        """
        try:
            session = cls(gateway=gateway, logger=logger or logging.getLogger(__name__))
            res = await session.connect()
            if not res or not res.get("Success", False):
                return False
            result = await session.send("*#13**15##", is_status_request=True)
            await session.close()
            return result is not None
        except Exception:
            return False

    async def close(self) -> None:
        """Discard a command stream so unread replies cannot reach another request."""
        self._last_activity = None
        try:
            await super().close()
        finally:
            self._stream_reader = None
            self._stream_writer = None

    async def _read_response(self):
        """Collect a complete response, including its terminal ACK or NACK."""
        collected = []
        loop = asyncio.get_running_loop()
        deadline = loop.time() + self.RESPONSE_TIMEOUT
        while True:
            raw = await asyncio.wait_for(
                self._stream_reader.readuntil(OWNSession.SEPARATOR),
                timeout=max(0, deadline - loop.time()),
            )
            decoded = raw.decode()
            self._logger.debug("%s Command RX: %r", self._gateway.log_id, decoded)
            try:
                response = OWNMessage.parse(decoded)
            except (ValueError, IndexError, TypeError) as err:
                self._logger.warning(
                    "%s Malformed command response %r: %s",
                    self._gateway.log_id, decoded, err,
                )
                response = None
            if isinstance(response, OWNSignaling):
                if response.is_ack() or response.is_nack():
                    return collected, response.is_ack()
            else:
                collected.append(response if response else decoded)

    async def send(self, message: str, is_status_request: bool = False):
        """Finish one transaction before the command session can be reused.

        Retry an immediate NACK once. After a lost connection, only a status
        query or a command whose write failed may be retried; a command already
        written may have been executed even when its acknowledgement was lost.
        """
        try:
            async with asyncio.timeout(self.RESPONSE_TIMEOUT):
                for attempt in range(2):
                    loop = asyncio.get_running_loop()
                    is_idle_stale = (
                        self._last_activity is not None
                        and (loop.time() - self._last_activity > self.IDLE_TIMEOUT)
                    )
                    if (
                        self._stream_writer is None
                        or self._stream_reader is None
                        or is_idle_stale
                    ):
                        if is_idle_stale:
                            self._logger.debug(
                                "%s Command session idle for >%ss; reconnecting fresh.",
                                self._gateway.log_id,
                                self.IDLE_TIMEOUT,
                            )
                        await self.close()
                        result = await self.connect()
                        if not result or not result.get("Success", False):
                            await self.close()
                            return None

                    written = False
                    try:
                        self._logger.debug("%s Command TX: %s", self._gateway.log_id, message)
                        self._stream_writer.write(str(message).encode())
                        written = True
                        await self._stream_writer.drain()
                        collected, accepted = await self._read_response()
                    except (ConnectionResetError, asyncio.IncompleteReadError):
                        await self.close()
                        if attempt == 0 and (is_status_request or not written):
                            self._logger.debug(
                                "%s Command connection reset, retrying %s once.",
                                self._gateway.log_id, message,
                            )
                            continue
                        self._logger.warning(
                            "%s Connection lost before acknowledgement of %s.",
                            self._gateway.log_id, message,
                        )
                        return None

                    if accepted:
                        self._last_activity = loop.time()
                        self._logger.debug(
                            "%s Message %s acknowledged with %s response(s).",
                            self._gateway.log_id, message, len(collected),
                        )
                        return collected or True
                    if collected or attempt == 1:
                        if is_status_request:
                            self._logger.debug(
                                "%s Gateway rejected status request %s (NACK, %s response(s)). Subsystem or device may not be present.",
                                self._gateway.log_id, message, len(collected),
                            )
                        else:
                            self._logger.warning(
                                "%s Gateway rejected message %s (NACK, %s response(s)).",
                                self._gateway.log_id, message, len(collected),
                            )
                        return None
                    self._logger.debug(
                        "%s Immediate NACK for %s, retrying once.",
                        self._gateway.log_id, message,
                    )
        except asyncio.CancelledError:
            await self.close()
            raise
        except TimeoutError:
            await self.close()
            self._logger.error(
                "%s Timed out waiting for the complete response to %s; command session closed.",
                self._gateway.log_id, message,
            )
            return None
        except Exception:  # pylint: disable=broad-except
            await self.close()
            self._logger.exception("%s Command session crashed.", self._gateway.log_id)
            return None
