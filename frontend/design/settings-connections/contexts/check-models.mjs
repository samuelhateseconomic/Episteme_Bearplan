import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

// Pure interpreter of captured, installed Figma actions. No Figma or provider writes.
const dir = dirname(fileURLToPath(import.meta.url));
const read = name => JSON.parse(readFileSync(join(dir, name), 'utf8'));
const inv = read('inventory.json');
const sources = read('sources.json');
const audit = read('audit.json');
const previous = read('previous-recovery-fingerprints.json');
const variables = read('variables.json');
const tokenIds = inv.isolatedVariableIds;
const originIds = inv.originVariableIds;
const allowed = new Set([...Object.values(tokenIds), ...Object.values(originIds)]);
const results = [];
function check(name, condition) {
  results.push({ name, pass: !!condition });
  if (!condition) throw new Error(name);
}
function value(v, state) {
  if (v.type === 'VARIABLE_ALIAS') return state.get(v.value.id);
  if (v.type === 'EXPRESSION') {
    const args = v.value.expressionArguments.map(a => value(a, state));
    if (v.value.expressionFunction === 'EQUALS') return args[0] === args[1];
    throw new Error('Unsupported expression');
  }
  return v.value;
}
function runActions(actions, state, receipt) {
  for (const a of actions) {
    if (a.type === 'SET_VARIABLE') state.set(a.variableId, value(a.variableValue, state));
    else if (a.type === 'NODE') receipt.destination = a.destinationId;
    else if (a.type === 'CONDITIONAL') {
      const block = a.conditionalBlocks.find(b => !b.condition || value(b.condition, state));
      if (block) runActions(block.actions, state, receipt);
    } else throw new Error('Unexpected action ' + a.type);
  }
}
function click(source, state) {
  const reaction = source.reactions.find(r => r.trigger.type === 'ON_CLICK');
  if (!reaction) throw new Error('Missing click ' + source.id);
  const receipt = {};
  runActions(reaction.actions, state, receipt);
  return receipt.destination;
}
function find(owner, name) {
  const matches = sources.filter(s => s.owner === owner && s.name === name);
  if (matches.length !== 1) throw new Error(`Expected one ${name} in ${owner}; got ${matches.length}`);
  return matches[0];
}
function inspectActions(actions, laneFrames) {
  for (const a of actions) {
    if (a.type === 'SET_VARIABLE') {
      if (!allowed.has(a.variableId)) throw new Error('Writes outside isolated context state');
    } else if (a.type === 'NODE') {
      if (!laneFrames.has(a.destinationId)) throw new Error('Context escaped its lane');
    } else if (a.type === 'CONDITIONAL') {
      for (const b of a.conditionalBlocks) inspectActions(b.actions, laneFrames);
    } else throw new Error('Unexpected context action');
  }
}

check('Prior recovery sources retain all 145 installed reaction fingerprints', previous.current.length === 145 && previous.differences.length === 0);
check('All context snapshots and guide stay editable', !audit.structure.raster.length && audit.structure.types.TEXT > 0 && audit.structure.types.INSTANCE > 0);
check('No frame overflow, overlap or missing/wrong font findings', !audit.structure.overflow.length && !audit.structure.overlap.length && !audit.structure.fonts.length && !audit.guide.issues.length);

