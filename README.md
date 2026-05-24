# rf-system-model

A Python package for behavioural simulation of RF signal chains with integrated PLL phase noise modelling. Designed for end-to-end analysis of wireless communication systems at the complex baseband level — from RF front-end impairments to EVM and BER.

## What it does

- **RF front-end** — LNA, PA (Rapp and cubic models), Mixer with configurable gain, nonlinearity (IIP3 / IIP2), and noise figure
- **PLL phase noise** — two-region model (reference + VCO noise) shaped by the loop filter, with optional OFDM subcarrier weighting and far-from-carrier VCO floor
- **Channel** — AWGN (SNR mode or fixed $kTB$ thermal mode) and free-space path loss (Friis equation)
- **Communications** — PRBS bit generation, Gray-coded QAM (4–256-QAM), OFDM modulation/demodulation
- **Measurement** — spectrum analysis, phase noise curves, EVM, BER
- **Flexible pipelines** — build signal chains from YAML or Python; tap, swap, or disable blocks at runtime

## Installation

Requires Python >= 3.10.

```bash
git clone https://github.com/PhillipRambo/rf-system-model.git
cd rf-system-model
pip install -e .
```

Dependencies: `numpy`, `matplotlib`, `pyyaml`, `scipy`

## Quick start

```python
import numpy as np

from rfmodel.core.config import load_yaml
from rfmodel.core.pipeline_builder import pipeline_from_config
from rfmodel.core.signal import Signal

# Importing the registries registers the built-in RF and channel block types
import rfmodel.rf.registry        # noqa: F401  (registers: lna, pa, mixer)
import rfmodel.channel.registry   # noqa: F401  (registers: awgn, pathloss, channel)

cfg  = load_yaml("verification/Tx_channel_Rx.yaml")
pipe = pipeline_from_config(cfg)

fs = 20e6
t  = np.arange(4096) / fs
x  = np.exp(1j * 2 * np.pi * 100e3 * t)

sig_in        = Signal(x=x, fs_hz=fs, fc_hz=5e9, meta={})
sig_out, taps = pipe.run(sig_in, taps=["LNA", "PA_TX"])
```

The communications blocks (PRBS, QAM, OFDM) are used programmatically rather than from YAML — see `verification/tx_setup.py` (`build_test_setup()`) for a complete TX → channel → RX setup that combines an OFDM payload with a YAML-loaded RF pipeline, and the notebooks under `verification/` for the system-level verification flow built on top of it.

## Repository layout

```
src/rfmodel/         Package source (core, rf, channel, comms, meas, plot_utils)
configs/             Example YAML pipeline configs
test_benches/        Per-block verification notebooks (LNA, PA, Mixer, PLL, OFDM, ...)
verification/        System-level verification notebooks (BER, EVM, Link Budget, Signal Generation Demo)
docs/                Jupyter Book sources (rendered to the documentation site)
```

## Running the verification notebooks

The four notebooks under `verification/` share a common setup helper (`tx_setup.py`) that builds the OFDM payload and instantiates the TX → channel → RX pipeline from `Tx_channel_Rx.yaml`:

- **`Signal_Generation_Demo.ipynb`** — step-by-step walkthrough of bit / QAM / OFDM / pipeline construction (start here)
- **`Link_Budget.ipynb`** — analytical vs simulated power at every tap, plus an input-power sweep
- **`EVM.ipynb`** — TX and full-chain EVM, with 2-D sweeps over PLL parameters and I/Q imbalance
- **`BER.ipynb`** — BER vs Eb/N0, chip-input sensitivity, and bench-test (kTB-floor) sensitivity

## Documentation

Full documentation — including the core framework, all components, and annotated example notebooks — is available at:

**[https://philliprambo.github.io/rf-system-model/](https://philliprambo.github.io/rf-system-model/)**

To build the docs locally:

```bash
pip install jupyter-book==0.15.1
jupyter-book build .
# open _build/html/index.html
```

## Running tests

```bash
pytest src/rfmodel/test/
```

## Contact

Phillip Rambo — phillipfbp@gmail.com
