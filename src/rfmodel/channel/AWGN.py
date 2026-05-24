# src/rfmodel/channel/awgn.py
from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np

from rfmodel.core.random import get_rng
from rfmodel.core.signal import Signal
from rfmodel.core.block import Block

_k_B = 1.380649e-23  # Boltzmann constant [J/K]


@dataclass
class AWGNParams:
    snr_db: float = 0.0
    thermal_noise: bool = False  # if True, fix noise power to kTB (ignores snr_db)
    temp_k: float = 290.0        # noise temperature [K], used when thermal_noise=True


class AWGNBlock(Block):
    """
    Complex-baseband AWGN channel.

    Two modes, selected by AWGNParams.thermal_noise:

    SNR mode (thermal_noise=False, default)
        Noise power tracks the input signal:  Pn = Ps / 10^(snr_db/10)
        Suitable for sweeping SNR independently of signal level.

    Thermal mode (thermal_noise=True)
        Noise power is fixed at the Johnson-Nyquist floor:
            Pn = k * temp_k * fs_hz
        where fs_hz comes from the Signal metadata.
        This models a matched source/cable at temperature temp_k — the noise
        is independent of signal level, so SNR changes across a power sweep.
        snr_db is ignored in this mode.
    """

    type_name = "awgn"

    def __init__(self, name: str, params: AWGNParams, seed: int | None = None):
        super().__init__(name=name)
        self.params = params
        self._rng = get_rng(seed)

    def process(self, s: Signal) -> Signal:
        p = self.params
        x = s.x

        if p.thermal_noise:
            # Fixed thermal noise floor: kTB over the complex-baseband bandwidth
            Pn = _k_B * p.temp_k * s.fs_hz
        else:
            # Fixed SNR ratio relative to instantaneous signal power
            Ps = np.mean(np.abs(x) ** 2)
            Pn = Ps / 10.0 ** (p.snr_db / 10.0)

        # Complex Gaussian: E[|n|^2] = 2*sigma^2  =>  sigma = sqrt(Pn/2)
        sigma = np.sqrt(Pn / 2.0)
        n = (
            self._rng.normal(0.0, sigma, size=x.shape)
            + 1j * self._rng.normal(0.0, sigma, size=x.shape)
        )

        return s.copy_with(x=x + n)
    
