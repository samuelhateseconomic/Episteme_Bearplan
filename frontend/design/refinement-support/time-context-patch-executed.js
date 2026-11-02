// CODE-ONLY DRAFT. Root reviews, then prepends refine-helpers.js with PAGE_ID=2:5.
// Finite ONE 12-minute demo save only; not a session ledger or app implementation.
// Run before building Reset: include prototypeVariableDefaults below in Reset.
if (PAGE_ID !== '2:5') throw Error('Time-context pass requires native Canvas page.');
const tcCollection = await figma.variables.getVariableCollectionByIdAsync('VariableCollectionId:9:6181');
const tcMode = tcCollection.modes[0].modeId;
const tcExisting = await figma.variables.getLocalVariablesAsync();
if (tcExisting.some(v => v.name === 'Stats / Last demo saved task'))
  throw Error('Time-context variables already exist; reconcile prior execution before retry.');
const tcNewVariableIds = [], tcDefaults = {};
function tcVar(name, type, value) {
  const v = figma.variables.createVariable('Stats / ' + name, tcCollection, type);
  v.scopes = type === 'STRING' ? ['TEXT_CONTENT'] : ['ALL_SCOPES'];
  v.setValueForMode(tcMode, value); tcNewVariableIds.push(v.id); tcDefaults[v.id] = value; return v;
}
const TC = {
  lastTask: tcVar('Last demo saved task', 'STRING', ''),
  lastContext: tcVar('Last demo saved context', 'STRING', ''),
  lastProject: tcVar('Last demo saved project', 'STRING', ''),
  finishOutputFocus: tcVar('Finish output focus', 'STRING', '57 / 60 min saved today'),
  finishOutputCoins: tcVar('Finish output coins', 'STRING', 'Coins · 45'),
  finishOutputAvailable: tcVar('Finish output available coins', 'STRING', '45 coins available'),
  correctionInput: tcVar('Correction captured focus', 'STRING', ''),
  correctionWalletInput: tcVar('Correction captured wallet', 'STRING', 'Coins · 33'),
  previewInput: tcVar('Correction preview captured focus', 'STRING', ''),
  correctionSession: tcVar('Correction session effect', 'STRING', 'Session time        12 → 10 min'),
  correctionFocus: tcVar('Correction focus effect', 'STRING', 'Saved today          45 → 43 min'),
  correctionCoins: tcVar('Correction coins effect', 'STRING', 'Coin balance         33 → 31'),
  cs: tcVar('CS61A project saved focus', 'STRING', 'CS61A · 4h 08m'),
  econ: tcVar('Economics project saved focus', 'STRING', 'Economics · 3h 10m'),
  extraProject: tcVar('Additional project saved focus', 'STRING', 'Personal · 12 min'),
  extraVisible: tcVar('Additional project visible', 'BOOLEAN', false),
  outline: tcVar('Outline estimate versus saved', 'STRING', '20 min estimated · No saved session in this example'),
};
const tcIds = { focus: 'VariableID:18:4759', selected: 'VariableID:9:6182', context: 'VariableID:9:6183',
  history: 'VariableID:101:5608', readEstimate: 'VariableID:101:5609',
  coins: 'VariableID:18:4760', available: 'VariableID:18:4761',
  total: 'VariableID:101:5605', sessions: 'VariableID:101:5606', week: 'VariableID:101:5607',
  sunday: 'VariableID:101:5610', sundayHeight: 'VariableID:101:5611' };
