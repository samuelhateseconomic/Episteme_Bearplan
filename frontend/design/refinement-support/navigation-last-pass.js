// CODE-ONLY R21 draft. Append after refine-helpers.js; PAGE_ID='2:5'.
// Root supplies current META plus FIXTURE. Optional NAV_EXTRA_SCREENS map and
// NAV_NEXT_PERIOD_ID (a reviewed native Nov9–15 frame) may extend the registry.
// Global navigation only: no completion/timer/carryover/Assistant business actions.
if(PAGE_ID!=='2:5')throw Error('Navigation pass requires native Canvas · Flows.');
const nvIds={...META.screens,...(typeof NAV_EXTRA_SCREENS==='object'?NAV_EXTRA_SCREENS:{})};
const nvVars={};
const nvVarIds={
  session:META.stateVariables.session,read:META.stateVariables.readingComplete,
  closed:META.stateVariables.weekClosed,snapshot:META.stateVariables.readingAtClosure,
  theme:META.stateVariables.themeComplete,chapter:'VariableID:124:5777',selected:META.prototypeVariables.selectedTask,
  context:META.prototypeVariables.selectedContext,order:'VariableID:79:5104',
  appliedCount:'VariableID:91:5604',unknown:'VariableID:105:5610',failed:'VariableID:105:5609'
};
for(const[k,id]of Object.entries(nvVarIds)){
  nvVars[k]=await figma.variables.getVariableByIdAsync(id);
  if(!nvVars[k])throw Error('Missing current navigation variable: '+k+' / '+id);
}
const nvTrack={ready:nvIds['Track ready'],running:nvIds['Track running'],paused:nvIds['Track paused'],
  review:nvIds['Track recovery'],sleep:nvIds['Track sleep'],completed:nvIds['Track completed selection'],
  failed:nvIds['Track finish failed']||'105:5656',unknown:nvIds['Track finish unconfirmed']||'105:5693'};
const nvRoots=new Map(),nvSkipped=[],nvWired=[],nvCounts={},nvEsc=[],nvAmbiguousStarts=[];
const nvStartsBefore=JSON.stringify(page.flowStartingPoints);
for(const[name,id]of Object.entries(nvIds)){
  const n=await figma.getNodeByIdAsync(id);
  if(n&&n.type==='FRAME'){
    let p=n;while(p&&p.type!=='PAGE')p=p.parent;
    if(p?.id===PAGE_ID)nvRoots.set(id,n);
  }
}
const nvTargetIds=new Set([...Object.values(nvTrack),nvIds.Today,nvIds['Today reordered'],
  nvIds['Today completed'],nvIds['Today with timer'],nvIds['Today paused'],nvIds['Today review'],
  nvIds['Today sleep'],nvIds['Today completed timer'],nvIds['Today completed paused'],
  nvIds['Today completed review'],nvIds['Today completed sleep'],nvIds['Today after focus'],
  nvIds['Today completed after focus'],nvIds.Week,nvIds['Week reordered'],nvIds['Week task completed'],
  nvIds['Closed week'],nvIds['Closed week completed'],nvIds['Next week'],nvIds['Next week one'],
  nvIds['Next week empty'],nvIds.Projects,nvIds['Reopened child'],nvIds.History,nvIds['Previous closed week']]);
