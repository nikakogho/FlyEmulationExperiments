"""Scientific figures and counterbalanced analysis from saved runs only."""
import json
from pathlib import Path
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flygym.vision import Retina
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from flyplasticity.retinal_bridge import RetinalBridge
from flyplasticity.spectral import CHANNELS

out = ROOT/'results/spectral_summary'
out.mkdir(exist_ok=True)
data = np.load(ROOT/'data/spectral/receptor_curves.npz')
fig, ax = plt.subplots(figsize=(8, 4), layout='constrained')
for c, name in enumerate(CHANNELS):
    ax.plot(data['wavelength_nm'], data['response'][:, c], label=name, lw=2)
ax.set(xlabel='Wavelength (nm)', ylabel='Relative response (band-normalized)',
       title='Measured receptor response shapes used by the model')
ax.legend(ncol=5)
fig.savefig(out/'response_curves.png', dpi=160)
plt.close(fig)

eye = Retina()
centers = np.array(json.loads((ROOT/'results/visual_learning_path/flyvis_receptor_centers.json').read_text()))
bridge = RetinalBridge(eye.ommatidia_id_map, centers)
record = np.load(ROOT/'results/spectral_scene/retinal_inputs.npz')
fig, axs = plt.subplots(3, 3, figsize=(10, 6), layout='constrained')
for row, cue in enumerate(('365', '450', '525')):
    for col, channel in enumerate(('R1-R6', 'R7 (UV subtypes)', 'R8 (blue/green mosaic)')):
        images = [eye.hex_pxls_to_human_readable(record[cue][side, bridge.to_source, col]) for side in (0, 1)]
        axs[row, col].imshow(np.concatenate(images, axis=1), cmap='magma', vmin=0, vmax=1)
        axs[row, col].set_title(f'{cue} nm | {channel}', fontsize=10)
        axs[row, col].axis('off')
fig.suptitle('Actual 3D eye inputs: left and right eye in each panel\nFalse-colour display of relative excitation; display colours are not sensory inputs')
fig.savefig(out/'retinal_channels.png', dpi=160)
plt.close(fig)

conditions = {'365':'spectral_memory_uv', '450':'spectral_memory', '525':'spectral_memory_green'}
matrices, fractions = [], []
for seed in (201, 202, 203):
    matrix, fractional = [], []
    for cue, folder in conditions.items():
        rows = json.loads((ROOT/f'results/{folder}/checks.json').read_text())['rows']
        lookup = {r['condition']:r['reward_free_mbon_hz'] for r in rows if r['seed']==seed}
        paired = np.array([lookup['paired'][c] for c in conditions])
        frozen = np.array([lookup['frozen'][c] for c in conditions])
        matrix.append(frozen-paired)
        fractional.append((frozen-paired)/frozen)
    matrices.append(matrix)
    fractions.append(fractional)
matrices, fractions = np.array(matrices), np.array(fractions)
# Counterbalanced preference: training A rather than B must shift the A-vs-B
# fractional suppression toward A. No behavior or p-value follows from this.
pairs = []
for a in range(3):
    for b in range(a+1, 3):
        interaction = fractions[:, a, a]-fractions[:, a, b]-fractions[:, b, a]+fractions[:, b, b]
        pairs.append(dict(cues_nm=[list(conditions)[a], list(conditions)[b]],
                          fractional_interaction_by_seed=interaction.tolist(),
                          positive_all_seeds=bool(np.all(interaction > 0))))
result = dict(seeds=[201,202,203], trained_cues_nm=list(conditions),
    mean_mbon_reduction_hz=matrices.mean(axis=0).tolist(),
    mean_fractional_reduction=fractions.mean(axis=0).tolist(),
    paired_cue_largest_fractional_effect_each_seed=[bool(np.all(np.argmax(fractions[:,i,:], axis=1)==i)) for i in range(3)],
    counterbalanced_interactions=pairs, improved_plasticity_demonstrated=False,
    embodied_learning_demonstrated=False,
    interpretation='Suppression includes generalization. Positive counterbalanced interaction indicates stimulus-dependent plasticity in this engineered adapter, not learned navigation or validated biological accuracy.')
(out/'checks.json').write_text(json.dumps(result, indent=2))
fig, axs = plt.subplots(1, 2, figsize=(9, 4), layout='constrained')
for ax, values, title in zip(axs, [matrices.mean(axis=0), fractions.mean(axis=0)*100],
                             ['Response reduction (Hz)', 'Response reduction (%)']):
    im = ax.imshow(values, cmap='Blues', vmin=0)
    ax.set(xticks=range(3), yticks=range(3), xticklabels=['UV','Blue','Green'],
           yticklabels=['UV','Blue','Green'], xlabel='Test cue', ylabel='Trained cue', title=title)
    for i in range(3):
        for j in range(3): ax.text(j, i, f'{values[i,j]:.1f}', ha='center', va='center',
                                  color='white' if values[i,j] > values.max()*.65 else 'black')
    fig.colorbar(im, ax=ax, shrink=.75)
fig.suptitle('Paired versus frozen plasticity: mean of three fixed seeds\nStationary neural probe; no navigation result')
fig.savefig(out/'memory_generalization.png', dpi=160)
plt.close(fig)
print(json.dumps(result, indent=2))