const TV = {};
for (const [k, id] of Object.entries(tcIds)) {
  TV[k] = await figma.variables.getVariableByIdAsync(id);
  if (!TV[k]) throw Error('Missing time-context input ' + k);
}
function tcLit(value) { const type = typeof value === 'boolean' ? 'BOOLEAN' : typeof value === 'number' ? 'FLOAT' : 'STRING'; return { type, resolvedType: type, value }; }
function tcAlias(v) { return { type: 'VARIABLE_ALIAS', resolvedType: v.resolvedType, value: { type: 'VARIABLE_ALIAS', id: v.id } }; }
function tcEq(v, value) { return { type: 'EXPRESSION', resolvedType: 'BOOLEAN', value: { expressionFunction: 'EQUALS', expressionArguments: [tcAlias(v), tcLit(value)] } }; }
function tcFold(fn, args) {
  if (!args.length) return tcLit(fn === 'AND');
  if (args.length === 1) return args[0];
  const mid = Math.ceil(args.length / 2);
  return { type: 'EXPRESSION', resolvedType: 'BOOLEAN', value: { expressionFunction: fn, expressionArguments: [tcFold(fn, args.slice(0, mid)), tcFold(fn, args.slice(mid))] } };
}
function tcSet(v, value) { return { type: 'SET_VARIABLE', variableId: v.id, variableValue: tcLit(value) }; }
function tcCapture(target, source) { return { type: 'SET_VARIABLE', variableId: target.id, variableValue: tcAlias(source) }; }
function tcIf(condition, actions) { return { type: 'CONDITIONAL', conditionalBlocks: [{ condition, actions }] }; }
const tcContextGroups = {
  history: ['History seminar', 'History seminar / Prepare discussion', 'History seminar / Prepare seminar discussion'],
  cs61a: ['CS61A', 'CS61A / Problem set 6'],
  economics: ['Economics', 'Economics / Problem set 4'],
  personal: ['Personal'],
};
// Original successful Finish writes 57 after45. The corrected baseline43 instead
// finishes to55, preserving its two-minute reduction. Replays at57/55 pass through
// current focus/wallet without re-awarding or erasing a later correction/purchase.
// Find original success recursively, but insert
// captures as FLAT single-IF siblings before its outer conditional. Existing
// leading snapshot actions have already run. Do not add nested IFs or ELSE.
function tcSavePaths(action, guards = []) {
  if (action.type === 'SET_VARIABLE' && action.variableId === TV.focus.id &&
      action.variableValue?.value === '57 / 60 min saved today') return [guards];
  if (action.type !== 'CONDITIONAL') return [];
  const out = [];
  for (const block of action.conditionalBlocks || []) {
    if (!block.condition) {
      // Unrelated navigation/toggle ELSE branches are outside this patch.
      const hasSave = a => a.type === 'SET_VARIABLE' && a.variableId === TV.focus.id && a.variableValue?.value === '57 / 60 min saved today' || a.type === 'CONDITIONAL' && (a.conditionalBlocks || []).some(b => (b.actions || []).some(hasSave));
      if ((block.actions || []).some(hasSave)) throw Error('Finish success has ELSE; reconcile before capture patch.');
      continue;
    }
    for (const child of block.actions || []) out.push(...tcSavePaths(child, guards.concat(block.condition)));
  }
  return out;
}
const tcFinishNodes = [];
function tcRewriteFinish(action) {
  if (action.type === 'SET_VARIABLE') {
    let variable = null;
    if (action.variableId === TV.focus.id && action.variableValue?.value === '57 / 60 min saved today') variable = TC.finishOutputFocus;
    if (action.variableId === TV.coins.id && action.variableValue?.value === 'Coins · 45') variable = TC.finishOutputCoins;
    if (action.variableId === TV.available.id && action.variableValue?.value === '45 coins available') variable = TC.finishOutputAvailable;
    return variable ? { ...action, variableValue: tcAlias(variable) } : action;
  }
  if (action.type === 'CONDITIONAL') return { ...action, conditionalBlocks: action.conditionalBlocks.map(b => ({ ...b, actions: (b.actions || []).map(tcRewriteFinish) })) };
  return action;
}
const tcCandidates=[];for(const id of ["7:2639","7:2686","7:2733","7:2780","7:2827","105:5656","105:5693"]){const root=await figma.getNodeByIdAsync(id);tcCandidates.push(root,...root.findAll(n=>n.type==="INSTANCE"&&/Finish|finish|saved result/.test(n.name)));}
for (const node of tcCandidates) {
  if (!node.reactions?.length) continue;
  let modified = false;
  const reactions = node.reactions.map(reaction => {
    const reactionSaves = (reaction.actions || []).some(action => tcSavePaths(action).length);
    const next = [];
    for (const action of reaction.actions || []) {
      const paths = tcSavePaths(action);
      for (const guards of paths) {
        const allowed = tcFold('AND', guards);
        next.push(tcIf(allowed, [tcCapture(TC.finishOutputFocus, TV.focus), tcCapture(TC.finishOutputCoins, TV.coins), tcCapture(TC.finishOutputAvailable, TV.available)]));
        const unsaved = tcFold('OR', [tcEq(TV.focus, '45 / 60 min saved today'), tcEq(TV.focus, '43 / 60 min saved today')]);
        const guard = tcFold('AND', [...guards, unsaved]);
        next.push(tcIf(guard, [tcCapture(TC.lastTask, TV.selected), tcCapture(TC.lastContext, TV.context), tcSet(TC.lastProject, 'other')]));
        for (const [project, contexts] of Object.entries(tcContextGroups))
          next.push(tcIf(tcFold('AND', [guard, tcFold('OR', contexts.map(c => tcEq(TV.context, c)))]), [tcSet(TC.lastProject, project)]));
        next.push(tcIf(tcFold('AND', [allowed, tcEq(TV.focus, '45 / 60 min saved today')]), [tcSet(TC.finishOutputFocus, '57 / 60 min saved today')]));
        next.push(tcIf(tcFold('AND', [allowed, tcEq(TV.focus, '43 / 60 min saved today')]), [tcSet(TC.finishOutputFocus, '55 / 60 min saved today')]));
        // Four known pre-save balances only: optional Birch debit is preserved.
        // Guards read the unchanged live wallet; only output variables change.
        for (const [before, after] of [[33,45],[3,15],[31,43],[1,13]])
          next.push(tcIf(tcFold('AND', [guard, tcEq(TV.coins, 'Coins · ' + before)]), [tcSet(TC.finishOutputCoins, 'Coins · ' + after), tcSet(TC.finishOutputAvailable, after + ' coins available')]));
        modified = true;
      }
      next.push(reactionSaves ? tcRewriteFinish(action) : action);
    }
    return { ...reaction, actions: next };
  });
  if (modified) { await node.setReactionsAsync(reactions); touch(node); tcFinishNodes.push(node.id); }
}
if (!tcFinishNodes.length) throw Error('No original 45-to-57 Finish success found.');

