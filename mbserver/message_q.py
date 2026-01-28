from __future__ import annotations

import time
from enum import Enum
from queue import Queue
from typing import Any, Dict, Mapping, Optional, Union, Literal, cast

MAX_QUEUE_SIZE = 20

b2c_q = Queue(maxsize=MAX_QUEUE_SIZE)  # queue for messages from the backend to the comms driver
c2b_q = Queue(maxsize=MAX_QUEUE_SIZE)  # queue for messages to the backend from the comms driver


class UiArea(str, Enum):
    HEADER = "header"
    BLOG_LIST = "blog_list"
    BLOG_INFO = "blog_info"
    POST_LIST = "post_list"
    POST_CONTENT = "post_content"
    PROGRESS = "progress"


class MessageTarget(str, Enum):
    FRONTEND = "frontend"
    BACKEND = "backend"
    COMMS = "comms"
    NONE = "none"  # A value has not yet been assigned


class MessageType(str, Enum):
    REQUEST = "request"
    CONTROL = "control"
    MB_MSG = "mb_msg"
    SIGNAL = "signal"
    NONE = "none"  # A value has not yet been assigned


class MessageVerb(str, Enum):
    # To FRONTEND - SIGNAL
    FLASH_RX_START = "flash_rx_start"
    FLASH_RX_STOP = "flash_rx_stop"
    FLASH_TX_START = "flash_tx_start"
    FLASH_TX_STOP = "flash_tx_stop"
    SCAN_IND_OFF = "scan_ind_off"
    RELOAD_UI = "reload_ui"

    # To BACKEND - REQ
    FETCH_LISTING = "fetch_listing"
    GET_LISTING = "get_listing"
    FETCH_POST = "fetch_post"
    GET_POST = "get_post"
    GET_BLOG_INFO = "get_blog_info"
    GET_WEATHER = "get_weather"

    # To BACKEND - CONTROL
    SCAN = "scan"
    CHG_RADIO_FREQUENCY = "chg_radio_frequency"
    CHG_USER_FREQUENCY = "chg_user_frequency"
    CHG_BLOG = "chg_blog"
    SHUTDOWN = "shutdown"

    # To BACKEND - MB_MSG
    INFORM = "inform"
    ANNOUNCE = "announce"

    # To BACKEND - SIGNAL
    NOTE_FREQ = "note_freq"
    NOTE_OFFSET = "note_offset"
    NOTE_CALLSIGN = "note_callsign"
    NOTE_PTT = "note_ptf"

    # To COMMS - MB_MSG
    SEND = "send"

    # To COMMS - CONTROL
    SET_FREQ = "set_freq"
    GET_FREQ = "get_freq"
    GET_OFFSET = "get_offset"
    GET_CALLSIGN = "get_callsign"
    NO_OP = "no_op"

    NONE = "none"  # A value has not yet been assigned


class MessageOperator(str, Enum):
    NULL = ""
    EQ = "eq"
    GT = "gt"
    LT = "lt"
    LATEST = "latest"
    MORE = "more"
    NONE = "none"  # A value has not yet been assigned


class MessageParameter(str, Enum):
    SOURCE = "source"  # The callsign of the station that sent the message.
    DESTINATION = "destination"  # The callsign of the station that the message is going or @MB for announcements.
    CALLSIGN = "callsign"  # The callsign of the station that is running this software
    FREQUENCY = "frequency"
    OFFSET = "offset"
    BLOG = "blog"
    POST_ID = "post_id"
    MB_MSG = "mb_msg"
    UI_AREA = "ui_area"
    OPERATOR = "operator"
    PTT = "ptt"


# ---- type helpers for IDE autocomplete / linting ----
# Canonical string forms are the Enum *names* (e.g. "COMMS") for target/type/verb
MessageTargetStr = Literal["FRONTEND", "BACKEND", "COMMS", "NONE"]
MessageTypeStr = Literal["REQUEST", "CONTROL", "MB_MSG", "SIGNAL", "NONE"]
# Keep verbs open-ended for maintainability: IDE will still suggest Enum names if you use MessageVerb.
# If you want strict verb Literals, you can generate them, but that becomes noisy to maintain.
MessageVerbStr = str

MessageParameterKey = Union[MessageParameter, str]
MessageOperatorLike = Union[MessageOperator, str]
UiAreaLike = Union[UiArea, str]

TargetLike = Union[MessageTarget, MessageTargetStr, str]
TypeLike = Union[MessageType, MessageTypeStr, str]
VerbLike = Union[MessageVerb, MessageVerbStr, str]


def _coerce_enum(enum_cls: type[Enum], value: Any, *, field: str) -> Enum:
    """Coerce an input into an Enum member.

    Accepts:
      - An Enum member (returned as-is if correct type)
      - A string matching either the member NAME (case-insensitive) or member VALUE (case-insensitive)
    """
    if isinstance(value, enum_cls):
        return value
    if isinstance(value, str):
        s = value.strip()
        # Match by name (preferred because it matches the 'COMMS' style the caller wants).
        member = enum_cls.__members__.get(s.upper())
        if member is not None:
            return member
        # Match by value (e.g. 'comms', 'request', 'flash_rx_start')
        for m in enum_cls:  # type: ignore[assignment]
            if str(m.value).lower() == s.lower():
                return m
    raise ValueError(f"Invalid {field}: {value!r}. Expected one of {[m.name for m in enum_cls]} or their values.")


def _coerce_param_key(key: MessageParameterKey) -> MessageParameter:
    if isinstance(key, MessageParameter):
        return key
    if isinstance(key, str):
        s = key.strip()
        member = MessageParameter.__members__.get(s.upper())
        if member is not None:
            return member
        # match by value
        for m in MessageParameter:
            if m.value.lower() == s.lower():
                return m
    raise ValueError(f"Invalid parameter key: {key!r}. Expected one of {[m.value for m in MessageParameter]}.")


