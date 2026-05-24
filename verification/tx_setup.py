"""Shared input generation and pipeline setup for the performance-verification notebooks.

Usage
-----
    from tx_setup import build_test_setup
    setup = build_test_setup(input_pwr_dbm=-30)

`setup` is a dataclass with the bits, QAM symbols, OFDM signal scaled to the
requested input power, the QAM/OFDM modulators, and the configured pipeline.
"""

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from rfmodel.core.signal import Signal
from rfmodel.core.pipeline_builder import pipeline_from_config
from rfmodel.core.config import load_yaml
from rfmodel.core.units import dbm_to_w
from rfmodel.comms.pseudorandom_NGR import PRBSBitSource, PRBSParams
from rfmodel.comms.QAM_modulator import QAMModulator, QAMParams
from rfmodel.comms.OFDM_block import OFDMModulator, OFDMParams

import rfmodel.rf.registry  # noqa: F401  (register RF blocks)
import rfmodel.channel.registry  # noqa: F401  (register channel blocks)


DEFAULT_YAML = Path(__file__).parent / "Tx_channel_Rx.yaml"


@dataclass
class TestSetup:
    cfg: dict
    pipe: object
    qam: QAMModulator
    ofdm: OFDMModulator
    bits: np.ndarray
    sig_bits: Signal
    qam_symbols: np.ndarray
    sig_ofdm: Signal              # OFDM signal at native (unit-average) power
    sig_ofdm_normalized: Signal   # OFDM signal scaled to input_pwr_dbm
    input_pwr_dbm: float
    M: int
    bits_per_symbol: int
    fs_hz: float
    n_fft: int
    cp_len: int
    n_data_subcarriers: int
    num_ofdm_symbols: int


def build_test_setup(
    input_pwr_dbm: float = -30.0,
    M: int = 64,
    fs_hz: float = 20e6,
    n_fft: int = 64,
    cp_len: int = 16,
    n_data_subcarriers: int = 52,
    num_ofdm_symbols: int = 64,
    yaml_path: str | Path = DEFAULT_YAML,
    enable_ofdm_weighting: bool = False,
) -> TestSetup:
    """Generate the OFDM test signal and build the RF pipeline.

    Parameters mirror the original `Performance_Verification.ipynb` defaults.
    """
    bits_per_symbol = int(np.log2(M))
    n_qam_symbols_transmitted = num_ofdm_symbols * n_data_subcarriers

    # --- Bits ---------------------------------------------------------------
    dummy_sig = Signal(
        x=np.array([], dtype=np.uint8),
        fs_hz=fs_hz,
        meta={"name": "PRBS15 Input Bits"},
    )
    prbs_gen = PRBSBitSource(
        name="tx_bits",
        params=PRBSParams(
            order=15,
            n_bits=n_qam_symbols_transmitted * bits_per_symbol,
            seed=123,
        ),
    )
    sig_bits = prbs_gen.process(dummy_sig)

    # --- QAM ----------------------------------------------------------------
    qam = QAMModulator(
        "qam1",
        QAMParams(M=M, gray_map=True, unit_average_power=True),
    )
    sig_qam = qam.process(sig_bits)

    # --- OFDM ---------------------------------------------------------------
    ofdm = OFDMModulator(
        "ofdm1",
        OFDMParams(
            n_fft=n_fft,
            cp_len=cp_len,
            n_data_subcarriers=n_data_subcarriers,
            normalize_ifft=True,
            null_dc=True,
        ),
    )
    sig_ofdm = ofdm.process(sig_qam)

    # --- Scale to target input power ---------------------------------------
    current_w = np.mean(np.abs(sig_ofdm.x) ** 2)
    target_w = dbm_to_w(input_pwr_dbm)
    scaling_factor = np.sqrt(target_w / current_w)
    sig_ofdm_normalized = sig_ofdm.copy_with(x=sig_ofdm.x * scaling_factor)

    # --- Pipeline -----------------------------------------------------------
    cfg = load_yaml(str(yaml_path))
    pipe = pipeline_from_config(cfg)

    Tu = n_fft / fs_hz

    mixer_tx = pipe.get("mixer_and_pll_TX")
    mixer_tx.params.mixer_ideal = False
    mixer_tx.params.pll.Tu = Tu
    mixer_tx.params.pll.enable_ofdm_weighting = enable_ofdm_weighting

    mixer_rx = pipe.get("mixer_and_pll_RX")
    mixer_rx.params.mixer_ideal = False
    mixer_rx.params.pll.Tu = Tu
    mixer_rx.params.pll.enable_ofdm_weighting = enable_ofdm_weighting

    return TestSetup(
        cfg=cfg,
        pipe=pipe,
        qam=qam,
        ofdm=ofdm,
        bits=sig_bits.x,
        sig_bits=sig_bits,
        qam_symbols=sig_qam.x,
        sig_ofdm=sig_ofdm,
        sig_ofdm_normalized=sig_ofdm_normalized,
        input_pwr_dbm=input_pwr_dbm,
        M=M,
        bits_per_symbol=bits_per_symbol,
        fs_hz=fs_hz,
        n_fft=n_fft,
        cp_len=cp_len,
        n_data_subcarriers=n_data_subcarriers,
        num_ofdm_symbols=num_ofdm_symbols,
    )
