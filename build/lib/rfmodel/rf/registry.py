from __future__ import annotations
import numpy as np

from rfmodel.core.factory import register_block
from rfmodel.rf.LNA import LNABlock, LNAParams
from rfmodel.rf.PA import PABlock, PAParams
from rfmodel.rf.Mixer_PLL_block import MixerBlock, MixerParams, PLLParams

@register_block("lna")
def _build_lna(cfg: dict) -> LNABlock:
    name = cfg["name"]
    seed = cfg.get("seed", None)
    p = cfg.get("params", {})

    params = LNAParams(
        gain_db=float(p["gain_db"]),
        nf_db=float(p["nf_db"]),
        IP3_dbm=float(p["IP3_dbm"]),
        temp_k=float(p.get("temp_k", 290.0)),
    )
    return LNABlock(name=name, params=params, seed=seed)



@register_block("pa")
def _build_pa(cfg: dict) -> PABlock:
    name = cfg["name"]
    p = cfg.get("params", {})

    params = PAParams(
        gain_db=float(p["gain_db"]),
        p1db_out_dbm=float(p["p1db_out_dbm"]),
        smoothness_p=float(p.get("smoothness_p", 2.0)),
        enable_cubic=bool(p.get("enable_cubic", False)),
    )
    return PABlock(name=name, params=params)

@register_block("mixer")
def _build_mixer(cfg: dict) -> MixerBlock:
    name = cfg["name"]
    seed = cfg.get("seed", None)
    p = cfg.get("params", {})

    # Handle Nested PLL Parameters if they exist in YAML
    pll_cfg = p.get("pll")
    pll_params = None
    if pll_cfg:
        vco_floor_raw = pll_cfg.get("vco_noise_floor")
        pll_params = PLLParams(
            VCO_Phase_Noise_dBc=tuple(pll_cfg.get("VCO_PhaseNoise")),
            SLF_dBc=float(pll_cfg.get("LF_noise_floor")),
            f_L=float(pll_cfg.get("loop_bandwidth")),
            Tu=float(pll_cfg.get("Tu", 0.0)),  # must exist if weighting is used
            enable_ofdm_weighting=bool(pll_cfg.get("enable_ofdm_weighting", False)),
            f_range_limits=tuple(pll_cfg.get("Foffset_Range", (10, 1e10))),
            vco_noise_floor_dbc=float(vco_floor_raw) if vco_floor_raw is not None else None,
        )
    iip2_raw = p.get("iip2_dbm")
    params = MixerParams(
        gain_db=float(p["gain_db"]),
        iip3_dbm=float(p["iip3_dbm"]),
        nf_db=float(p["nf_db"]),
        iip2_dbm=float(iip2_raw) if iip2_raw is not None else None,
        pll=pll_params
    )
    
    return MixerBlock(name=name, params=params, seed=seed)

