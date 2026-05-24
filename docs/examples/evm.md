# EVM Verification

Measures the RMS Error Vector Magnitude of the received constellation under realistic RF impairments. The notebook produces four results:

1. **TX EVM (after the PA)** — isolates the TX-side contribution to constellation error (PLL phase noise + PA nonlinearity), independent of the RX chain
2. **Full-chain EVM** — TX + channel + RX, the operational figure of merit
3. **EVM vs PLL parameters** — 2-D sweep over **VCO phase noise at 1 MHz offset** and **PLL loop bandwidth**, averaged over multiple phase-noise realisations to reduce Monte-Carlo variance
4. **EVM vs I/Q imbalance** — 2-D sweep over **amplitude imbalance** (Q vs I, in dB) and **phase imbalance** (degrees), using the standard $y = K_1 x + K_2 x^*$ complex-baseband model

A single-point I/Q imbalance cell at the end lets you read off the EVM penalty for a chosen imbalance pair against the balanced reference.

```{note}
The PLL caches its noise coefficient at construction time, so the sweep rebuilds the PLL on each grid point rather than mutating `params.pll.VCO_Phase_Noise_dBc` in place.
```

**Key checks:**
- TX EVM is dominated by phase noise at low input power and by PA compression near P1dB
- Tightening the loop bandwidth lowers EVM only up to the point where reference-noise dominates
- I/Q imbalance EVM matches the analytical floor for known $(\varepsilon, \theta)$ pairs

## Pipeline configuration

```{literalinclude} ../../verification/Tx_channel_Rx.yaml
:language: yaml
```