// Bind existing detail labels, preserving current layout and all-time/week totals.
const tcDetails = await figma.getNodeByIdAsync('7:3121');
const tcCS = await figma.getNodeByIdAsync('7:3199');
const tcEcon = await figma.getNodeByIdAsync('7:3200');
const tcOutline = await figma.getNodeByIdAsync('101:5664');
const tcProjects = await figma.getNodeByIdAsync('7:3197');
for (const [n, v] of [[tcCS, TC.cs], [tcEcon, TC.econ], [tcOutline, TC.outline]]) {
  if (n?.type !== 'TEXT') throw Error('Stats label identity changed; reconcile first.');
  n.setBoundVariable('characters', v); touch(n);
}
const tcExtra = text('Personal · 12 min', 'Context', 'text');
add(tcProjects, tcExtra); tcExtra.textAutoResize = 'HEIGHT';
tcExtra.resize(tcProjects.width - tcProjects.paddingLeft - tcProjects.paddingRight, tcExtra.height);
tcExtra.layoutSizingHorizontal = 'FILL';
tcExtra.setBoundVariable('characters', TC.extraProject);
tcExtra.setBoundVariable('visible', TC.extraVisible); touch(tcExtra);

const tcOwnedOutputs = new Set([TV.history.id, TV.readEstimate.id]);
function tcStripOldAttribution(actions) {
  return (actions || []).flatMap(action => {
    if (action.type === 'SET_VARIABLE' && tcOwnedOutputs.has(action.variableId)) return [];
    if (action.type === 'CONDITIONAL') return [{ ...action, conditionalBlocks: action.conditionalBlocks.map(b => ({ ...b, actions: tcStripOldAttribution(b.actions) })) }];
    return [action];
  });
}
const tcBase = [tcSet(TV.history, 'History seminar · 5h 15m'), tcSet(TV.readEstimate, '30 min estimated · 12 min saved'),
  tcSet(TC.cs, 'CS61A · 4h 08m'), tcSet(TC.econ, 'Economics · 3h 10m'),
  tcSet(TC.outline, '20 min estimated · No saved session in this example'), tcSet(TC.extraVisible, false)];