for(const id of nvTargetIds)if(!id||!nvRoots.has(id))throw Error('Missing reviewed native navigation destination '+id);
const nvExtraNext=typeof NAV_NEXT_PERIOD_ID==='string'?NAV_NEXT_PERIOD_ID:null;
if(nvExtraNext){
  const n=await figma.getNodeByIdAsync(nvExtraNext);let p=n;while(p&&p.type!=='PAGE')p=p.parent;
  if(!n||n.type!=='FRAME'||p?.id!==PAGE_ID)throw Error('Nov9–15 must be a reviewed native destination.');
}
function nvLit(value){const type=typeof value==='boolean'?'BOOLEAN':'STRING';return{type,resolvedType:type,value};}
function nvAlias(v){return{type:'VARIABLE_ALIAS',resolvedType:v.resolvedType,value:{type:'VARIABLE_ALIAS',id:v.id}};}
function nvEq(v,value){return{type:'EXPRESSION',resolvedType:'BOOLEAN',value:{expressionFunction:'EQUALS',expressionArguments:[nvAlias(v),nvLit(value)]}};}
function nvFold(fn,args){
  if(!args.length)return nvLit(fn==='AND');
  if(args.length===1)return args[0];
  const mid=Math.ceil(args.length/2);
  return{type:'EXPRESSION',resolvedType:'BOOLEAN',value:{expressionFunction:fn,expressionArguments:[nvFold(fn,args.slice(0,mid)),nvFold(fn,args.slice(mid))]}};
}
function nvAll(...args){return nvFold('AND',args);}function nvAny(...args){return nvFold('OR',args);}
function nvSet(v,value){return{type:'SET_VARIABLE',variableId:v.id,variableValue:nvLit(value)};}
function nvGo(id){if(!id)throw Error('Unknown navigation ID');return{type:'NODE',destinationId:id,navigation:'NAVIGATE',transition:{type:'DISSOLVE',duration:.12,easing:{type:'EASE_OUT'}},resetScrollPosition:true};}
function nvIf(condition,actions){return{type:'CONDITIONAL',conditionalBlocks:[{condition,actions}]};}
function nvCases(rows){return rows.map(([condition,idOrActions])=>nvIf(condition,typeof idOrActions==='string'?[nvGo(idOrActions)]:idOrActions));}
function nvNoErrors(){return nvAll(nvEq(nvVars.unknown,false),nvEq(nvVars.failed,false));}
function nvIdle(){return nvAny(nvEq(nvVars.session,'idle'),nvEq(nvVars.session,'finished'));}
function nvDaily(){
  const rows=[],bad=nvAny(nvEq(nvVars.unknown,true),nvEq(nvVars.failed,true));
  rows.push([nvAll(bad,nvEq(nvVars.read,false)),nvIds['Today paused']],
    [nvAll(bad,nvEq(nvVars.read,true)),nvIds['Today completed paused']]);
  for(const[state,open,complete]of[
    ['running','Today with timer','Today completed timer'],['paused','Today paused','Today completed paused'],
    ['review','Today review','Today completed review'],['sleep','Today sleep','Today completed sleep'],
    ['finished','Today after focus','Today completed after focus']
  ])for(const[done,name]of[[false,open],[true,complete]])
    rows.push([nvAll(nvNoErrors(),nvEq(nvVars.session,state),nvEq(nvVars.read,done)),nvIds[name]]);
  rows.push([nvAll(nvNoErrors(),nvEq(nvVars.session,'idle'),nvEq(nvVars.read,true)),nvIds['Today completed']],
    [nvAll(nvNoErrors(),nvEq(nvVars.session,'idle'),nvEq(nvVars.read,false),nvEq(nvVars.order,true)),nvIds['Today reordered']],
    [nvAll(nvNoErrors(),nvEq(nvVars.session,'idle'),nvEq(nvVars.read,false),nvEq(nvVars.order,false)),nvIds.Today]);
  return nvCases(rows);
}
function nvTrackRows(){
  return[
    [nvEq(nvVars.unknown,true),nvTrack.unknown],
    [nvAll(nvEq(nvVars.unknown,false),nvEq(nvVars.failed,true)),nvTrack.failed],
    ...['running','paused','review','sleep'].map(s=>[nvAll(nvNoErrors(),nvEq(nvVars.session,s)),nvTrack[s]]),
    [nvAll(nvNoErrors(),nvIdle(),nvEq(nvVars.selected,'Read the primary source'),nvEq(nvVars.read,true)),nvTrack.completed],
    [nvAll(nvNoErrors(),nvIdle(),nvEq(nvVars.selected,'Read the primary source'),nvEq(nvVars.read,false)),nvTrack.ready],
    ...['Choose the seminar theme','Summarize chapter 4'].flatMap((title,i)=>[true,false].map(value=>[nvAll(nvNoErrors(),nvIdle(),nvEq(nvVars.selected,title),nvEq(i===0?nvVars.theme:nvVars.chapter,value)),value?nvTrack.completed:nvTrack.ready])),
[nvAll(nvNoErrors(),nvIdle(),{type:'EXPRESSION',resolvedType:'BOOLEAN',value:{expressionFunction:'NOT',expressionArguments:[nvAny(...['Read the primary source','Choose the seminar theme','Summarize chapter 4'].map(t=>nvEq(nvVars.selected,t)))]}}),nvTrack.ready]
  ];
}
function nvTrackRoute(){return nvCases(nvTrackRows());}
function nvFrozenRows(prefix=nvLit(true)){return[
  [nvAll(prefix,nvEq(nvVars.snapshot,false)),nvIds['Closed week']],
  [nvAll(prefix,nvEq(nvVars.snapshot,true)),nvIds['Closed week completed']]
];}
function nvCurrentWeek(){return nvCases([
  ...nvFrozenRows(nvEq(nvVars.closed,true)),
  [nvAll(nvEq(nvVars.closed,false),nvEq(nvVars.read,true)),nvIds['Week task completed']],
  [nvAll(nvEq(nvVars.closed,false),nvEq(nvVars.read,false),nvEq(nvVars.order,true)),nvIds['Week reordered']],
  [nvAll(nvEq(nvVars.closed,false),nvEq(nvVars.read,false),nvEq(nvVars.order,false)),nvIds.Week]
]);}
function nvNextWeek(){return nvCases([
  [nvEq(nvVars.appliedCount,'0'),nvIds['Next week empty']],
  [nvEq(nvVars.appliedCount,'1'),nvIds['Next week one']],
  ...['2','3','4','5','6','7','8','9','10','11','12'].map(n=>[nvEq(nvVars.appliedCount,n),nvIds['Next week']])
]);}
function nvProjects(){return nvCases([
  [nvEq(nvVars.theme,true),nvIds.Projects],[nvEq(nvVars.theme,false),nvIds['Reopened child']]
]);}
const nvFuture=new Set(['Next week','Next week one','Next week empty'].map(k=>nvIds[k]));
const nvSourceDays=new Set(['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Week moved'].map(k=>nvIds[k]));
const nvSourceWeeks=new Set(['Week','Week reordered','Week moved','Week completed','Week task completed','Reorder preview',
  'Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'].map(k=>nvIds[k]));
