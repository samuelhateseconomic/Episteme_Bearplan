# R21 resumed visual check — November 2, 2026

Read-only independent review. Root remains sole Figma writer.

File: jobFe4sXDot7BKsej0arNB; session8ac12b29-2135-4b7a-8c4c-fd2b515b445b.
Reviewed current default rendered800×900 Light frames: Today5:3972, children5:5292, Week6:1802. These captures precede root's resumed fixes.

## Findings

- Child placement passes: Read is the first child, Outline the second, gray struck-through Theme the third. No dropped child or duplicate Read appears in the rendered view.
- Today has8 readable active rows and2compact completed rows. Long reflection title fits. No overlapping Start controls or visible duplicate Read.
- Week retains clear selected-placement context, grip at project context, due/estimate, unique2of11/18%, Previous/Today/Next and EndWeek atbottomright. The body truncates below fold inside its intended scroll region; actualscroll remains unverified.
- P2: Today Completed chevron pointsright while2grayrows areexpanded. Earlier unfinished lies below thisviewport under theexpandeddefaults. Root is reconciling disclosure state.
- P2: Today manual-order cue is absent in staticrender. Text64:4633 (andchildbackdrop64:4654) bindsvar124:5785, whose9:4default remains8unfinished·2complete. Entryactions alone do notrepair designrenderdefaults.
- P2: Week still visibly duplicatesHistory. Top6:1821 andfooter6:1929 arebothvisibletrue;footerparent6:1928. Root to retainone.
- P2: Childdrawerheading5:5337 under5:5334 still saysPrepare discussion while canonicalfixture saysPrepare seminar discussion. Of11scoped liveProjects/Done/child/taskeditor roots checked, thisis theonly exactshortenedheading found. Preserve naturalheight when replacing; currenttitle shares availablewidth withBack.

No new staticP1 found in thislimiteddefaultscope. This is not finalR22 or runtime/user acceptance. Repeat only affected compositions afterroot's fixes.

## Post-fix check (second capture)

Today5:3972 passes: Yourordercue visible,8active rows unchanged,Completedcollapsed correctly, Earlierunfinished immediatelyvisible. Week6:1802 passes duplicateHistoryrepair;EndWeekretainsbottomright. Completedbody148:7907bindsexpanded28:4603;collapsed6:1919bindsinverse28:4604;expanded164:8478binds28:4603/component164:8311. Expandedcomponent164:8311rendersadownchevron. Hiddeninstance164:8316cannotrenderindependently(1×1),socomponentvisualused.

Child5:5292introducedaheaderregressionaftercanonicaltitlewrap:Header5:5335fixedheight58containsHeading5:5336natural90atlocaly−16. Context5:5338('1of3complete')overflowsintoscroll81:5203startingy90andisclipped. Suggestedrepair:ViewheadingcrossaxisAUTO/verticalHUGtoserve90pxheight;keepProjecttaskscrollFILLsofooterstaysat836. Rootnotified;finalrecheckpending. Parentcompletedchildren148:7806alwaysvisibleisappropriateforthisdirectchildlistwithoutadisclosure.

## Post-fix check (third capture)

Child5:5292headerrepairpasses:canonicaltitlewrapswithoutclipping,progressfullyvisible,Readremainsfirst,footerstable. Launcher141:7346passes800×900Light:8buttonsfitinfourpairedrows,backgroundcorrect,sampleboundaries/pendingverificationvisible. Shopfailed7:2980balance33alignswithbaselineandRefresherrorcopyisreadable. Forest7:2879capturedtask/contextwrapclearlyandthreeexistingcardsfit. Finished7:2827alllabelsfit;bindingreadbackconfirmsfocus18:4759,savedcontext155:8300,savedtask155:8299,wallet18:4760;purchaseavailable7:2998binds18:4761. Staticfinisheddefault12minutesalongside45/33isnotexecutedentryevidence.

Requiredfindingfromadditionalerrorcapture5:4694:Feedback5:4843atlocaly932h68liesinsideMaincontent5:4708height840scroll;Retryisthereforebelowinitialviewport. EntryseedingReadcompletewillnotreclaimenoughspaceafterthreecompactcompletedrows.Rootnotifiedtopinfeedback/retryoutsideorsituatethefeedbackbeforetheworklist. Retryitselfiswiredwith88actions;thisisvisibilitynotmissinghandler.

Potentialdead-controlfinding:purchasefailure7:3008Action/Buy·30hasreactions0butrendersoutlined/enabled. IfRefreshisrequiredfirst,visuallydisablethebuttonandstatewhy.Theboundedprototypeissuccesspurchaseunsupported;donovertattestpurchase.

NoothernewP1observedinthesefivepost-fixcompositions.Errorandpurchaseaffordancefindingsawaitrootrepairandrecheck.NewadditiveForestcard166:5720ishiddenbydefault;rootwillrenderafter-saveexampleforreview.

## Fourth capture — final targeted recovery and downstream views

Rendered 800×900 Light: Reopen failed5:4694, purchase failed7:2980, closed week6:2600, carryover choices6:2634, Stats7:3036, reverse reorder147:7536.

Reopen feedback/Retry now stays visibly pinned under top navigation; this repairs the required recovery visibility finding. Purchase failure now visually disables Buy controls and preserves readable Refresh balance recovery; this repairs the actionable-control appearance finding.

Closed week keeps frozen-at-closure status distinct from current Read status, with footer current-task and carryover actions visible. Historical card metadata wraps naturally. Carryover cards retain selection, project/parent, unchanged deadline and suggested next-week date; Cancel/Review stay outside the list viewport. Stats separates saved time, finalized sessions, current leaf completion and frozen Missed; disclosure controls and correction entry fit. No extra required static finding in these views. Scroll-body cutoffs are intentional geometry; actual scrolling remains unverified.

Reverse reorder147:7536 has one required static clarity finding: Cancel overlaps the disabled 'Move down · last item' label; that boundary claim is also false because Read is second among eight active tasks. Exact unsupported disabled control147:7579. Suggested minimal repair: hide that control, retain Cancel/Move up with spacing. Selected Read, its insertion cue above Outline and resulting current order otherwise read clearly. Root notified; final reverse recheck pending.
