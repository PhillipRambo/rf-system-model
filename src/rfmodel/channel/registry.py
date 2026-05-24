from __future__ import annotations
import numpy as np

from rfmodel.core.factory import register_block, build_block
from rfmodel.channel.AWGN import AWGNBlock, AWGNParams
from rfmodel.channel.path_loss import PathLossBlock, PathLossParams
from rfmodel.channel.channel import ChannelBlock


@register_block("channel")
def _build_channel(cfg: dict) -> ChannelBlock:
    name = cfg["name"]
    block_cfgs = cfg.get("blocks", [])

    blocks = [build_block(bcfg) for bcfg in block_cfgs]
    return ChannelBlock(name=name, blocks=blocks)


@register_block("awgn")
def _build_awgn(cfg: dict) -> AWGNBlock:
    name = cfg["name"]
    seed = cfg.get("seed", None)
    p    = cfg.get("params", {})

    thermal = bool(p.get("thermal_noise", False))
    params  = AWGNParams(
        snr_db        = float(p.get("snr_db", 0.0)),
        thermal_noise = thermal,
        temp_k        = float(p.get("temp_k", 290.0)),
    )
    return AWGNBlock(name=name, params=params, seed=seed)


@register_block("pathloss")
def _build_pathloss(cfg: dict) -> PathLossBlock:
    name = cfg["name"]
    p = cfg.get("params", {})

    params = PathLossParams(
        freq_hz=float(p["freq_hz"]),
        distance_m=float(p["distance_m"]),
        tx_ant_gain_db=float(p.get("tx_ant_gain_db", 0.0)),
        rx_ant_gain_db=float(p.get("rx_ant_gain_db", 0.0)),
    )
    return PathLossBlock(name=name, params=params)