const nvHistoryRoots=new Set(['History','Previous closed week','Closed week','Closed week completed'].map(k=>nvIds[k]));
function nvWeekForFrame(f){
  if(nvFuture.has(f.id))return nvNextWeek();
  if(nvSourceDays.has(f.id))return nvCases([...nvFrozenRows(nvEq(nvVars.closed,true)),[nvEq(nvVars.closed,false),f.id]]);
  return nvCurrentWeek();
}
function nvHasAncestor(n,name,stop){let p=n.parent;while(p&&p.id!==stop.id){if(p.name===name)return true;p=p.parent;}return false;}
function nvActionLabel(n){return n.name.startsWith('Action / ')?n.name.slice(9).trim().toLowerCase():null;}
function nvCheckExpr(d){
  if(d?.type!=='EXPRESSION')return;
  const x=d.value;if(['AND','OR','EQUALS'].includes(x.expressionFunction)&&x.expressionArguments.length!==2)throw Error('Non-binary '+x.expressionFunction);
  for(const a of x.expressionArguments)nvCheckExpr(a);
}
function nvValidate(actions){for(const a of actions){
  if(a.type==='CONDITIONAL'){
    if(a.conditionalBlocks.length!==1||!a.conditionalBlocks[0].condition)throw Error('One explicit IF required.');
    const b=a.conditionalBlocks[0];nvCheckExpr(b.condition);
    if(b.actions.some(x=>x.type==='CONDITIONAL'||Array.isArray(x)))throw Error('Nested router actions unsupported.');
  }else if(Array.isArray(a)||!['NODE','SET_VARIABLE'].includes(a.type))throw Error('Unsupported router action');
}}
function nvOwner(n){let p=n;while(p){if(nvRoots.has(p.id))return p;p=p.parent;}return null;}
async function nvPatch(n,actions,kind='global',trigger='ON_CLICK'){
  nvValidate(actions);const owner=nvOwner(n);
  if(owner)actions=actions.flatMap(a=>{
    if(a.type==='NODE')return a.destinationId===owner.id?[]:[a];
    if(a.type!=='CONDITIONAL')return[a];
    const b=a.conditionalBlocks[0],remain=b.actions.filter(x=>x.type!=='NODE'||x.destinationId!==owner.id);
    return remain.length?[nvIf(b.condition,remain)]:[];
  });
  const old=n.reactions||[];
  const keep=old.filter(r=>r.trigger?.type!==trigger);
  const t=trigger==='ON_KEY_DOWN'?{type:trigger,device:'KEYBOARD',keyCodes:[27]}:{type:trigger};
  await n.setReactionsAsync(actions.length?[...keep,{trigger:t,actions}]:keep);touch(n);
  nvWired.push({id:n.id,kind,source:n.name});nvCounts[kind]=(nvCounts[kind]||0)+1;
}
const nvProjectNames=Object.fromEntries(FIXTURE.projects.map(p=>[p.id,p.name]));
const nvParentNames=Object.fromEntries(FIXTURE.parents.map(p=>[p.id,p.title]));
const nvTaskFacts=[...FIXTURE.tasks,FIXTURE.new_task_save_branch].filter(Boolean);
function nvCanonical(row,f){
  const title=row.findAllWithCriteria({types:['TEXT']}).find(n=>n.componentPropertyReferences?.characters?.startsWith('Title#'))?.characters||row.name.slice(7);
  let matches=nvTaskFacts.filter(t=>t.title===title);
  if(matches.length>1){const projectValue=Object.entries(row.componentProperties).find(([k])=>k.split('#')[0]==='Project')?.[1]?.value;const direct=matches.filter(t=>typeof projectValue==='string'&&projectValue.startsWith(nvProjectNames[t.project_id]));if(direct.length===1)matches=direct;}
  if(matches.length>1){
    const evidence=row.findAllWithCriteria({types:['TEXT']}).map(n=>n.characters);
    const local=matches.filter(t=>evidence.some(s=>s.startsWith(nvProjectNames[t.project_id])));
    if(local.length===1)matches=local;
    else{
      const heading=f.findAllWithCriteria({types:['TEXT']}).map(n=>n.characters);
      const scoped=matches.filter(t=>heading.some(s=>s===nvProjectNames[t.project_id]));
      if(scoped.length===1)matches=scoped;
    }
  }
  if(matches.length!==1)return null;
  const t=matches[0];return{...t,context:nvProjectNames[t.project_id]+(t.parent_id?' / '+nvParentNames[t.parent_id]:'')};
}
function nvTaskStart(task){
  const rows=nvTrackRows().slice(0,6); // error and active-session branches do not select another task.
  const idle=nvAll(nvNoErrors(),nvIdle());
  const select=[nvSet(nvVars.selected,task.title),nvSet(nvVars.context,task.context)];
  if(task.id==='read')rows.push(
    [nvAll(idle,nvEq(nvVars.read,true)),[...select,nvGo(nvTrack.completed)]],
    [nvAll(idle,nvEq(nvVars.read,false)),[...select,nvGo(nvTrack.ready)]]
  );
  else if(task.id==='theme')rows.push(
    [nvAll(idle,nvEq(nvVars.theme,false)),[...select,nvGo(nvTrack.ready)]],
    [nvAll(idle,nvEq(nvVars.theme,true)),[nvGo(nvIds.Projects)]]
  );
  else if(task.id==='chapter4')rows.push([nvAll(idle,nvEq(nvVars.chapter,false)),[...select,nvGo(nvTrack.ready)]],[nvAll(idle,nvEq(nvVars.chapter,true)),[...select,nvGo(nvTrack.completed)]]);
  else rows.push([idle,[...select,nvGo(nvTrack.ready)]]);
  return nvCases(rows);
}
for(const f of nvRoots.values()){
  const nodes=f.findAllWithCriteria({types:['INSTANCE']});
  for(const n of nodes){
    const label=nvActionLabel(n);if(!label)continue;
    let actions=null,kind=null;
    if(label==='plan'){actions=nvDaily();kind='daily';}
    else if(label==='track'||label==='open timer'){actions=nvTrackRoute();kind='track';}
    else if(label==='today'){
      const calendar=nvHasAncestor(n,'Week navigation',f);
      actions=calendar?nvCurrentWeek():nvDaily();kind=calendar?'weekToday':'daily';
    }else if(label==='week'){actions=nvWeekForFrame(f);kind='week';}
    else if(label==='projects'){actions=nvProjects();kind='projects';}
    else if(label==='history'){actions=[nvGo(nvIds.History)];kind='history';}
    else if(label==='source history'||label==='source week'){
      if(nvFuture.has(f.id)&&label==='source history'){
        props(n,{Label:'Source week'});n.name='Action / Source week';touch(n);
      }
      actions=nvCurrentWeek();kind='sourceWeek';
    }
    else if(label==='carry other work'&&nvFuture.has(f.id)){
      n.setBoundVariable('visible',nvVars.closed);touch(n);
      nvCounts.closedCarryoverVisibility=(nvCounts.closedCarryoverVisibility||0)+1;
    }
    else if(label==='back to plan'&&nvHistoryRoots.has(f.id)){actions=nvCurrentWeek();kind='backToPlan';}
    else if((['previous','previous week','next'].includes(label)||label.startsWith('next ·'))&&
      (nvHasAncestor(n,'Week navigation',f)||nvSourceWeeks.has(f.id))){
      const next=label==='next'||label.startsWith('next ·');
      if(next&&nvSourceWeeks.has(f.id)){actions=nvNextWeek();kind='calendarNext';}
      else if(!next&&nvFuture.has(f.id)){actions=nvCurrentWeek();kind='calendarPrevious';}
      else if(!next&&nvSourceWeeks.has(f.id)){actions=[nvGo(nvIds['Previous closed week'])];kind='calendarPrevious';}
      else if(next&&nvFuture.has(f.id)&&nvExtraNext){actions=[nvGo(nvExtraNext)];kind='calendarNext';}
      else if(next&&nvFuture.has(f.id)&&label.includes('sample boundary'))
        nvSkipped.push({id:n.id,root:f.id,label,reason:'Intentionally disabled sample-boundary control retained.'});
      else nvSkipped.push({id:n.id,root:f.id,label,reason:'No reviewed destination for this calendar period; resolve before acceptance.'});
    }
    if(actions)await nvPatch(n,actions,kind);
  }
  for(const row of nodes.filter(n=>n.name.startsWith('Task / '))){
    if([META.components.Completed,META.components.Parent].includes(row.mainComponent?.id))continue;
    const start=row.findAllWithCriteria({types:['INSTANCE']}).find(n=>n.findAllWithCriteria({types:['TEXT']}).some(t=>t.characters==='Start'));
    if(!start)continue;
    const task=nvCanonical(row,f);
    if(!task){nvAmbiguousStarts.push({row:row.id,start:start.id,root:f.id,title:row.name});continue;}
    await nvPatch(start,nvTaskStart(task),'taskStart');
  }
}
// Escape follows the visible Cancel/Keep planning action, preserving non-key triggers.
// Repaired carryover and Assistant/Track lifecycle handlers are intentionally untouched.
const nvModalNames=['Add project','Rename project','Task details','Task validation','Task save failed','Task save blocked / closed planned day',
  'Move date','Move conflict','Move failed','Move response uncertain','End Week preview','End Week completed preview','Reorder preview'];
