// DRAFT ONLY — NOT EXECUTED. Root is sole Figma writer.
// Preserve all3 baseline card IDs; add one separate finite saved-session card.
// Existing first Today12card is mapped to fixture session-read-saved (known Read).
// No task/project attribution is invented for Oct31/Oct30 aggregate-only cards.
// Requires figma-use, figma-generate-design, figma-generate-library.
await figma.setCurrentPageAsync(await figma.getNodeByIdAsync('2:5'));
const forest=await figma.getNodeByIdAsync('7:2879');
const main=await figma.getNodeByIdAsync('7:2893');
const row=await figma.getNodeByIdAsync('7:2900');
const baseline=await figma.getNodeByIdAsync('7:2901');
const titleTemplate=await figma.getNodeByIdAsync('7:2905');
const contextTemplate=await figma.getNodeByIdAsync('7:2906');
const collection=await figma.variables.getVariableCollectionByIdAsync('VariableCollectionId:9:6181');
const focus=await figma.variables.getVariableByIdAsync('VariableID:18:4759');
const savedTask=await figma.variables.getVariableByIdAsync('VariableID:155:8299');
const savedContext=await figma.variables.getVariableByIdAsync('VariableID:155:8300');
const gap16=await figma.variables.getVariableByIdAsync('VariableID:2:47');
const gap4=await figma.variables.getVariableByIdAsync('VariableID:2:44');
if(!forest||!main||!row||!baseline||titleTemplate?.type!=='TEXT'||contextTemplate?.type!=='TEXT'||!collection||!focus||!savedTask||!savedContext||!gap16||!gap4)throw Error('Forest identities changed; reconcile.');
if(main.children.some(n=>n.name==='Tree / New demo saved session'))throw Error('Forest newcard already exists; reconcile rather than replay.');
const local=await figma.variables.getLocalVariablesAsync();
if(local.some(v=>v.name==='Forest / New demo saved session visible'||v.name==='Forest / Baseline Read confirmed date'))throw Error('Forest variables already exist; reconcile.');
for(const t of baseline.findAllWithCriteria({types:['TEXT']}))for(const seg of t.getStyledTextSegments(['fontName']))await figma.loadFontAsync(seg.fontName);
const mode=collection.defaultModeId,createdVariables=[],defaults={};
function variable(name,type,value){const v=figma.variables.createVariable(name,collection,type);v.scopes=type==='STRING'?['TEXT_CONTENT']:['ALL_SCOPES'];v.hiddenFromPublishing=true;v.setValueForMode(mode,value);createdVariables.push(v.id);defaults[v.id]=value;return v;}
const visible=variable('Forest / New demo saved session visible','BOOLEAN',false);
const baselineDate=variable('Forest / Baseline Read confirmed date','STRING','Today · 12 min');
const created=[],changed=new Set();
function track(n){created.push(n.id);return n;}
function rememberTree(n){created.push(n.id,...n.findAll(()=>true).map(c=>c.id));}
function wrapText(n,parent,width){parent.appendChild(n);n.textAutoResize='HEIGHT';n.resize(width,n.height);n.layoutSizingHorizontal='FILL';return n;}

// The new tree is a fourth record, separate from prior saved Read.
// Clone retains editable SVG artwork, semantic fills, radii and padding.
const card=baseline.clone();rememberTree(card);card.name='Tree / New demo saved session';
main.insertChild(main.children.indexOf(row),card);changed.add(main.id);
card.layoutMode='HORIZONTAL';card.resize(main.width-main.paddingLeft-main.paddingRight,156);
card.primaryAxisSizingMode='FIXED';card.counterAxisSizingMode='AUTO';
card.layoutSizingHorizontal='FILL';card.layoutSizingVertical='HUG';
card.primaryAxisAlignItems='MIN';card.counterAxisAlignItems='MIN';
card.setBoundVariable('itemSpacing',gap16);card.setBoundVariable('visible',visible);
const original=[...card.children],art=original.find(n=>n.type==='FRAME');
if(!art)throw Error('Cloned editable Pine artwork missing.');
const inheritedTexts=original.filter(n=>n.type==='TEXT');
if(inheritedTexts.length!==3)throw Error('Unexpected baseline card text structure.');
const details=track(figma.createAutoLayout('VERTICAL'));details.name='Saved session context';
details.fills=[];details.resize(592,108);card.appendChild(details);
details.primaryAxisSizingMode='AUTO';details.counterAxisSizingMode='FIXED';
details.layoutSizingHorizontal='FILL';details.layoutSizingVertical='HUG';
details.setBoundVariable('itemSpacing',gap4);
const detailWidth=card.width-card.paddingLeft-card.paddingRight-art.width-16;
for(const text of inheritedTexts)wrapText(text,details,detailWidth);
const newTitle=track(titleTemplate.clone());newTitle.name='Captured saved task';
wrapText(newTitle,details,detailWidth);details.insertChild(0,newTitle);
newTitle.setBoundVariable('characters',savedTask);
const newContext=track(contextTemplate.clone());newContext.name='Captured saved project and parent';
wrapText(newContext,details,detailWidth);details.insertChild(1,newContext);
newContext.setBoundVariable('characters',savedContext);
// Inherited Pine/Today12/Unfinished strings remain the finite12-minute new save.
for(const t of inheritedTexts)if(t.characters==='Today · 12 min')t.characters='Today · 12 min confirmed';