for (let i = 0; i < inv.lanes.length; i++) {
  const lane = inv.lanes[i], f = lane.frames, prefix = lane.config.label + ': ';
  const state = new Map(variables.map(v => [v.id, Object.values(v.values)[0]]));
  const base = JSON.stringify([...state]);
  const own = sources.filter(s => Object.values(f).some(r => r.id === s.owner));
  for (const s of own) for (const r of s.reactions) inspectActions(r.actions, new Set(Object.values(f).map(r => r.id)));
  check(prefix + 'all installed controls stay within their lane and allowed state', own.length === 44);
  check(prefix + 'no inherited task/session/history bindings remain', audit.states[i].oldBindings.length === 0);
  check(prefix + 'Settings opens from Today', click(find(f.work.id, 'Action / Open Settings'), state) === f.overview.id);
  check(prefix + 'opening Settings preserves the token sample', JSON.stringify([...state]) === base);
  check(prefix + 'bCourses management opens', click(find(f.overview.id, 'Action / Manage bCourses'), state) === f.bcourses.id);
  check(prefix + 'removal starts with a preview', click(find(f.bcourses.id, 'Action / Remove bCourses token'), state) === f.remove.id && state.get(tokenIds[i]) === 'Token saved');
  check(prefix + 'Keep token cancels without changing sample state', click(find(f.remove.id, 'Action / Keep token'), state) === f.bcourses.id && JSON.stringify([...state]) === base);
  click(find(f.bcourses.id, 'Action / Remove bCourses token'), state);
  check(prefix + 'only explicit confirmation changes token sample', click(find(f.remove.id, 'Action / Remove token'), state) === f.removed.id && state.get(tokenIds[i]) === 'Token not saved');
  check(prefix + 'confirmation leaves all other lanes untouched', [...state].every(([id,v]) => id === tokenIds[i] || v === (Object.values(originIds).includes(id) ? 'work' : 'Token saved')));
  check(prefix + 'Close keeps the removal result', click(find(f.removed.id, 'Action / Close'), state) === f.bcourses.id && state.get(tokenIds[i]) === 'Token not saved');
  check(prefix + 'Back to work returns to the same Today frame', click(find(f.bcourses.id, 'Action / Back to work'), state) === f.work.id);
  check(prefix + 'Open timer returns to the paused Track sample', click(find(f.work.id, 'Action / Open timer'), state) === f.track.id);
  check(prefix + 'Settings from Track records Track origin', click(find(f.track.id, 'Action / Open Settings'), state) === f.overview.id && state.get(originIds[i]) === 'track');
  check(prefix + 'Back to work restores Track origin', click(find(f.overview.id, 'Action / Back to work'), state) === f.track.id);
  click(find(f.track.id, 'Action / Open Settings'), state);
  check(prefix + 'Settings gear also restores Track origin', click(find(f.overview.id, 'Action / Close Settings'), state) === f.track.id);
  click(find(f.track.id, 'Action / Open Settings'), state);
  check(prefix + 'Google management opens without changing token sample', click(find(f.overview.id, 'Action / Manage Google'), state) === f.google.id && state.get(tokenIds[i]) === 'Token not saved');
  check(prefix + 'Google scope opens explicitly', click(find(f.google.id, 'Action / Sign-in & calendars'), state) === f.consent.id);
  check(prefix + 'Not now keeps context and token sample', click(find(f.consent.id, 'Action / Not now'), state) === f.google.id && state.get(originIds[i]) === 'track' && state.get(tokenIds[i]) === 'Token not saved');
  check(prefix + 'offline exits restore originating Track sample', sources.filter(s => s.owner === f.offline.id && s.name === 'Action / Back to work').every(s => click(s, state) === f.track.id));
  const starts = inv.guide.buttons.filter(b => b.seed === tokenIds[i]);
  for (const b of starts) {
    const source = sources.find(s => s.id === b.id);
    check(prefix + b.label + ' resets only this lane', click(source, state) === b.destination && state.get(tokenIds[i]) === 'Token saved' && state.get(originIds[i]) === 'work');
  }
  const states = audit.states[i].states;
  check(prefix + 'offline policy remains separate from retained last success', states.find(s => s.key === 'offline').googlePolicy === 'Paused · Google unavailable' && states.find(s => s.key === 'offline').googleLast === 'Last complete sync: Nov 3 at 9:41 AM');
  check(prefix + 'other Settings examples show automatic policy', states.filter(s => s.googlePolicy && s.key !== 'offline').every(s => s.googlePolicy === 'Automatic sync on'));
  const snapshots = audit.snapshots.filter(s => s.id === f.work.id || s.id === f.track.id);
  check(prefix + 'Today and Track retain the same paused Read sample', snapshots.length === 2 && snapshots.every(s => s.texts.some(t => t.text === 'Read the primary source')) && snapshots.some(s => s.texts.some(t => t.text === 'Paused · 18:00 remaining')) && snapshots.some(s => s.texts.some(t => t.text === '18:00')));
  const roots = audit.structure.lanes.filter(r => Object.values(f).some(s => s.id === r.root));
  check(prefix + 'actual dimensions and semantic theme match', roots.length === 9 && roots.every(r => r.width === lane.config.w && r.height === lane.config.h && r.mode['VariableCollectionId:2:8'] === lane.config.mode));
  const bc = roots.find(r => r.root === f.bcourses.id);
  check(prefix + 'long management content keeps an explicit vertical scroll area', bc.scroll.overflow === 'VERTICAL' && bc.scroll.contentHeight > 0);
}

const result = { passed: results.filter(r => r.pass).length, failed: results.filter(r => !r.pass).length, checks: results, limitation: 'Interprets installed finite reactions and static audits; does not click presentation or test real storage, resizing, keyboard, timer or provider behavior.' };
if (process.argv.includes('--write')) writeFileSync(join(dir, 'models.json'), JSON.stringify(result, null, 2) + '\n');
console.log(`${result.passed} passed, ${result.failed} failed`);