for(const name of nvModalNames){
  const f=nvRoots.get(nvIds[name]);if(!f)continue;
  const labels=name.startsWith('End Week')?['keep planning']:['cancel'];
  const cancel=f.findAllWithCriteria({types:['INSTANCE']}).find(n=>labels.includes(nvActionLabel(n)));
  const click=cancel?.reactions.find(r=>r.trigger?.type==='ON_CLICK');
  if(!click?.actions?.length){nvSkipped.push({root:f.id,name,reason:'No explicit cancel action to copy for Escape.'});continue;}
  try{nvValidate(click.actions);}catch(error){nvSkipped.push({root:f.id,cancel:cancel.id,reason:'Cancel still requires business-action repair: '+String(error)});continue;}
  // Avoid copying a state-changing operation into Escape accidentally.
  const hasSet=click.actions.some(a=>a.type==='SET_VARIABLE'||a.type==='CONDITIONAL'&&a.conditionalBlocks.some(b=>b.actions.some(x=>x.type==='SET_VARIABLE')));
  if(hasSet){nvSkipped.push({root:f.id,cancel:cancel.id,reason:'Cancel changes prototype state; root must review Escape semantics explicitly.'});continue;}
  await nvPatch(f,JSON.parse(JSON.stringify(click.actions)),'escape','ON_KEY_DOWN');nvEsc.push({root:f.id,cancel:cancel.id});
}
if(JSON.stringify(page.flowStartingPoints)!==nvStartsBefore)throw Error('Named starts changed unexpectedly.');

