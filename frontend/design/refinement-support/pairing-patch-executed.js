// R21 pairing only. Root runs before refine-completion-draft.js, then generic
// Start/navigation and actual renders. No source/frozen or app changes.
if(PAGE_ID!=='2:5')throw Error('Pairing requires Canvas · Flows');
const CT=Object.fromEntries(await Promise.all(Object.entries(META.refinementVariableGroups.created).map(async([k,id])=>[k,await figma.variables.getVariableByIdAsync(id)])));
const readDone=await figma.variables.getVariableByIdAsync(META.stateVariables.readingComplete),readOpen=await figma.variables.getVariableByIdAsync(META.stateVariables.readingIncomplete),themeDone=await figma.variables.getVariableByIdAsync(META.stateVariables.themeComplete),expanded=await figma.variables.getVariableByIdAsync(META.stateVariables.completedExpanded),onSunday=await figma.variables.getVariableByIdAsync('VariableID:130:6959'),orderDefault=await figma.variables.getVariableByIdAsync('VariableID:132:7001'),orderReverse=await figma.variables.getVariableByIdAsync('VariableID:79:5104');
const D={read:{title:'Read the primary source',done:readDone,open:readOpen,due:'Due Nov 3 · 30 min',ctx:'History seminar / Prepare discussion'},theme:{title:'Choose the seminar theme',done:themeDone,open:CT.themeIncomplete,due:'10 min',ctx:'History seminar / Prepare seminar discussion'},chapter:{title:'Summarize chapter 4',done:CT.chapterComplete,open:CT.chapterIncomplete,due:'Due Oct 30 · 25 min',ctx:'History seminar'}};
const titleKey=Object.fromEntries(Object.entries(D).map(([k,d])=>[d.title,k]));
const skipRoots=new Set(['6:2600','14:3706','14:3733']);
const roots=[];for(const id of new Set(Object.values(META.screens))){const f=await figma.getNodeByIdAsync(id);if(f?.type==='FRAME'){let p=f;while(p&&p.type!=='PAGE')p=p.parent;if(p?.id===PAGE_ID)roots.push(f);}}
const surfaces=[],pairRows=[],movedUnits=[],newGroups=[],warnings=[];
function allRows(n){return n.findAllWithCriteria({types:['INSTANCE']}).filter(r=>r.name.startsWith('Task / ')&&titleKey[r.name.slice(7)]);}
function gray(r){return r.mainComponent?.id===C.Completed.id;}
function inside(n,p){let a=n;while(a){if(a.id===p.id)return true;a=a.parent;}return false;}
function unit(row){return row.parent?.name.startsWith('Move visibility /')?row.parent:row;}
function auto(n){n.layoutPositioning='AUTO';n.layoutSizingHorizontal='FILL';if(n.type==='FRAME'&&n.layoutMode==='VERTICAL'){n.primaryAxisSizingMode='AUTO';n.layoutSizingVertical='HUG';}touch(n);return n;}
function disclosureUnit(scope){const d=scope.findAllWithCriteria({types:['INSTANCE']}).find(n=>n.name.startsWith('Disclosure / Completed'));if(!d)return null;let p=d;while(p.parent&&p.parent.id!==scope.id)p=p.parent;return p.parent?.id===scope.id?p:null;}
function completedGroup(host,name,always=false){let g=host.children.find(n=>n.name===name);if(g)return g;g=box('VERTICAL',name,Math.max(80,host.width-(host.paddingLeft||0)-(host.paddingRight||0)),null,null,0,4);add(host,g);auto(g);const disc=disclosureUnit(host);if(disc)host.insertChild(host.children.indexOf(disc)+1,g);else{const footer=host.children.find(n=>/Footer actions|Week footer|History footer/.test(n.name));if(footer)host.insertChild(host.children.indexOf(footer),g);}if(!always)g.setBoundVariable('visible',expanded);touch(g);newGroups.push(g.id);return g;}
function putGray(group,row,sunday){let u=unit(row);if(!inside(u,group)){group.appendChild(u);auto(u);movedUnits.push(u.id);}if(sunday&&row.name==='Task / '+D.read.title&&!u.name.startsWith('Move visibility /')){const w=box('VERTICAL','Move visibility / Completed Read on Sunday',u.width,null,null,0,0);group.insertChild(group.children.indexOf(u),w);add(w,u);w.setBoundVariable('visible',onSunday);auto(w);}row.setBoundVariable('visible',D[titleKey[row.name.slice(7)]].done);touch(row);return row;}
function newRow(container,key,weekly=false,completed=false,project=false){const d=D[key];const r=inst(container,completed?'Completed':weekly?'Weekly':'Active',completed?{Title:d.title}:weekly?{Title:d.title,Project:d.ctx,Context:d.due}:{Title:d.title,Context:project?d.due:d.ctx});r.name='Task / '+d.title;auto(r);r.setBoundVariable('visible',completed?d.done:d.open);touch(r);return r;}
function wrapMove(row){const p=row.parent,i=p.children.indexOf(row),w=box('VERTICAL','Move visibility / Restored Read on Sunday',row.width,null,null,0,0);p.insertChild(i,w);add(w,row);w.setBoundVariable('visible',onSunday);auto(w);return w;}
function restoreRead(active,weekly,sunday,project){
 const existing=active.findAllWithCriteria({types:['FRAME']}).filter(n=>n.name.startsWith('Manual order /'));
 if(existing.length){for(const g of existing){const outline=allRows(g).find(r=>r.name==='Task / Outline the discussion')||g.findAllWithCriteria({types:['INSTANCE']}).find(r=>r.name==='Task / Outline the discussion');if(!outline){warnings.push({scope:g.id,reason:'Manual group lacks Outline; inspect before restore'});continue;}const r=newRow(g,'read',weekly,false,project),u=sunday?wrapMove(r):r;let a=outline;while(a.parent&&a.parent!==g)a=a.parent;const index=g.children.indexOf(a)+(g.name.includes('Outline then Read')?1:0);g.insertChild(Math.max(0,index),u);pairRows.push(r.id);}return;}
 const outline=active.findAllWithCriteria({types:['INSTANCE']}).find(r=>r.name==='Task / Outline the discussion');
 if(sunday&&outline){let anchor=outline;while(anchor.parent&&anchor.parent!==active)anchor=anchor.parent;for(const [after,v,name]of[[false,orderDefault,'before Outline'],[true,orderReverse,'after Outline']]){const g=box('VERTICAL','Completion restored / Read '+name,active.width,null,null,0,0);add(active,g);g.setBoundVariable('visible',v);auto(g);const r=newRow(g,'read',weekly,false,project);wrapMove(r);const index=active.children.indexOf(anchor)+(after?1:0);active.insertChild(index,g);pairRows.push(r.id);}return;}
 const r=newRow(active,'read',weekly,false,project);active.insertChild(0,sunday?wrapMove(r):r);pairRows.push(r.id);
}
async function clearRowReactions(r){for(const n of[r,...r.findAll(()=>true)])if('reactions'in n&&n.reactions.length){await n.setReactionsAsync([]);touch(n);}}
function pair(surface){const {scope,active,host,keys,weekly,sunday,project,always}=surface;
 const group=completedGroup(host,'Completion pairs / '+surface.name,always);
 for(const key of keys){let candidates=allRows(scope).filter(r=>r.name==='Task / '+D[key].title),act=candidates.filter(r=>!gray(r)),done=candidates.filter(gray);
  if(!act.length){if(key==='read')restoreRead(active,weekly,sunday,project);else{const r=newRow(active,key,weekly,false,project);const sub=project&&key==='chapter'?active.children.find(n=>n.name==='Subtasks'):null;active.insertChild(sub?active.children.indexOf(sub)+1:0,r);pairRows.push(r.id);}act=allRows(scope).filter(r=>r.name==='Task / '+D[key].title&&!gray(r));}
  for(const r of act){r.setBoundVariable('visible',D[key].open);touch(r);}
  // Reuse every existing gray row ID; duplicate visible gray rows in the SAME
  // surface are hidden and reported instead of silently retaining double rows.
  if(!done.length){const r=newRow(group,key,false,true);if(sunday&&key==='read')putGray(group,r,true);done=[r];pairRows.push(r.id);}
  else{putGray(group,done[0],sunday);for(const duplicate of done.slice(1)){duplicate.visible=false;duplicate.setBoundVariable('visible',null);duplicate.name='Duplicate hidden / '+duplicate.name.slice(7);touch(duplicate);awaitClear.push(duplicate);warnings.push({row:duplicate.id,scope:scope.id,reason:'Duplicate gray row hidden; original ID retained'});}}
  const keep=done[0];keep.setBoundVariable('visible',D[key].done);touch(keep);surfaces.push({scope:scope.id,active:active.id,completedGroup:group.id,key,activeRows:act.map(r=>r.id),completedRow:keep.id,sunday,project});
 }
}
const awaitClear=[];
for(const f of roots){if(skipRoots.has(f.id))continue;
 // Each embedded Today backdrop is its own surface, separate from its drawer.
 for(const m of f.findAllWithCriteria({types:['FRAME']}).filter(n=>n.name==='Main content')){
  const today=m.children.find(n=>n.name==='Today’s tasks');if(today){const active=today.children.find(n=>n.name==='Scrollable rows')||today;pair({name:'Today completed work',scope:m,active,host:m,keys:['read','theme','chapter'],weekly:false,sunday:true,project:false,always:f.id==='5:4694'});m.clipsContent=true;m.overflowDirection='VERTICAL';today.primaryAxisSizingMode='AUTO';today.layoutSizingVertical='HUG';today.clipsContent=false;today.overflowDirection='NONE';active.primaryAxisSizingMode='AUTO';active.layoutSizingVertical='HUG';touch(m);touch(today);touch(active);continue;}
  const day=m.children.find(n=>n.name==='Day placements');if(day){const active=day.children.find(n=>n.name==='Scrollable rows')||day;const sunday=m.findAllWithCriteria({types:['TEXT']}).some(t=>t.characters==='Sunday, Nov 1');const keys=sunday?['read','theme','chapter']:allRows(active).some(r=>r.name==='Task / '+D.read.title)?['read']:[];if(keys.length)pair({name:'Day completed work',scope:m,active,host:active,keys,weekly:true,sunday,project:false,always:f.name==='Week completed'});}
 }
 // Foreground Active projects: parent children and standalone leaves have
 // different bodies. Done remains a live completed-only index, so no active
 // counterpart is injected into Done or its previous-week/unplanned views.
 if(f.name.startsWith('Done'))continue;
 for(const drawer of f.findAllWithCriteria({types:['FRAME']}).filter(n=>n.name==='Project drawer')){
  const body=drawer.findAllWithCriteria({types:['FRAME']}).find(n=>n.name==='Project task groups');if(!body)continue;
  const sub=body.children.find(n=>n.name==='Subtasks');
  if(sub){pair({name:'Parent completed children',scope:sub,active:sub,host:sub,keys:['read','theme'],weekly:false,sunday:false,project:true,always:false});pair({name:'Standalone completed work',scope:body,active:body,host:body,keys:['chapter'],weekly:false,sunday:false,project:true,always:false});}
  else if(allRows(body).some(r=>r.name==='Task / '+D.read.title||r.name==='Task / '+D.theme.title))pair({name:'Parent completed children',scope:body,active:body,host:body,keys:['read','theme'],weekly:false,sunday:false,project:true,always:true});
 }
}
for(const r of awaitClear)await clearRowReactions(r);
return done({pairingCount:surfaces.length,pairing:surfaces.slice(0,12),addedRowIds:pairRows,movedGrayUnits:movedUnits,newCompletedGroups:newGroups,warnings,completionIntegration:{expandOnComplete:[META.stateVariables.completedExpanded,META.stateVariables.completedCollapsed],requiredActions:'On supported active-row completion set completedExpanded=true and completedCollapsed=false before final derived sync; checkbox mutation stays in-place. Existing Completed controls may collapse again.',runAfter:'Run refine-completion-draft.js then root generic Start/nav wiring. All new row checkbox actions are assigned there.'},notes:['No current task identity, deadline, completion or session defaults changed.','Frozen/source history roots and carryover selection rows are excluded.','Current Done gets no active counterparts; reopening removes it from Done.','Render Today default/expanded, paused timer, compact Week and Project-child surfaces after execution; inspect default/reverse order and moved Sunday before accepting.']});

