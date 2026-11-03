const META={"screens":{"Today":"5:3972","Today completed":"5:4109","Earlier unfinished":"5:4258","Task saved":"5:4403","Today with timer":"5:4551","Reopen failed":"5:4694","Projects":"5:4847","Done":"5:4951","Reopened task":"5:5054","Rename project":"5:5166","Add project":"5:5229","Project completed child":"5:5292","Done previous week":"5:5369","Done unplanned":"5:5430","Task details":"5:5491","Task validation":"5:5567","Week":"6:1802","Wednesday":"6:1934","Reorder preview":"6:2004","Week reordered":"6:2136","Week moved":"6:2266","Week completed":"6:2336","Move date":"6:2420","Move conflict":"6:2481","End Week preview":"6:2541","Closed week":"6:2600","Carryover":"6:2634","Carryover preview":"6:2683","Carryover exclusions":"6:2732","Next week":"6:2761","Track ready":"7:2586","Track running":"7:2639","Track paused":"7:2686","Track recovery":"7:2733","Track sleep":"7:2780","Track finished":"7:2827","Forest":"7:2879","Shop":"7:2929","Purchase failed":"7:2980","Stats":"7:3036","Stats details":"7:3121","Correction":"7:3210","Correction preview":"7:3247","Correction saved":"7:3282","Assistant":"7:3316","Assistant generating":"7:3355","Assistant answer":"7:3390","Assistant sources":"7:3434","Assistant unavailable":"7:3482","Monday":"9:5736","Tuesday":"9:5791","Thursday":"9:5846","Friday":"9:5901","Saturday":"9:5956","Task save failed":"9:6023","Reopened child":"9:6097","Today paused":"14:3112","Today review":"14:3157","Today sleep":"14:3202","Today completed timer":"14:3247","Today completed paused":"14:3293","Today completed review":"14:3339","Today completed sleep":"14:3385","Today after focus":"14:3431","Today completed after focus":"14:3471","Week task completed":"14:3512","End Week completed preview":"14:3649","Closed week completed":"14:3706","Previous closed week":"14:3733","History":"14:3767","Carryover one":"17:4256","Carryover one preview":"17:4308","Next week one":"17:4359","Track completed selection":"17:4429","Next week empty":"23:4666","Move saving":"70:4678","Move failed":"70:4844","Move response uncertain":"70:5009","Today reordered":"79:5105","Change carryover day":"91:5667","Carryover review changed":"91:5720","Carryover save failed":"91:5773","Carryover response missing":"91:5826","Track task picker":"105:5618","Track finish failed":"105:5656","Track finish unconfirmed":"105:5693","Assistant draft retained":"110:5638","Task save blocked / closed planned day":"124:7050","Reorder preview up":"147:7536"},"stateVariables":{"session":"VariableID:18:4753","readingComplete":"VariableID:18:4754","readingIncomplete":"VariableID:18:4755","weekClosed":"VariableID:18:4756","themeComplete":"VariableID:18:4757","readingAtClosure":"VariableID:18:4758","focus":"VariableID:18:4759","wallet":"VariableID:18:4760","available":"VariableID:18:4761","parentProgress":"VariableID:18:4762","childCount":"VariableID:18:4763","taskCount":"VariableID:18:4764","carryState":"VariableID:23:4741","carryRemaining":"VariableID:23:4742","doneTotal":"VariableID:23:4743","doneWeek":"VariableID:23:4744","completedExpanded":"VariableID:28:4603","completedCollapsed":"VariableID:28:4604","readingMovedOffSunday":"VariableID:130:6958","readingOnSunday":"VariableID:130:6959","readingMovedAtClosure":"VariableID:130:6960","readingOnSundayAtClosure":"VariableID:130:6961","readCarrySuggestion":"VariableID:130:6962"},"prototypeVariables":{"collection":"VariableCollectionId:9:6181","selectedTask":"VariableID:9:6182","selectedContext":"VariableID:9:6183"},"components":{"Button":"3:198","Secondary":"3:213","Quiet":"3:228","Checkbox":"3:244","Checked":"3:252","Input":"3:263","Active":"3:289","Selected":"3:298","Completed":"3:306","Parent":"3:313","Long title":"3:322","Weekly":"3:340","Disclosure":"3:346","Feedback":"3:351","Streak":"3:381","Weekly column card":"12:33"}};const faPage=await figma.getNodeByIdAsync('2:5');await figma.setCurrentPageAsync(faPage);figma.skipInvisibleInstanceChildren=false;const faRoots=faPage.children.flatMap(n=>n.type==='SECTION'?n.children.filter(c=>c.type==='FRAME'):n.type==='FRAME'?[n]:[]);const faByRoot=new Map(faRoots.map(n=>[n.id,n]));const faVariables=await figma.variables.getLocalVariablesAsync(),faVarMap=new Map(faVariables.map(v=>[v.id,v])),faBase=new Map(faVariables.map(v=>[v.id,Object.values(v.valuesByMode)[0]])),faProto=META.prototypeVariables.collection;const faRxCache=new Map();function faReactions(n){if(!n)return[];if(!faRxCache.has(n.id))faRxCache.set(n.id,n.reactions||[]);return faRxCache.get(n.id)}
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
function faReaction(n,type='ON_CLICK'){const r=faReactions(n)?.find(r=>r.trigger?.type===type);if(!r)throw Error('Missing '+type+' action '+n?.id+' '+n?.name);return r.actions||[];}
function faRoot(id){const f=faByRoot.get(id);if(!f)throw Error('Missing model root '+id);return f;}
function faAction(id,label){const n=faRoot(id).findAllWithCriteria({types:['INSTANCE']}).find(n=>n.name==='Action / '+label);if(!n)throw Error('Missing action '+id+' / '+label);return n;}
function faRow(ids,title,completed){
  for(const id of ids){const f=faByRoot.get(id);if(!f)continue;
    const n=f.findAllWithCriteria({types:['INSTANCE']}).find(n=>n.name==='Task / '+title&&(n.mainComponent?.id===META.components.Completed)===completed);if(n)return n;
  }throw Error('Missing '+(completed?'completed':'active')+' row '+title);
}
function faCheckbox(row){
  const all=row.findAllWithCriteria({types:['INSTANCE','FRAME']}).filter(n=>n.name==='Checkbox');
  return all.find(n=>faReactions(n)?.some(r=>r.trigger?.type==='ON_CLICK'))||all[0];
}
function faSettle(id,e){let at=id;const visited=[];for(let i=0;i<8&&at;i++){
  const f=faByRoot.get(at);if(!f)return at;
  const after=faReactions(f).filter(r=>r.trigger?.type==='AFTER_TIMEOUT');if(!after.length)return at;
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


const failRoot=faRoot('5:4694'),retry=await figma.getNodeByIdAsync('I5:4843;3:349');
for(const session of['idle','running','paused','review','sleep'])faTest('Failed reopen Retry preserves '+session+' and then reopens Read',()=>{
 const e=faEnvironment({session}),before=[e.get(faV.focus),e.get(faV.wallet),e.get(faV.selected)];
 faSettle('5:4694',e);faAssert(e.get(faV.read)===true,'Failure did not retain complete');const to=faClick(retry,e);
 faAssert(e.get(faV.read)===false&&e.get(faV.readOpen)===true,'Retry did not reopen');faAssert(e.get(faV.session)===session,'Retry changed session');
 faAssert(before.every((v,i)=>v===[e.get(faV.focus),e.get(faV.wallet),e.get(faV.selected)][i]),'Retry changed saved/session context');return to;
});
const disc=await figma.getNodeByIdAsync('5:4101'),openDisc=await figma.getNodeByIdAsync('164:8316');
faTest('Completed disclosure opens and closes in place without changing completion',()=>{
 const e=faEnvironment();e.set('VariableID:28:4603',false);e.set('VariableID:28:4604',true);
 faAssert(faClick(disc,e)===null,'Disclosure navigated');faAssert(e.get('VariableID:28:4603')===true&&e.get('VariableID:28:4604')===false,'Did not open');
 faClick(openDisc,e);faAssert(e.get('VariableID:28:4603')===false&&e.get('VariableID:28:4604')===true,'Did not close');faAssert(e.get(faV.read)===false,'Disclosure changed task');
});
faTest('Reset returns every prototype variable to baseline, including final additions',()=>{
 const e=faEnvironment({read:true,readOpen:false,closed:true,created:true,session:'running'});e.set('VariableID:155:8299','Unrelated saved task');e.set('VariableID:166:5718',true);
 const action=faAction('141:7346','Reset demo · Today');const routes=faRun(faReaction(action),e);faAssert(routes.length===1&&routes[0]==='5:3972','Reset did not target Today');for(const v of faVariables.filter(v=>v.variableCollectionId===faProto))faAssert(e.get(v.id)===faBase.get(v.id),'Reset left '+v.name);const to=faSettle(routes[0],e);faAssert(to==='5:3972'&&e.get(faV.tasks)==='9 / 25','Reset arrival current totals wrong');faAssert(e.get(faV.session)==='idle'&&e.get(faV.focus)==='45 / 60 min saved today','Reset arrival changed baseline session or credit');return{variables:faVariables.filter(v=>v.variableCollectionId===faProto).length};
});
const asRoot=faRoot('7:3482');
faTest('Direct unavailable Assistant retains typed question or seeds sample question',()=>{
 const e=faEnvironment();e.set('VariableID:110:5634','My retained question');faSettle(asRoot.id,e);faAssert(e.get('VariableID:110:5634')==='My retained question','Typed question lost');
 e.set('VariableID:110:5634','');faSettle(asRoot.id,e);faAssert(e.get('VariableID:110:5634')==='What should I focus on today?','Isolated error blank');
});
faTest('Failure feedback ancestor cannot override Retry',()=>{faAssert(faReactions(failRoot.query('INSTANCE[name=Feedback]').first()||{id:'5:4843',reactions:[]}).length===0,'Feedback ancestor still reacts');});
for(const focus of['45 / 60 min saved today','43 / 60 min saved today','57 / 60 min saved today','55 / 60 min saved today'])faTest('Forest separates prior and new session at '+focus,()=>{
 const e=faEnvironment({focus});faSettle('7:2879',e);faAssert(e.get('VariableID:166:5718')===['57','55'].includes(focus.slice(0,2)),'New tree visibility wrong');faAssert(e.get('VariableID:166:5719')===('Today · '+(['43','55'].includes(focus.slice(0,2))?'10':'12')+' min'),'Prior corrected tree time wrong');
});
return {modelChecks:faTests,pass:faTests.filter(t=>t.status==='Pass').length,fail:faTests.filter(t=>t.status==='Fail').length,limit:'Read-only installed-reaction Map model; actual clicks/scroll remain unverified.'};
