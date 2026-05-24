from __future__ import annotations
from dataclasses import dataclass
import numpy as np

from rfmodel.core.units import db_to_linear, dbm_to_w
from rfmodel.core.random import get_rng
from rfmodel.core.signal import Signal
from rfmodel.core.block import Block

@dataclass
class PLLParams:
    VCO_Phase_Noise_dBc: tuple[float, float] # Takes phase noise in dBc at offset frequency [PN,f_offset]
    SLF_dBc: float #Low frequency noise floor
    f_L: float #Loop Bandwidth
    Tu: float  # OFDM usefull length of symbol length, i.e length of FFT interval
    enable_ofdm_weighting: bool = False #flag to enable OFDM weighting function
    f_range_limits: tuple[float, float] = (10, 1e10) # offset frequencies to evaluate the Phase noise over
    vco_noise_floor_dbc: float | None = None  # far-from-carrier VCO thermal floor; None = disabled

class PLL:
    def __init__(self, params: PLLParams, rng):
        self.p = params
        self._rng = rng
        self.alpha = 10**(float(self.p.VCO_Phase_Noise_dBc[0]) / 10) * (float(self.p.VCO_Phase_Noise_dBc[1]))**2
        self.SLF = 10**(self.p.SLF_dBc / 10)
        self.VCO_floor = 10**(self.p.vco_noise_floor_dbc / 10) if self.p.vco_noise_floor_dbc is not None else 0.0
        if self.p.enable_ofdm_weighting and not self.p.Tu:
            raise ValueError("PLLParams: Tu must be set (> 0) when enable_ofdm_weighting=True")

    def get_psd(self, f: np.ndarray) -> np.ndarray:
        f_L = self.p.f_L
        
        # Avoid division by zero at f=0
        f_safe = np.where(f == 0, np.finfo(float).eps, f)
        
        lp_factor = 1 / (1 + (f_safe / f_L)**2)   # low-pass: reference noise
        hp_factor = (f_safe / f_L)**2 / (1 + (f_safe / f_L)**2)  # high-pass: VCO noise
        
        S_phi = self.SLF * lp_factor + (self.alpha / f_safe**2) * hp_factor + self.VCO_floor
        
        if self.p.enable_ofdm_weighting:
            denom = (np.pi * f_safe * self.p.Tu)**2
            h_bbf = 1 - np.divide(
                np.sin(np.pi * f_safe * self.p.Tu)**2,
                denom,
                out=np.zeros_like(f_safe),
                where=denom != 0
            )
            S_phi *= h_bbf
            
        return S_phi

    def generate_lo_impairment(self, N: int, fs: float) -> np.ndarray:
        """Generates a time-domain phasor e^(j*phi(t)) with modeled phase noise."""
        df = fs / N
        f = np.fft.rfftfreq(N, 1/fs)
        
        #Get the PSD for these specific frequencies
        S_phi = self.get_psd(f)

        #Convert PSD to frequency-domain noise (amplitude scaling)
        phi_f = (self._rng.standard_normal(len(f)) + 1j * self._rng.standard_normal(len(f)))
        phi_f *= np.sqrt(S_phi * df) * (N / 2)
        phi_f[0] = 0.0  # zero DC: a constant phase offset has no physical meaning

        phi_t = np.fft.irfft(phi_f, n=N)
        
        #Return the LO phasor
        return np.exp(1j * phi_t)

@dataclass
class MixerParams:
    gain_db: float
    iip3_dbm: float
    nf_db: float
    temp_k: float = 290.0
    iip2_dbm: float | None = None
    pll: PLLParams | None = None
    mixer_ideal: bool = False

class MixerBlock(Block):
    type_name = "mixer"

    def __init__(self, name: str, params: MixerParams, seed: int | None = None):
        super().__init__(name=name)
        self.params = params
        self._rng = get_rng(seed)
        if self.params.pll is not None:
            self.pll = PLL(self.params.pll, self._rng)
        else:
            self.pll = None
    def process(self, s: Signal) -> Signal:
        p = self.params
        x = s.x
        
        if self.pll:
            lo_signal = self.pll.generate_lo_impairment(len(x), s.fs_hz) # create PLL impariments if PLL is enabled
            x = x * lo_signal

        if p.mixer_ideal:
            return s.copy_with(x=x) # just skip the next stages
            

        G = db_to_linear(p.gain_db)
        alpha_lin = np.sqrt(G)

        beta = alpha_lin / (2.0 * dbm_to_w(p.iip3_dbm))
        y = alpha_lin * x - beta * (np.abs(x)**2) * x

        if p.iip2_dbm is not None:
            a2 = alpha_lin / np.sqrt(2.0 * dbm_to_w(p.iip2_dbm))
            y += a2 * x**2

        # Noise stage
        F = db_to_linear(p.nf_db)
        k = 1.380649e-23

        noise_psd_w_per_hz = (F - 1.0) * k * p.temp_k * G
        B_hz = s.fs_hz / 2.0
        Pn_out_added_w = noise_psd_w_per_hz * B_hz

        sigma = np.sqrt(Pn_out_added_w / 2.0)
        n = (
            self._rng.normal(0.0, sigma, size=y.shape)
            + 1j * self._rng.normal(0.0, sigma, size=y.shape)
        )
        y_final = y + n



        return s.copy_with(x=y_final)
    