"""Offline comparison and recovery summary; never instantiates a network."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def main():
    old = json.loads((ROOT/'results/learning_track_preflight/telemetry.json').read_text())
    out = ROOT/'results/learning_track_preflight_v2'
    rows = json.loads((out/'telemetry.json').read_text())
    fields = ('time_s', 'total_spikes', 'ppl1_spikes', 'mean_population_hz', 'voltage_range_v')
    same = len(rows) >= len(old) and all(all(a[k] == b[k] for k in fields) for a, b in zip(old, rows))
    # Counts at t cover (t-5ms, t]; rates at t are for the NEXT step.
    baseline = [r for r in rows if r['time_s'] <= .25]
    odor = [r for r in rows if .25 < r['time_s'] <= .5]
    recovery = [r for r in rows if r['time_s'] > .5]
    last_active = max((r['time_s'] for r in rows if r['total_spikes']), default=0.)
    report = dict(
        analysis_neural_steps=0, historical_prefix_identical=same,
        historical_observations_compared=len(old),
        baseline_total_spikes=sum(r['total_spikes'] for r in baseline),
        odor_mbon01_spikes=sum(r['mbon01_spikes'] for r in odor),
        recovery_mbon01_spikes=sum(r['mbon01_spikes'] for r in recovery),
        recovery_total_spikes=sum(r['total_spikes'] for r in recovery),
        last_active_interval_end_s=last_active,
        final_contiguous_quiet_duration_s=round(rows[-1]['time_s']-last_active, 9),
        max_population_hz=max(r['mean_population_hz'] for r in rows),
        total_ppl1_spikes=sum(r['ppl1_spikes'] for r in rows),
        total_ppl1_spikes_with_enabled_route=sum(r['ppl1_spikes_with_enabled_route'] for r in rows),
        voltage_range_v=[min(r['voltage_range_v'][0] for r in rows),
                         max(r['voltage_range_v'][1] for r in rows)],
        full_checkpoint_bytes=(out/'network_state.pkl').stat().st_size,
        checkpoint_note='Brian2 Network.store file present; no neural restore/re-exposure performed',
        learning_demonstrated=False, subjective_welfare='not established')
    (out/'offline_summary.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__': main()
