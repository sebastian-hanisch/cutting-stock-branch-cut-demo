"""SETTING_SPECS-Permalink-Muster, Presets und Zufalls-Seed-Button (Standardmuster
aus dem OR-Demo-Portfolio, siehe csbb_presets.py / cscp_presets.py)."""

import math
import random
from dataclasses import dataclass
from typing import Callable, Optional

import streamlit as st

import csbc_constants as C


@dataclass(frozen=True)
class SettingSpec:
    url_param: str
    caster: Callable
    default: object
    lo: Optional[float] = None
    hi: Optional[float] = None


SETTING_SPECS = {
    "n_types_slider": SettingSpec("n", int, C.DEFAULT_N_TYPES, C.N_TYPES_MIN, C.N_TYPES_MAX),
    "roll_width_slider": SettingSpec("w", int, C.DEFAULT_ROLL_WIDTH, C.ROLL_WIDTH_MIN, C.ROLL_WIDTH_MAX),
    "max_demand_slider": SettingSpec("d", int, C.DEFAULT_MAX_DEMAND, C.MAX_DEMAND_MIN, C.MAX_DEMAND_MAX),
    "seed_input": SettingSpec("seed", int, C.DEFAULT_SEED, 0, 2_000_000_000),
}


def bounds(state_key):
    spec = SETTING_SPECS[state_key]
    return spec.lo, spec.hi


def init_session_state_defaults():
    for state_key, spec in SETTING_SPECS.items():
        if state_key not in st.session_state:
            st.session_state[state_key] = spec.default
    if "force_regen" not in st.session_state:
        st.session_state["force_regen"] = False


def load_permalink_settings():
    if "permalink_loaded" in st.session_state:
        return
    qp = st.query_params
    for state_key, spec in SETTING_SPECS.items():
        if spec.url_param in qp:
            try:
                value = spec.caster(qp[spec.url_param])
                if isinstance(value, float) and not math.isfinite(value):
                    continue
                if spec.lo is not None:
                    value = max(spec.lo, value)
                if spec.hi is not None:
                    value = min(spec.hi, value)
                st.session_state[state_key] = value
            except (ValueError, TypeError):
                pass
    st.session_state["permalink_loaded"] = True


def sync_query_params(n_types, roll_width, max_demand, seed):
    try:
        st.query_params["n"] = str(int(n_types))
        st.query_params["w"] = str(int(roll_width))
        st.query_params["d"] = str(int(max_demand))
        st.query_params["seed"] = str(int(seed))
    except Exception:
        pass


def apply_preset(name):
    p = C.PRESETS[name]
    st.session_state["n_types_slider"] = p["n_types"]
    st.session_state["roll_width_slider"] = p["roll_width"]
    st.session_state["max_demand_slider"] = p["max_demand"]
    st.session_state["seed_input"] = p["seed"]
    st.session_state["force_regen"] = True


def randomize_seed():
    st.session_state["seed_input"] = random.randint(0, 2_000_000_000)
    st.session_state["force_regen"] = True