const tcSaved = tcFold('OR', [tcEq(TV.focus, '57 / 60 min saved today'), tcEq(TV.focus, '55 / 60 min saved today')]);
const tcDerived = [...tcBase,
  tcIf(tcEq(TV.focus, '55 / 60 min saved today'), [tcSet(TV.history, 'History seminar · 5h 13m'), tcSet(TV.readEstimate, '30 min estimated · 10 min saved'), tcSet(TV.total, '12h 43m'), tcSet(TV.sessions, '25'), tcSet(TV.week, 'Oct 26–Nov 1 · 6h 40m saved'), tcSet(TV.sunday, '55m'), tcSet(TV.sundayHeight, 49.5)]),
  tcIf(tcFold('AND', [tcEq(TV.focus, '57 / 60 min saved today'), tcEq(TC.lastProject, 'history')]), [tcSet(TV.history, 'History seminar · 5h 27m')]),
  tcIf(tcFold('AND', [tcEq(TV.focus, '55 / 60 min saved today'), tcEq(TC.lastProject, 'history')]), [tcSet(TV.history, 'History seminar · 5h 25m')]),
  tcIf(tcFold('AND', [tcSaved, tcEq(TC.lastProject, 'cs61a')]), [tcSet(TC.cs, 'CS61A · 4h 20m')]),
  tcIf(tcFold('AND', [tcSaved, tcEq(TC.lastProject, 'economics')]), [tcSet(TC.econ, 'Economics · 3h 22m')]),
  tcIf(tcFold('AND', [tcSaved, tcEq(TC.lastProject, 'personal')]), [tcSet(TC.extraProject, 'Personal · 12 min'), tcSet(TC.extraVisible, true)]),
  // Explicit fallback is a demo limitation, not invented attribution to History.
  tcIf(tcFold('AND', [tcSaved, tcEq(TC.lastProject, 'other')]), [tcSet(TC.extraProject, 'Other demo context · 12 min'), tcSet(TC.extraVisible, true)]),
  tcIf(tcFold('AND', [tcEq(TV.focus, '57 / 60 min saved today'), tcEq(TC.lastTask, 'Read the primary source'), tcEq(TC.lastProject, 'history')]), [tcSet(TV.readEstimate, '30 min estimated · 24 min saved')]),
  tcIf(tcFold('AND', [tcEq(TV.focus, '55 / 60 min saved today'), tcEq(TC.lastTask, 'Read the primary source'), tcEq(TC.lastProject, 'history')]), [tcSet(TV.readEstimate, '30 min estimated · 22 min saved')]),
  tcIf(tcFold('AND', [tcSaved, tcEq(TC.lastTask, 'Outline the discussion'), tcEq(TC.lastProject, 'history')]), [tcSet(TC.outline, '20 min estimated · 12 min saved')]),
  // Preserve the original known correction of baseline Read time; do not pretend
  // this finite correction branch edits whichever task happened to save last.
  tcIf(tcEq(TV.focus, '43 / 60 min saved today'), [tcSet(TV.history, 'History seminar · 5h 13m'), tcSet(TV.readEstimate, '30 min estimated · 10 min saved')]),
];
const tcStatsRoots = [];
for (const id of ['7:3036', '7:3121']) {
  const root = await figma.getNodeByIdAsync(id);
  const reactions = root.reactions.map(reaction => reaction.trigger?.type === 'AFTER_TIMEOUT'
    ? { ...reaction, actions: [...tcStripOldAttribution(reaction.actions), ...JSON.parse(JSON.stringify(tcDerived))] } : reaction);
  if (!reactions.some(r => r.trigger?.type === 'AFTER_TIMEOUT')) throw Error('Stats entry reaction missing ' + id);
  await root.setReactionsAsync(reactions); touch(root); tcStatsRoots.push(id);
}