def _validate_param_value(param: MessageParameter, value: Any) -> Any:
    """Validate and (where helpful) coerce parameter values."""
    if param in (MessageParameter.SOURCE, MessageParameter.DESTINATION, MessageParameter.CALLSIGN, MessageParameter.BLOG):
        if not isinstance(value, str):
            raise TypeError(f"Parameter '{param.value}' must be a str, got {type(value).__name__}.")
        return value

    if param is MessageParameter.MB_MSG:
        if not isinstance(value, str):
            raise TypeError(f"Parameter '{param.value}' must be a str, got {type(value).__name__}.")
        return value

    if param in (MessageParameter.FREQUENCY, MessageParameter.OFFSET):
        if not isinstance(value, int):
            raise TypeError(f"Parameter '{param.value}' must be an int, got {type(value).__name__}.")
        return value

    if param is MessageParameter.POST_ID:
        # Internally this is often coerced to int later; accept either int or a digit string.
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.strip().isdigit():
            return value.strip()
        raise TypeError(
            f"Parameter '{param.value}' must be an int or a digit string, got {value!r} ({type(value).__name__})."
        )

    if param is MessageParameter.PTT:
        if not isinstance(value, bool):
            raise TypeError(f"Parameter '{param.value}' must be True or False, got {type(value).__name__}.")
        return value

    if param is MessageParameter.OPERATOR:
        return _coerce_enum(MessageOperator, value, field="operator")

    if param is MessageParameter.UI_AREA:
        return _coerce_enum(UiArea, value, field="ui_area")

    # Future-proofing: if new params are added but not yet validated here, allow them.
    return value


class UnifiedMessage:
    """Message used for transport to/from the comms layer.

    You can set fields using either Enums (legacy style) or short strings.

    Examples:
        m.set_many(target=MessageTarget.COMMS, typ=MessageType.CONTROL, verb=MessageVerb.SET_FREQ,
                   params={MessageParameter.FREQUENCY: 7078000})

        m.set_many(target="COMMS", typ="CONTROL", verb="SET_FREQ",
                   params={"frequency": 7078000})
    """

    __slots__ = ("ts", "priority", "target", "typ", "verb", "params")

    def __init__(self, **kwargs: Any):
        self.ts: float = time.time()
        self.priority: int = 1
        self.target: MessageTarget = MessageTarget.NONE
        self.typ: MessageType = MessageType.NONE
        self.verb: MessageVerb = MessageVerb.NONE
        # Store params with *string* keys (e.g. 'frequency') for compact JSON-serialisable shape.
        self.params: Dict[str, Any] = {}

        if kwargs:
            self.set_many(**kwargs)

    @classmethod
    def create(
        cls,
        *,
        target: Optional[TargetLike] = None,
        typ: Optional[TypeLike] = None,
        verb: Optional[VerbLike] = None,
        params: Optional[Mapping[MessageParameterKey, Any]] = None,
        priority: Optional[int] = None,
        ts: Optional[float] = None,
        **extra: Any,
    ) -> "UnifiedMessage":
        """Factory constructor with the same runtime validation as `set_many()`.

        This avoids the two-step pattern of constructing a message and then calling
        `set_many()` separately.
        """
        m = cls()
        m.set_many(
            target=target,
            typ=typ,
            verb=verb,
            params=params,
            priority=priority,
            ts=ts,
            **extra,
        )
        return m


    def set_many(
        self,
        *,
        target: Optional[TargetLike] = None,
        typ: Optional[TypeLike] = None,
        verb: Optional[VerbLike] = None,
        params: Optional[Mapping[MessageParameterKey, Any]] = None,
        priority: Optional[int] = None,
        ts: Optional[float] = None,
        **extra: Any,
    ) -> None:
        """Bulk-assign fields with runtime validation.

        This method intentionally validates at runtime to prevent invalid messages
        being created (even if called from dynamically-typed code).
        """
        if extra:
            raise ValueError(f"Unknown UnifiedMessage fields: {sorted(extra.keys())}. Allowed: ts, priority, target, typ, verb, params")

        if ts is not None:
            if not isinstance(ts, (int, float)):
                raise TypeError(f"ts must be a float timestamp, got {type(ts).__name__}")
            self.ts = float(ts)

        if priority is not None:
            if not isinstance(priority, int):
                raise TypeError(f"priority must be an int, got {type(priority).__name__}")
            self.priority = priority

        if target is not None:
            self.target = cast(MessageTarget, _coerce_enum(MessageTarget, target, field="target"))

        if typ is not None:
            self.typ = cast(MessageType, _coerce_enum(MessageType, typ, field="typ"))

        if verb is not None:
            self.verb = cast(MessageVerb, _coerce_enum(MessageVerb, verb, field="verb"))

        if params is not None:
            if not isinstance(params, Mapping):
                raise TypeError(f"params must be a mapping/dict, got {type(params).__name__}")
            new_params: Dict[str, Any] = {}
            for k, v in params.items():
                p = _coerce_param_key(k)
                new_params[p.value] = _validate_param_value(p, v)
            self.params = new_params

    # Getters

    def get_ts(self) -> float:
        return self.ts

    def get_priority(self) -> int:
        return self.priority

    def get_target(self) -> MessageTarget:
        return self.target

    def get_typ(self) -> MessageType:
        return self.typ

    def get_verb(self) -> MessageVerb:
        return self.verb

    def get_param(self, parameter: MessageParameter):
        return self.params[parameter.value]

    def get_params(self) -> Dict[str, Any]:
        return self.params