const protectedComplete=nvAny(nvAll(nvEq(nvVars.selected,'Read the primary source'),nvEq(nvVars.read,true)),nvAll(nvEq(nvVars.selected,'Choose the seminar theme'),nvEq(nvVars.theme,true)),nvAll(nvEq(nvVars.selected,'Summarize chapter 4'),nvEq(nvVars.chapter,true)));
const notProtected={type:'EXPRESSION',resolvedType:'BOOLEAN',value:{expressionFunction:'NOT',expressionArguments:[protectedComplete]}};
for(const f of nvRoots.values()){
for(const n of f.findAllWithCriteria({types:['INSTANCE']})){
 if(n.name==='Action / Start countdown'){
  const idleValid=nvAll(nvNoErrors(),nvIdle(),notProtected);
  const actions=nvCases(nvTrackRows().slice(0,6));
  actions.push(nvIf(nvAll(nvNoErrors(),nvIdle(),protectedComplete),[nvGo(nvTrack.completed)]));
  // Capture the guard before changing session; subsequent IFs read its old value.
  actions.push(nvIf(idleValid,[nvSet(nvVars.session,'running'),nvGo(nvTrack.running)]));
  await nvPatch(n,actions,'guardedCountdownStart');
 }
}
for(const target of f.findAll(n=>n.type==='FRAME'&&n.name==='Grip target')){
 const icon=target.findAll(n=>n.type==='FRAME'&&n.name==='Icon / grip')[0];
 const drag=icon?.reactions.find(r=>r.trigger?.type==='ON_DRAG');
 if(drag){await target.setReactionsAsync([...(target.reactions||[]).filter(r=>r.trigger?.type!=='ON_DRAG'),drag]);await icon.setReactionsAsync(icon.reactions.filter(r=>r!==drag));touch(target);touch(icon);nvCounts.fullSizeDragTarget=(nvCounts.fullSizeDragTarget||0)+1;}
}
}

return done({routerCounts:nvCounts,rewiredCount:nvWired.length,rewiredExamples:nvWired.slice(0,5),escapeRoutes:nvEsc,skipped:nvSkipped,ambiguousTaskStarts:nvAmbiguousStarts,
  namedStartsPreserved:page.flowStartingPoints,variables:nvVarIds,rootsScanned:nvRoots.size,
  unresolvedCalendarEdges:nvSkipped.filter(x=>x.reason.includes('calendar period')),
  limits:[
    'No model/provider/application action is executed. Only existing navigation/Start controls are wired.',
    'Carryover result rows have no Start control; this pass does not invent one.',
    'Manual-order plus active-session combinations still need rendered-content checks; session controls take priority over idle reordered layout.',
    'The movement branch has no shared moved-placement variable; cross-workspace reconstruction of arbitrary movement is outside this bounded router.',
    'Root owns business completion/timer/closure/Assistant actions and prototype Reset, including isolated recovery starts.',
    'Missing Nov9–15 or ambiguous task destinations remain explicit acceptance findings; no fallback ELSE or false calendar jump is installed.'
  ]});