// Explicit finite correction of the BASELINE Read session, not the new save.
// Capture before writes, so 57->55 cannot cascade into a second45->43 action.
// Already-corrected43/55 are no-ops. No restore control exists in the inspected
// Correction roots, so this patch deliberately invents no restoration route.
function tcCorrectionEffects(input) {
  const uncorrected = tcFold('OR', [tcEq(input, '45 / 60 min saved today'), tcEq(input, '57 / 60 min saved today')]);
  const corrected = tcFold('OR', [tcEq(input, '43 / 60 min saved today'), tcEq(input, '55 / 60 min saved today')]);
  return [
    tcIf(tcEq(input, '45 / 60 min saved today'), [tcSet(TC.correctionSession, 'Session time        12 → 10 min'), tcSet(TC.correctionFocus, 'Saved today          45 → 43 min')]),
    tcIf(tcEq(input, '57 / 60 min saved today'), [tcSet(TC.correctionSession, 'Session time        12 → 10 min'), tcSet(TC.correctionFocus, 'Saved today          57 → 55 min')]),
    tcIf(tcEq(input, '43 / 60 min saved today'), [tcSet(TC.correctionSession, 'Session time        10 → 10 min'), tcSet(TC.correctionFocus, 'Saved today          43 → 43 min')]),
    tcIf(tcEq(input, '55 / 60 min saved today'), [tcSet(TC.correctionSession, 'Session time        10 → 10 min'), tcSet(TC.correctionFocus, 'Saved today          55 → 55 min')]),
    ...[[33,31],[3,1],[45,43],[15,13]].map(([before,after]) => tcIf(tcFold('AND', [uncorrected, tcEq(TC.correctionWalletInput, 'Coins · ' + before)]), [tcSet(TC.correctionCoins, 'Coin balance         ' + before + ' → ' + after)])),
    ...[33,3,45,15,31,1,43,13].map(balance => tcIf(tcFold('AND', [corrected, tcEq(TC.correctionWalletInput, 'Coins · ' + balance)]), [tcSet(TC.correctionCoins, 'Coin balance         ' + balance + ' → ' + balance)])),
  ];
}
function tcStripLegacyCorrection(actions) {
  return (actions || []).flatMap(action => {
    if (action.type === 'SET_VARIABLE' && ((action.variableId === TV.focus.id && action.variableValue?.value === '43 / 60 min saved today') || (action.variableId === TV.coins.id && action.variableValue?.value === 'Coins · 31') || (action.variableId === TV.available.id && action.variableValue?.value === '31 coins available'))) return [];
    if (action.type === 'CONDITIONAL') return [{ ...action, conditionalBlocks: action.conditionalBlocks.map(b => ({ ...b, actions: tcStripLegacyCorrection(b.actions) })) }];
    return [action];
  });
}
const tcCorrectionTouched = [];
for (const id of ['7:3210', '7:3247', '7:3282']) {
  const root = await figma.getNodeByIdAsync(id);
  for (const node of [root, ...root.findAllWithCriteria({ types: ['FRAME', 'INSTANCE'] })]) {
    if (!node.reactions?.length) continue;
    const before = JSON.stringify(node.reactions), next = node.reactions.map(r => ({ ...r, actions: tcStripLegacyCorrection(r.actions) }));
    if (JSON.stringify(next) !== before) { await node.setReactionsAsync(next); touch(node); tcCorrectionTouched.push(node.id); }
  }
}
for (const [id, v] of [['7:3269', TC.correctionSession], ['7:3304', TC.correctionSession], ['7:3270', TC.correctionFocus], ['7:3305', TC.correctionFocus], ['7:3273', TC.correctionCoins], ['7:3308', TC.correctionCoins]]) {
  const n = await figma.getNodeByIdAsync(id); if (n?.type !== 'TEXT') throw Error('Correction text changed ' + id);
  n.setBoundVariable('characters', v); touch(n);
}
const tcPreview = await figma.getNodeByIdAsync('7:3247');
const tcPreviewReactions = tcPreview.reactions.map(r => r.trigger?.type === 'AFTER_TIMEOUT' ? { ...r, actions: [...r.actions, tcCapture(TC.previewInput, TV.focus), tcCapture(TC.correctionWalletInput, TV.coins), ...tcCorrectionEffects(TC.previewInput)] } : r);
if (!tcPreviewReactions.some(r => r.trigger?.type === 'AFTER_TIMEOUT')) tcPreviewReactions.push({ trigger: { type: 'AFTER_TIMEOUT', timeout: .01 }, actions: [tcCapture(TC.previewInput, TV.focus), tcCapture(TC.correctionWalletInput, TV.coins), ...tcCorrectionEffects(TC.previewInput)] });
await tcPreview.setReactionsAsync(tcPreviewReactions); touch(tcPreview);
const tcApplyCorrection = await figma.getNodeByIdAsync('7:3280');
const tcUncorrectedInput = tcFold('OR', [tcEq(TC.correctionInput, '45 / 60 min saved today'), tcEq(TC.correctionInput, '57 / 60 min saved today')]);
const tcApplyPrefix = [tcCapture(TC.correctionInput, TV.focus), tcCapture(TC.correctionWalletInput, TV.coins), ...tcCorrectionEffects(TC.correctionInput),
  tcIf(tcEq(TC.correctionInput, '45 / 60 min saved today'), [tcSet(TV.focus, '43 / 60 min saved today')]),
  tcIf(tcEq(TC.correctionInput, '57 / 60 min saved today'), [tcSet(TV.focus, '55 / 60 min saved today')]),
  ...[[33,31],[3,1],[45,43],[15,13]].map(([before,after]) => tcIf(tcFold('AND', [tcUncorrectedInput, tcEq(TC.correctionWalletInput, 'Coins · ' + before)]), [tcSet(TV.coins, 'Coins · ' + after), tcSet(TV.available, after + ' coins available')]))];
