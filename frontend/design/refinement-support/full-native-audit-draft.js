// READ-ONLY installed native audit/model. Root supplies current META.
// No setReactionsAsync, setValueForMode, node edits, model calls or app operations.
const faPage=await figma.getNodeByIdAsync('2:5');await figma.setCurrentPageAsync(faPage);
figma.skipInvisibleInstanceChildren=false;
const faRoots=faPage.children.flatMap(n=>n.type==='SECTION'?n.children.filter(c=>c.type==='FRAME'):n.type==='FRAME'?[n]:[]);
const faByRoot=new Map(faRoots.map(n=>[n.id,n])),faNodes=new Map(),faIssues=[],faCascades=[],faGrips=[],faTargets=new Map();
function faWalk(n,root){faNodes.set(n.id,{n,root});if('children'in n)for(const c of n.children)faWalk(c,root);}
for(const f of faRoots)faWalk(f,f);
const faVariables=await figma.variables.getLocalVariablesAsync(),faVarMap=new Map(faVariables.map(v=>[v.id,v]));
const faBase=new Map(faVariables.map(v=>[v.id,Object.values(v.valuesByMode)[0]]));
const faV={
  read:META.stateVariables.readingComplete,readOpen:META.stateVariables.readingIncomplete,theme:META.stateVariables.themeComplete,
  closed:META.stateVariables.weekClosed,snapshot:META.stateVariables.readingAtClosure,session:META.stateVariables.session,
  tasks:META.stateVariables.taskCount,parent:META.stateVariables.parentProgress,focus:META.stateVariables.focus,wallet:META.stateVariables.wallet,
  selected:META.prototypeVariables.selectedTask,context:META.prototypeVariables.selectedContext,
  created:'VariableID:124:5773',createdAtClosure:'VariableID:124:5774',themeAtClosure:'VariableID:124:5775',
  chapter:'VariableID:124:5777',chapterOpen:'VariableID:124:5778',themeOpen:'VariableID:124:5779',chapterAtClosure:'VariableID:124:5780',
  frozenCount:'VariableID:124:5786',todayCount:'VariableID:124:5785',weekCount:'VariableID:124:5782',
  moved:'VariableID:130:6958',onSunday:'VariableID:130:6959',movedAtClosure:'VariableID:130:6960',sunAtClosure:'VariableID:130:6961',suggestion:'VariableID:130:6962',
  unknown:'VariableID:105:5610',failed:'VariableID:105:5609',carryCount:'VariableID:91:5603',appliedCount:'VariableID:91:5604',
  readEligible:'VariableID:91:5615',readDay:'VariableID:91:5616',themeEligible:'VariableID:126:6930',chapterEligible:'VariableID:126:6936',createdEligible:'VariableID:126:6942'
};
const faProto=META.prototypeVariables.collection;
function faIssue(code,where,detail){faIssues.push({code,node:where.n?.id||where.id,root:where.root?.id,detail});}
function faRefs(d,set=new Set()){
  if(!d)return set;if(d.type==='VARIABLE_ALIAS'&&d.value?.id)set.add(d.value.id);
  if(d.type==='EXPRESSION')for(const a of d.value.expressionArguments||[])faRefs(a,set);return set;
}
function faWrites(a,set=new Set()){
  if(a.type==='SET_VARIABLE'&&a.variableId)set.add(a.variableId);
  if(a.type==='CONDITIONAL')for(const b of a.conditionalBlocks||[])for(const x of b.actions||[])faWrites(x,set);return set;
}
function faExpr(d,where){
  if(!d)return;
  if(d.type==='VARIABLE_ALIAS'&&d.value?.id&&!faVarMap.has(d.value.id))faIssue('missing-variable',where,d.value.id);
  if(d.type!=='EXPRESSION')return;
  const x=d.value,args=x.expressionArguments||[],arity={AND:2,OR:2,EQUALS:2,NOT_EQUAL:2,NOT:1};
  if(arity[x.expressionFunction]&&args.length!==arity[x.expressionFunction])faIssue('expression-arity',where,{fn:x.expressionFunction,count:args.length});
  for(const a of args)faExpr(a,where);
}
function faScan(actions,where,depth=0){
  const phases=[];
  for(let i=0;i<actions.length;i++){
    const a=actions[i];if(!a||Array.isArray(a)){faIssue('invalid-action-array',where,i);continue;}
    if(a.type==='CONDITIONAL'){
      if(depth)faIssue('nested-conditional',where,i);
      if(a.conditionalBlocks?.length!==1)faIssue('not-single-if',where,{index:i,blocks:a.conditionalBlocks?.length});
      for(const b of a.conditionalBlocks||[]){
        if(!b.condition)faIssue('implicit-else',where,i);else faExpr(b.condition,where);
        const reads=faRefs(b.condition),writes=new Set();for(const x of b.actions||[])faWrites(x,writes);
        phases.push({i,reads,writes});faScan(b.actions||[],where,depth+1);
      }
    }else if(a.type==='SET_VARIABLE'){
      if(!faVarMap.has(a.variableId))faIssue('missing-set-variable',where,a.variableId);faExpr(a.variableValue,where);
    }else if(a.type==='NODE'){
      if(!a.destinationId)faIssue('missing-destination',where,{index:i,navigation:a.navigation});
      else{if(!faTargets.has(a.destinationId))faTargets.set(a.destinationId,[]);faTargets.get(a.destinationId).push({node:where.n.id,root:where.root.id,navigation:a.navigation});}
    }
  }
  if(depth===0)for(const p of phases){
    const unstable=[...p.reads].filter(id=>p.writes.has(id));
    for(const id of unstable)if(phases.some(q=>q.i>p.i&&q.reads.has(id)))
      faCascades.push({node:where.n.id,root:where.root.id,variable:id,name:faVarMap.get(id)?.name,index:p.i,review:'An IF mutates its own predicate and a later IF reads it; inspect captured-guard semantics.'});
  }
}
let faReactionCount=0,faActionNodes=0;
for(const item of faNodes.values()){
  const n=item.n;if(!('reactions'in n))continue;
  if(n.reactions.length)faActionNodes++;
  for(const r of n.reactions){faReactionCount++;faScan(r.actions||[],item);}
  if(n.name==='Grip target'||n.name==='Icon / grip'){
    const drag=n.reactions.find(r=>r.trigger?.type==='ON_DRAG');
    if(drag){const b=n.absoluteBoundingBox||{width:n.width,height:n.height};faGrips.push({id:n.id,root:item.root.id,width:b.width,height:b.height});if(b.width<32||b.height<32)faIssue('grip-target-under-32',item,{width:b.width,height:b.height});}
  }
}
for(const[id,sources]of faTargets){
  const target=faNodes.get(id)?.n||await figma.getNodeByIdAsync(id);
  if(!target)for(const s of sources)faIssues.push({code:'unresolved-destination',node:s.node,root:s.root,detail:id});
  else if(sources.some(s=>['NAVIGATE','SWAP','OVERLAY'].includes(s.navigation))){
    let p=target;while(p&&p.type!=='PAGE')p=p.parent;
    if(p?.id!=='2:5')for(const s of sources.filter(s=>['NAVIGATE','SWAP','OVERLAY'].includes(s.navigation)))faIssues.push({code:'native-link-to-other-page',node:s.node,root:s.root,detail:{destination:id,page:p?.id}});
  }
}
for(const s of faPage.flowStartingPoints)if(!faByRoot.has(s.nodeId))faIssues.push({code:'start-not-native-root',node:s.nodeId,detail:s.name});
const faRequiredStarts=['5:3972','6:1802','7:2733','7:2780','5:4694','5:5567','9:6023','7:2980','7:3210','7:3482'];
for(const id of faRequiredStarts)if(!faPage.flowStartingPoints.some(s=>s.nodeId===id))faIssues.push({code:'missing-baseline-start',node:id});
const faCoverage=[];
for(const title of['Read the primary source','Choose the seminar theme','Summarize chapter 4','Draft seminar questions']){
  const rows=[...faNodes.values()].filter(x=>x.n.type==='INSTANCE'&&x.n.name==='Task / '+title);
  const missing=[];let controls=0;
  for(const x of rows){const boxes=x.n.findAllWithCriteria({types:['INSTANCE']}).filter(n=>n.name==='Checkbox');
    if(!boxes.length)continue;controls++;
    if(!boxes.some(n=>n.reactions.some(r=>r.trigger?.type==='ON_CLICK'&&(r.actions||[]).length)))missing.push({row:x.n.id,root:x.root.id,checkbox:boxes[0].id});
  }
  faCoverage.push({title,rows:rows.length,checkboxRows:controls,withoutClick:missing,interpretation:'Coverage finding; inspect actual visibility/modal shielding before treating a missing handler as a reachable defect.'});
}
// The interpreter writes only a disposable JS Map, never Figma variables.
function faEnvironment(extra={}){
  const e=new Map(faBase);for(const v of faVariables)if(v.variableCollectionId===faProto){
    if(v.name.startsWith('Refinement / carryover / ')&&v.name.endsWith(' applied'))e.set(v.id,false);
  }
  const defaults={read:false,readOpen:true,theme:true,themeOpen:false,chapter:true,chapterOpen:false,closed:false,snapshot:false,
    session:'idle',created:false,createdAtClosure:false,themeAtClosure:true,chapterAtClosure:true,moved:false,onSunday:true,
    movedAtClosure:false,sunAtClosure:true,suggestion:'Sun, Nov 8',unknown:false,failed:false,
    selected:'Read the primary source',context:'History seminar / Prepare seminar discussion',tasks:'9 / 25',focus:'45 / 60 min saved today',wallet:'Coins · 33',appliedCount:'0'};
  for(const[k,value]of Object.entries({...defaults,...extra})){if(!faV[k]||!faVarMap.has(faV[k]))throw Error('Missing model variable '+k);e.set(faV[k],value);}
  return e;
}
function faEv(d,e){
  if(d==null)return true;if(d.type==='VARIABLE_ALIAS')return e.get(d.value.id);
  if(d.type!=='EXPRESSION')return d.value;
  const a=d.value.expressionArguments.map(x=>faEv(x,e));switch(d.value.expressionFunction){
    case'AND':return a.every(Boolean);case'OR':return a.some(Boolean);case'NOT':return!a[0];case'EQUALS':return a[0]===a[1];case'NOT_EQUAL':return a[0]!==a[1];
    case'ADDITION':return a[0]+a[1];case'SUBTRACTION':return a[0]-a[1];case'MULTIPLICATION':return a[0]*a[1];case'DIVISION':return a[0]/a[1];
    default:throw Error('UNVERIFIED expression '+d.value.expressionFunction);
  }
}
function faRun(actions,e,routes=[]){for(const a of actions){
  if(a.type==='SET_VARIABLE')e.set(a.variableId,faEv(a.variableValue,e));
  else if(a.type==='CONDITIONAL'){for(const b of a.conditionalBlocks||[])if(faEv(b.condition,e)){faRun(b.actions,e,routes);break;}}
  else if(a.type==='NODE')routes.push(a.destinationId);
  else if(a.type!=='SET_VARIABLE_MODE')throw Error('UNVERIFIED action '+a.type);
}return routes;}
function faReaction(n,type='ON_CLICK'){const r=n?.reactions?.find(r=>r.trigger?.type===type);if(!r)throw Error('Missing '+type+' action '+n?.id+' '+n?.name);return r.actions||[];}
function faRoot(id){const f=faByRoot.get(id);if(!f)throw Error('Missing model root '+id);return f;}
function faAction(id,label){const n=faRoot(id).findAllWithCriteria({types:['INSTANCE']}).find(n=>n.name==='Action / '+label);if(!n)throw Error('Missing action '+id+' / '+label);return n;}
function faRow(ids,title,completed){
  for(const id of ids){const f=faByRoot.get(id);if(!f)continue;
    const n=f.findAllWithCriteria({types:['INSTANCE']}).find(n=>n.name==='Task / '+title&&(n.mainComponent?.id===META.components.Completed)===completed);if(n)return n;
  }throw Error('Missing '+(completed?'completed':'active')+' row '+title);
}
function faCheckbox(row){
  const all=row.findAllWithCriteria({types:['INSTANCE','FRAME']}).filter(n=>n.name==='Checkbox');
  return all.find(n=>n.reactions?.some(r=>r.trigger?.type==='ON_CLICK'))||all[0];
}
function faSettle(id,e){let at=id;const visited=[];for(let i=0;i<8&&at;i++){
  const f=faByRoot.get(at);if(!f)return at;
  const after=f.reactions.filter(r=>r.trigger?.type==='AFTER_TIMEOUT');if(!after.length)return at;
  const next=after.flatMap(r=>faRun(r.actions||[],e));if(next.length>1)throw Error('Multiple timed navigation results '+next.join(','));
  if(!next.length||next[0]===at)return at;if(visited.includes(next[0]))throw Error('Timed navigation cycle');visited.push(at);at=next[0];
}return at;}
function faClick(n,e){const routes=faRun(faReaction(n),e);if(routes.length>1)throw Error('Multiple click destinations '+routes.join(','));return routes.length?faSettle(routes[0],e):null;}
function faAssert(ok,message){if(!ok)throw Error(message);}
const faTests=[];
function faTest(name,fn){try{const detail=fn();faTests.push({name,status:'Pass',...(detail?{detail}: {})});}catch(error){const message=String(error.message||error);faTests.push({name,status:message.startsWith('UNVERIFIED')?'Unverified':'Fail',detail:message});}}
faTest('One Save and replay add one current leaf; failed retry preserves identity',()=>{
  const e=faEnvironment(),save=faAction('5:5491','Save');faClick(save,e);
  faAssert(e.get(faV.created)===true,'Created flag was not set');faAssert(/\/\s*26$/.test(e.get(faV.tasks)),'Expected denominator26: '+e.get(faV.tasks));
  faClick(save,e);faAssert(/\/\s*26$/.test(e.get(faV.tasks)),'Repeated Save duplicated the leaf');
  faClick(faAction('9:6023','Retry Save'),e);faAssert(/\/\s*26$/.test(e.get(faV.tasks)),'Retry duplicated the leaf');
});
faTest('Closed-day Save creates nothing and retains a reviewable form',()=>{
  const e=faEnvironment({closed:true}),to=faClick(faAction('5:5491','Save'),e);
  faAssert(e.get(faV.created)===false,'Closed Save created a task');faAssert(to==='124:7050','Expected blocked Save frame; got '+to);
});
for(const session of['idle','running','paused','review','sleep'])faTest('Read completion/reopen preserves '+session+' session',()=>{
  const e=faEnvironment({session}),before=[e.get(faV.focus),e.get(faV.wallet),e.get(faV.selected)];
  faClick(faCheckbox(faRow(['5:3972','5:4847'],'Read the primary source',false)),e);
  faAssert(e.get(faV.read)===true&&e.get(faV.readOpen)===false,'Completion/inverse mismatch');
  faAssert(e.get(faV.session)===session,'Completion changed session');faAssert(/^10\s*\/\s*25$/.test(e.get(faV.tasks)),'Wrong leaf total '+e.get(faV.tasks));
  faClick(faCheckbox(faRow(['5:4109','5:5292','6:2336'],'Read the primary source',true)),e);
  faAssert(e.get(faV.read)===false&&e.get(faV.readOpen)===true,'Reopen/inverse mismatch');faAssert(e.get(faV.session)===session,'Reopen changed session');
  faAssert(before.every((x,i)=>x===[e.get(faV.focus),e.get(faV.wallet),e.get(faV.selected)][i]),'Task completion changed saved credit/wallet/selected session task');
});
faTest('Theme and Chapter reopen after closure stay excluded; snapshots remain frozen',()=>{
  const e=faEnvironment();faClick(faAction('6:2541','End Week'),e);
  const frozen=[e.get(faV.themeAtClosure),e.get(faV.chapterAtClosure),e.get(faV.createdAtClosure),e.get(faV.frozenCount)];
  faClick(faCheckbox(faRow(['5:5292','5:4109','5:4951'],'Choose the seminar theme',true)),e);
  faClick(faCheckbox(faRow(['5:4951','5:4109','6:2336'],'Summarize chapter 4',true)),e);
  faAssert(e.get(faV.theme)===false&&e.get(faV.chapter)===false,'Theme/Chapter did not reopen');
  faClick(faAction('6:2600','Carry unfinished…'),e);
  faAssert(e.get(faV.themeEligible)===false&&e.get(faV.chapterEligible)===false,'Completed-at-closure work became eligible after reopening');
  faAssert(frozen.every((x,i)=>x===[e.get(faV.themeAtClosure),e.get(faV.chapterAtClosure),e.get(faV.createdAtClosure),e.get(faV.frozenCount)][i]),'Closure facts changed after reopen');
});
faTest('Created + reopened Theme/Chapter produce12 reviewed candidates and exactly12 applied plans',()=>{
  const e=faEnvironment({theme:false,themeOpen:true,chapter:false,chapterOpen:true,created:true});
  faClick(faAction('6:2541','End Week'),e);faAssert(e.get(faV.carryCount)==='12','Expected12 candidates; got '+e.get(faV.carryCount));
  faAssert(e.get(faV.themeEligible)===true&&e.get(faV.chapterEligible)===true&&e.get(faV.createdEligible)===true,'Extra candidates not eligible');
  faClick(faAction('6:2683','Apply carryover'),e);faAssert(e.get(faV.appliedCount)==='12','Expected12 applied; got '+e.get(faV.appliedCount));
  faClick(faAction('6:2683','Apply carryover'),e);faAssert(e.get(faV.appliedCount)==='12','Duplicate Apply changed saved count');
});
faTest('Successful Move persists Friday/current flags and captured Saturday carryover suggestion',()=>{
  const e=faEnvironment();faSettle('70:4678',e);faAssert(e.get(faV.moved)===true&&e.get(faV.onSunday)===false,'Move success did not update current placement flags');
  faClick(faAction('6:2541','End Week'),e);
  faAssert(e.get(faV.movedAtClosure)===true&&e.get(faV.sunAtClosure)===false,'Move was not captured');
  faAssert(e.get(faV.suggestion)==='Sat, Nov 7'&&e.get(faV.readDay)==='Sat, Nov 7','Expected Saturday suggestion after retained Saturday placement');
  e.set(faV.moved,false);e.set(faV.onSunday,true);faClick(faAction('6:2600','Carry unfinished…'),e);
  faAssert(e.get(faV.movedAtClosure)===true&&e.get(faV.sunAtClosure)===false,'Current placement changed frozen placement flags');
  faAssert(e.get(faV.readDay)==='Sat, Nov 7','Re-entry lost captured suggestion');
});
const faCounts={roots:faRoots.length,nodes:faNodes.size,reactionNodes:faActionNodes,reactions:faReactionCount,destinations:faTargets.size,dragGripTargets:faGrips.length,
  structureIssues:faIssues.length,potentialGuardCascades:faCascades.length,modelPass:faTests.filter(t=>t.status==='Pass').length,modelFail:faTests.filter(t=>t.status==='Fail').length,modelUnverified:faTests.filter(t=>t.status==='Unverified').length};
const faOut={counts:faCounts,structureIssues:faIssues,potentialGuardCascades:faCascades,gripTargets:faGrips,modelChecks:faTests,namedStarts:faPage.flowStartingPoints,
  boundedCompletionCoverage:faCoverage,
  limit:'Read-only structure and local Map interpretation of INSTALLED reaction metadata. No Figma preview clicking, keyboard execution, arbitrary drag, actual timing, application persistence, hardware or assistive-technology evidence.'};
const faBytes=JSON.stringify(faOut).length;
return faBytes<90000?faOut:{counts:faCounts,modelChecks:faTests,gripTargets:faGrips,structureIssueNodeIds:[...new Set(faIssues.map(x=>x.node))],cascadeNodeIds:[...new Set(faCascades.map(x=>x.node))],detailsOmitted:true,serializedBytes:faBytes,followUp:'Issue details exceed budget; query the listed exact nodes in a narrower read-only pass.',limit:faOut.limit};