// Attribute the fixture's known prior Read session, without changing its identity.
const priorTask=track(titleTemplate.clone());priorTask.name='Frozen baseline saved task / Read';
wrapText(priorTask,baseline,baseline.width-baseline.paddingLeft-baseline.paddingRight);
priorTask.characters='Read the primary source';baseline.insertChild(2,priorTask);
const priorContext=track(contextTemplate.clone());priorContext.name='Frozen baseline saved context';
wrapText(priorContext,baseline,baseline.width-baseline.paddingLeft-baseline.paddingRight);
priorContext.characters='History seminar / Prepare seminar discussion';baseline.insertChild(3,priorContext);
contextTemplate.setBoundVariable('characters',baselineDate);changed.add(contextTemplate.id);
baseline.primaryAxisSizingMode='AUTO';baseline.layoutSizingVertical='HUG';changed.add(baseline.id);
row.counterAxisSizingMode='AUTO';row.layoutSizingVertical='HUG';changed.add(row.id);

// Derive visibility/time on entry only. Keep captures owned by successful Finish.
// One IF per action: compatible with installed native conditional constraints.
function lit(value){const type=typeof value==='boolean'?'BOOLEAN':'STRING';return {type,resolvedType:type,value};}
function alias(v){return {type:'VARIABLE_ALIAS',resolvedType:v.resolvedType,value:{type:'VARIABLE_ALIAS',id:v.id}};}
function eq(value){return {type:'EXPRESSION',resolvedType:'BOOLEAN',value:{expressionFunction:'EQUALS',expressionArguments:[alias(focus),lit(value)]}};}
function or(a,b){return {type:'EXPRESSION',resolvedType:'BOOLEAN',value:{expressionFunction:'OR',expressionArguments:[a,b]}};}
function set(v,value){return {type:'SET_VARIABLE',variableId:v.id,variableValue:lit(value)};}
function iff(condition,actions){return {type:'CONDITIONAL',conditionalBlocks:[{condition,actions}]};}
const derive=[set(visible,false),set(baselineDate,'Today · 12 min'),
 iff(or(eq('57 / 60 min saved today'),eq('55 / 60 min saved today')),[set(visible,true)]),
 iff(or(eq('43 / 60 min saved today'),eq('55 / 60 min saved today')),[set(baselineDate,'Today · 10 min')])];
const reactions=JSON.parse(JSON.stringify(forest.reactions||[])),index=reactions.findIndex(r=>r.trigger?.type==='AFTER_TIMEOUT');
if(index>=0)reactions[index]={...reactions[index],actions:[...derive,...reactions[index].actions]};
else reactions.push({trigger:{type:'AFTER_TIMEOUT',timeout:.01},actions:derive});
await forest.setReactionsAsync(reactions);changed.add(forest.id);
return {createdNodeIds:[...new Set(created)],mutatedNodeIds:[...changed],createdVariableIds:createdVariables,
 prototypeVariableDefaults:defaults,newSavedTree:card.id,newSavedTreeVisible:visible.id,baselineReadDate:baselineDate.id,
 baselineCardIds:['7:2901','7:2908','7:2915'],newCard:{width:card.width,height:card.height,task:newTitle.id,context:newContext.id},
 limitations:['Finite first12-minute save only; use55/57 to show it and43/45 to hide it.',
 'Reset must include both new variable defaults.',
 'Oct31/Oct30 cards retained unchanged: their individual task/project records were not provided by the aggregate fixture.',
 'Verify render at baseline and after firstsave/correction; no browser-click claim.']};