await tcApplyCorrection.setReactionsAsync(tcApplyCorrection.reactions.map(r => r.trigger?.type === 'ON_CLICK' ? { ...r, actions: [...JSON.parse(JSON.stringify(tcApplyPrefix)), ...r.actions] } : r));
touch(tcApplyCorrection); tcCorrectionTouched.push(tcApplyCorrection.id, tcPreview.id);
return done({ createdVariableIds: tcNewVariableIds,
  prototypeVariableDefaults: tcDefaults,
  timeContextVariables: Object.fromEntries(Object.entries(TC).map(([k, v]) => [k, v.id])),
  finishCaptureNodes: tcFinishNodes, statsRoots: tcStatsRoots, correctionNodes: [...new Set(tcCorrectionTouched)],
  reviewNotes: [
    'Draft only until root reviews and executes. Finite first 12-minute save; not a general session ledger.',
    'Capture occurs only when focus was45 or43 before the original success. Save yields57 or55; replay at57/55 preserves corrected totals and captured task/context.',
    'Changing setup selection after finalization cannot rewrite saved attribution.',
    'Reset must apply every prototypeVariableDefaults value plus existing focus/stat defaults.',
    'Read/Outline rows cover their known task estimates; other tasks contribute to the captured project total only in this bounded Stats sample.',
    'Captured correction45->43 or57->55; repeat43/55 does not subtract again.55 Stats retain the saved project/taskdelta plus baseline Read reduction.',
    'Known Birch wallet branches only: Finish33->45,3->15,31->43,1->13; correction33->31,3->1,45->43,15->13. Captured wallet prevents cascading writes; repeats preserve current balances.',
    'No existing restoration control was found in the three inspected Correction roots; no restore route was invented.',
    'Verify installed single-IF reactions with Read, Outline, CS61A, Economics, Personal, duplicate-title Book study room, changed post-finish selection, retries and reset.'
  ] });

