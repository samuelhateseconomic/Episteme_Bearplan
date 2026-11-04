// Executed construction record; DO NOT REPLAY. Reconcile live IDs in inventory.json.

await figma.setCurrentPageAsync(await figma.getNodeByIdAsync('2:5'));
if(figma.currentPage.findOne(n=>n.name==='13 · Google — sign-in file')) throw new Error('UX-C04 already exists; reconcile before retry.');
const created=[], frames={}, buttons={}, texts={}, sections={};
const fonts=[{family:'Inter',style:'Regular'},{family:'Inter',style:'Medium'},{family:'Inter',style:'Semi Bold'}];
await Promise.all(fonts.map(f=>figma.loadFontAsync(f)));
const assets={};for(const id of ['3:198','3:213','3:228','3:207','3:210','233:6184']) assets[id]=await figma.getNodeByIdAsync(id);
const vars={};for(const key of ['33','34','35','36','40','41','45','46','47','48','55']) vars[key]=await figma.variables.getVariableByIdAsync('VariableID:2:'+key);
const styles={title:'S:79851d0363784e2629aa8c1a07a66ce2367b5b15,',heading:'S:3f921ebfce0e917b8598299e7c8457ef51e5013e,',body:'S:a4fb236894d8e3b302e56ff5558b2a07b654eb24,',context:'S:b3cf6bba360bfae78018718af859ef7006f5ebcf,',label:'S:8d4da908df3484d5bd346377a06ae3b99b781980,'};
function track(n){created.push(n.id);return n;}
function paint(key){return figma.variables.setBoundVariableForPaint({type:'SOLID',color:{r:0,g:0,b:0}},'color',vars[key]);}
function gap(n,key){n.setBoundVariable('itemSpacing',vars[key]);}
function pad(n,key){for(const k of ['paddingTop','paddingRight','paddingBottom','paddingLeft'])n.setBoundVariable(k,vars[key]);}
async function txt(parent,key,value,style='body',tone='34'){
 const t=track(figma.createText());parent.appendChild(t);t.fontName=fonts[0];await t.setTextStyleIdAsync(styles[style]);t.characters=value;t.name=key;t.fills=[paint(tone)];t.textAutoResize='HEIGHT';t.resize(parent.width-parent.paddingLeft-parent.paddingRight,20);t.layoutSizingHorizontal='FILL';t.layoutSizingVertical='HUG';return t;
}
function sec(key,title,x,y,w,h){const s=track(figma.createSection());figma.currentPage.appendChild(s);s.name=title;s.x=x;s.y=y;s.resizeWithoutConstraints(w,h);sections[key]=s;return s;}
sec('file','13 · Google — sign-in file',21100,3300,2580,2800);
sec('auth','14 · Google — browser sign-in & recovery',24000,3300,2580,2800);
sec('cal','15 · Google — calendars, sync & account review',26900,3300,2580,2800);
const scopes=[
 ['Calendars to show','Read events from calendars you select. Your personal calendars stay unchanged.'],
 ['BearPlans calendar','Publish timed plans to its own calendar, with a reminder 30 minutes before.'],
 ['Google Tasks','Copy every local project, task and subtask to Google Tasks, including tasks added from bCourses. Completion returns here; other Google edits are replaced.']
];
const spec=[
 ['file','setup','Set up Google','Choose a Google Desktop app sign-in JSON file. Its contents stay hidden.',[],[['Close','close'],['Setup help','help','secondary'],['Choose file','selectedFresh','primary']],'This prototype uses fixed sample files. It does not open a file picker or contact Google.'],
 ['file','selectedFresh','Review sign-in file','Sample file selected · Desktop app JSON',[],[['Cancel','close'],['Choose another','setup','secondary'],['Save file','savingFresh','primary']],'Saving checks the file format only. Google sign-in and permissions come next.'],
 ['file','selectedSame','Replace sign-in file','The selected file belongs to the same Google client.',[],[['Cancel','close'],['Save file','savingSame','primary']],'Your existing sign-in is retained. This does not recheck access or clear earlier errors.'],
 ['file','selectedDifferent','Use a different sign-in file?','This file belongs to a different Google client.',[],[['Cancel','close'],['Replace file','savingDifferent','primary']],'Replacing it signs Google out here and cancels a pending sign-in. Sign in again afterwards. Local tasks and remote copies remain.'],
 ['file','savingFresh','Saving sign-in file…','Checking and saving the selected Desktop app file.',[],[['Saving…',null,'busy']],'Wait for confirmation. A lost response may need a status check.'],
 ['file','savingSame','Saving replacement…','Keeping sign-in for the same Google client.',[],[['Saving…',null,'busy']]],
 ['file','savingDifferent','Replacing setup…','Saving the new file, then signing out the old client here.',[],[['Replacing…',null,'busy']],'Wait for the result before signing in again.'],
 ['file','ready','Setup ready · sign-in needed','The Desktop app file was saved. No Google account has been authorized yet.',[],[['Close','close'],['Review connection','consent','primary']],'A valid file does not prove working APIs or permissions.'],
 ['file','sameSaved','File saved · sign-in retained','The same Google client is still signed in. Access has not been rechecked.',[],[['Close','close'],['Google controls','controls','primary']],'Any existing reconnect or sync issue still needs attention.'],
 ['file','wrongType','Choose a Desktop app file','This sample is a Web application credential. It cannot be used here.',[],[['Cancel','close'],['Choose another','selectedFresh','primary']],'Previous setup and sign-in were kept. Download a Desktop app JSON file instead.','error'],
 ['file','malformed','The file could not be read','Choose a complete Google Desktop app JSON file with valid Google addresses.',[],[['Cancel','close'],['Choose another','selectedFresh','primary']],'Previous setup and sign-in were kept. File contents are not displayed.','error'],
 ['file','oversized','The file is too large','Choose a Desktop app sign-in file no larger than 32 KB.',[],[['Cancel','close'],['Choose another','selectedFresh','primary']],'Previous setup and sign-in were kept.','error'],
 ['file','saveFailed','Could not save this file','Saving failed before the previous setup was replaced.',[],[['Cancel','close'],['Retry','savingDifferent','primary']],'The old file and sign-in remain. The selected sample file is retained for retry.','error'],
 ['file','saveUnknown','Setup save not confirmed','The response was lost after saving may have started.',[],[['Close','close'],['Check status','ready','secondary'],['Save again','savingDifferent','primary']],'Check saved setup before continuing. Do not assume the old client or sign-in was retained.','error'],
 ['file','help','Prepare a sign-in file','In Google Cloud, use an OAuth client of type Desktop app and download its JSON file.',[['Required services','Enable Google Calendar API and Google Tasks API. Configure the consent screen and add your Google account as a test user if the project is in testing.'],['Keep it private','Choose the file in BearPlans. No client ID, secret or token is shown in Settings.']],[['Back','setup']],'The source checks format and Google addresses. Sign-in and the first sync reveal authorization or API problems.'],
 ['file','selectedSameExpired','Replace file · reconnect still needed','The selected file belongs to the same Google client.',[],[['Cancel','close'],['Save file','sameExpiredSaved','primary']],'Saving preserves the earlier reconnect requirement. It does not make expired access valid.'],
 ['file','sameExpiredSaved','File saved · reconnect needed','The same-client setup file was saved. The earlier access issue remains.',[],[['Close','close'],['Reconnect','consent','primary']],'Reconnect in your browser to check access.'],
 ['auth','consent','Connect Google','After sign-in, automatic sync can begin while BearPlans is running, awake and online.',scopes,[['Not now','close'],['Continue with Google','waiting','primary']],'Copies of local work are sent to Google. Calendar selection controls reads only; it does not limit task export.'],
 ['auth','waiting','Waiting for Google sign-in','Finish sign-in and grant the requested permissions in your system browser. Then return to BearPlans.',[],[['Back to Settings','pendingControls'],['Open sign-in','fallback','secondary']],'This dialog can close while sign-in continues. Keep BearPlans running; the attempt expires after five minutes.'],
 ['auth','fallback','Open sign-in in your browser','If no browser window appeared, use Open sign-in again for the current attempt.',[],[['Back to Settings','pendingControls'],['Open sign-in','browserBoundary','primary']],'This prototype never opens Google. The next view represents the external-browser boundary.'],
 ['auth','browserBoundary','Continue in your system browser','Google owns the account and permission screens. BearPlans never asks for your Google password.',[],[['Return to waiting','waiting']],'Prototype boundary only. Choose a simulated outcome from the canvas review guide.'],
 ['auth','pendingControls','Google sign-in is still pending','Returning to Settings did not cancel the browser attempt.',[],[['Close Settings','close'],['View sign-in','waiting','secondary'],['Start again','restartReview','primary']],'Starting again replaces the pending attempt. A late result from the earlier attempt must not reconnect it.'],
 ['auth','restartReview','Start a new sign-in?','The pending attempt will be invalidated before a new one starts.',[],[['Keep waiting','waiting'],['Start again','waiting','primary']],'Any existing saved connection is retained unless a new sign-in succeeds.'],
 ['auth','denied','Sign-in was not completed','Google sign-in was declined, canceled in the browser or did not match the pending attempt.',[],[['Close','close'],['Try again','consent','primary']],'The setup file remains. An existing saved sign-in was not replaced.','error'],
 ['auth','timeout','Sign-in timed out','No completed sign-in was received within five minutes.',[],[['Close','close'],['Try again','consent','primary']],'Keep BearPlans open during sign-in. A new attempt invalidates the previous one.','error'],
 ['auth','permissions','More permissions are needed','A Google sign-in was saved, but some required access is missing.',[['Missing access in this example','Google Tasks. Reconnect and grant every requested permission so the three functions can work.']],[['Close','close'],['Reconnect','consent','primary']],'Some provider work may have succeeded. This is not a successful combined sync.','error'],
 ['auth','expired','Reconnect Google','Saved access is expired or revoked. Local tasks and cached events remain available.',[],[['Close','close'],['Reconnect','consent','primary']],'Sign in to the same account to retain its existing links. A different account requires review.','error'],
 ['auth','authorized','Signed in · sync not confirmed','Google authorization was received. The first combined sync has not been confirmed.',[],[['Close','close'],['Choose calendars','calLoading','primary']],'Automatic task export and timed-plan publishing can run before you choose calendars.'],
 ['auth','unavailable','Could not confirm sign-in','Google or the local sign-in service could not finish the request.',[],[['Close','close'],['Check status','controls','secondary'],['Try again','consent','primary']],'Saved setup and local work remain. Check connection status before assuming that sign-in changed.','error'],
 ['cal','controls','Google connection','Manage sign-in and the calendars whose events appear in Plan.',[],[['Close','close'],['Replace file','selectedSame','secondary'],['Choose calendars','calLoading','primary']],'All local tasks are exported. Calendar selection changes reading only. Pause and Disconnect are covered in the next design unit.'],
 ['cal','calLoading','Loading calendars…','Reading available calendars from Google.',[],[['Loading…',null,'busy']],'This is provider work. Local tasks remain usable.'],
 ['cal','calTwo','Calendars to show','Choose the calendars whose events appear beside your planned day.',[],[['Cancel','controls'],['Save calendars','calSaving','primary']],'Saving reads events once. It does not add tasks or limit Google Tasks export.'],
 ['cal','calOne','Calendars to show','Choose the calendars whose events appear beside your planned day.',[],[['Cancel','controls'],['Save calendars','calSaving','primary']],'Saving reads events once. It does not add tasks or limit Google Tasks export.'],
 ['cal','calSaving','Saving calendar choices…','Saving the selection, then reading its events.',[],[['Saving…',null,'busy']],'These are separate steps. A later event-read failure does not undo saved choices.'],
 ['cal','calSaved','Calendar choices saved','Events from selected calendars can appear beside Plan days. Nothing was added as a task.',[],[['Close','close'],['Check first sync','firstSync','primary']],'Calendar choice does not limit all-task export or publishing timed plans.'],
 ['cal','calEmpty','No calendars available','Google returned no calendars to show.',[],[['Close','close'],['Refresh list','calLoading','primary']],'Task export and BearPlans-calendar publishing have separate outcomes.'],
 ['cal','calError','Could not load calendars','Saved choices and cached events remain. The list could not be refreshed.',[],[['Close','close'],['Retry','calLoading','primary']],'This does not prove that Google Tasks or publishing failed too.','error'],
 ['cal','calRefreshFailed','Choices saved · events not refreshed','Your calendar selection was saved, but fetching its events failed.',[],[['Close','close'],['Retry refresh','calSaved','primary']],'Retry only the event read. Do not ask the user to save the selection again.','error'],
 ['cal','firstSync','Checking Google sync…','Reading selected calendars, publishing timed plans and syncing Google Tasks.',[],[['Checking…',null,'busy']],'Already-written provider changes are not rolled back if another step fails.'],
 ['cal','synced','First sync succeeded','The combined Google sync completed successfully.',[],[['Close','close'],['Google controls','controls','secondary']],'Last successful sync · just now. Local edits, remote task completion and owned-calendar publishing retain their normal rules.'],
 ['cal','partial','Sync needs attention','Some Google changes may already have succeeded. The combined sync did not finish.',[],[['Close','close'],['Retry sync','firstSync','primary']],'Retry reconciles the same linked work. It must not duplicate tasks or events.','error'],
 ['cal','otherAccount','A different Google account is signed in','Sync is blocked before using the previous account’s links.',[],[['Close','close'],['Sign in to previous','consent','secondary'],['Review account','adoptReview','primary']],'Your local tasks and remote copies remain. No account email is available to display.','error'],
 ['cal','adoptReview','Start links in this account?','Using this account clears the old account’s local sync links and cached calendar choices.',[],[['Keep previous links','otherAccount'],['Use this account','adopted','primary']],'Local tasks, focus history and tasks added from events stay. Nothing is deleted in either Google account. Next sync creates fresh remote links; review calendars again.'],
 ['cal','adopted','Account change saved · sync pending','Local sync links were reset for the account now signed in.',[],[['Close','close'],['Choose calendars','calLoading','primary']],'No new sync is claimed yet. Earlier remote lists/events remain in the previous account.']
];
for(const [group,key,title,body,rows,actions,note,tone] of spec){
 const f=track((await figma.getNodeByIdAsync('234:6389')).clone());for(const c of [...f.children])c.remove();sections[group].appendChild(f);f.name='Google / '+key;f.resize(540,100);f.layoutSizingHorizontal='FIXED';f.layoutSizingVertical='HUG';f.fills=[paint('33')];f.strokes=[paint('36')];f.strokeWeight=1;f.cornerRadius=12;for(const p of ['topLeftRadius','topRightRadius','bottomLeftRadius','bottomRightRadius'])f.setBoundVariable(p,vars['55']);pad(f,'48');gap(f,'47');f.clipsContent=false;
 frames[key]=f;buttons[key]={};texts[key]={};
 await txt(f,'Provider context','Settings / Google','context','35');
 await txt(f,'Dialog heading',title,'title');
 texts[key].body=(await txt(f,'Purpose and consequence',body,'body',tone==='error'?'40':'34')).id;
 for(const [h,b]of rows){const r=track(figma.createAutoLayout('VERTICAL'));f.appendChild(r);r.resize(492,20);r.layoutSizingHorizontal='FILL';r.layoutSizingVertical='HUG';r.fills=[];gap(r,'45');await txt(r,'Section heading',h,'heading');await txt(r,'Section detail',b,'context','35');}
 if(key==='calTwo'||key==='calOne'){
  texts[key].selection=(await txt(f,'Draft count',key==='calTwo'?'2 selected':'1 selected','context','35')).id;
  for(const [idx,name,context]of [[0,'Personal','Main calendar · Read only'],[1,'Classes','Read only']]){
   const row=track(assets['233:6184'].createInstance());f.appendChild(row);row.name='Calendar option / '+name;row.setProperties({'Course#233:0':name,'Term#233:1':context});row.layoutSizingHorizontal='FILL';row.layoutSizingVertical='HUG';
   const cb=row.findAllWithCriteria({types:['INSTANCE']}).find(n=>n.name==='Selection');
   if(idx===1&&key==='calOne'){const unchecked=await figma.getNodeByIdAsync('3:249');if(unchecked?.type==='COMPONENT')cb.swapComponent(unchecked);}
   buttons[key]['calendar'+idx]=row.id;
  }
 }
 if(note)await txt(f,'Context and recovery',note,'context','35');
 const bar=track(figma.createAutoLayout('HORIZONTAL'));f.appendChild(bar);bar.name='Dialog actions';bar.resize(492,36);bar.layoutSizingHorizontal='FILL';bar.layoutSizingVertical='HUG';bar.fills=[];gap(bar,'46');bar.counterAxisAlignItems='CENTER';bar.primaryAxisAlignItems='MAX';
 for(const [label,dest,t='quiet'] of actions){
  const id={primary:'3:198',secondary:'3:213',quiet:'3:228',busy:'3:210'}[t];const b=track(assets[id].createInstance());bar.appendChild(b);b.name=(t==='busy'?'Busy / ':'Action / ')+label;b.setProperties({'Label#3:54':label});buttons[key][label]={id:b.id,dest};for(const child of b.findAll(()=>true))created.push(child.id);
 }
}
for(const group of Object.keys(sections)){
 const groupFrames=spec.filter(s=>s[0]===group).map(s=>frames[s[1]]);let y=80;
 for(let i=0;i<groupFrames.length;i+=4){let height=0;for(let j=0;j<4&&i+j<groupFrames.length;j++){const f=groupFrames[i+j];f.x=60+j*620;f.y=y;height=Math.max(height,f.height);}y+=height+100;}
 sections[group].resizeWithoutConstraints(2580,y+40);
}
const all=Object.values(frames).flatMap(f=>[f,...f.findAll(()=>true)]);for(const n of all)if(!created.includes(n.id))created.push(n.id);
return {createdNodeIds:created,sections:Object.fromEntries(Object.entries(sections).map(([k,n])=>[k,{id:n.id,name:n.name,x:n.x,y:n.y,width:n.width,height:n.height}])),frames:Object.fromEntries(Object.entries(frames).map(([k,n])=>[k,{id:n.id,width:n.width,height:n.height}])),buttons,texts,specCount:spec.length,styles};
