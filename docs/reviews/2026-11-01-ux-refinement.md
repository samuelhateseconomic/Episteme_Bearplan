# BearPlans — prototype refinement execution

Started November 1 and continued November 2, 2026. Synthetic service-day fixture remains November 1. macOS 26.6.2 / Darwin arm64. Existing Figma file `jobFe4sXDot7BKsej0arNB`, session `8ac12b29-2135-4b7a-8c4c-fd2b515b445b`. User authorized applying the repair plan. Design and evidence only; application source/data remain separately owned.

## Baseline — UX-R01

Inspected current shared guidance, plans, ledger, Git status/diffs and live canvas. Preserved 75 screen IDs in nine Sections, ten named starts and Inter fallback. Native editable nodes and semantic variables reused. External pre-edit manifest/reaction signatures saved in `/private/tmp/bearplans-figma-20261101/refinement-baseline.json`. Two broad reads exceeded the return limit without writes; narrowed successful manifest returned75 roots and per-root signatures.

Latest discrepancy: Assistant carryover now exists in app commit81f5922 with Undo. Read-only Figma sample remains a deliberate subset. Carryover same-weekday preselection, immediate choices and frozen Missed rules govern repairs. Concurrent bCourses work is unrelated and preserved; no secrets/user DB inspected.

## Checks and evidence

Execution in progress. Static structural/visual evidence will be recorded per repair. Actual browser execution, keyboard/screen-reader/reflow and user acceptance remain separate gates.

## Fixture — UX-R02

Independent product reviewer defined [synthetic fixture](../../frontend/design/ux-refinement-fixture.json):25 current leaves/9complete,11 unique source leaves/12placements,2complete18%,9 eligible carryover defaults. Parent excluded; duplicated title distinguished by project. Previous closed week has1unfinished leaf/Missed1; source closure adds9, overall10. DefaultRead dueNov3/30min; OutlineNov4/20; TestNov4/30. Session branches distinguish12-minute normal finish from2trusted/5gap/28remaining recovery. Saved history facts intentionally differ. Arithmetic verified independently.

## Current task facts — UX-R03

Corrected323 instance-property sets on Canvas · Flows and46 on Screens using the fixture, including hidden variants/accessibility context. Outline is dueNov4/20min; TestNov4/30; other source dates retained. All read-back fonts Inter. Historical free text untouched for deliberate frozen-context repair inR12. No screen IDs or reaction trees changed. Structural property results captured in the execution ledger; visual dependents follow inR04–05.

## Compact bounds and scroll — UX-R04

Repaired disclosures11:40/11:41 to592px FILL; applied width repair to17 references. Today content now has one outer working-content scroll owner with naturally expanding task bodies, propagated across current/mirrored prototype states. Compact render inspected: readable rows, no horizontal disclosure overflow. Browser-control retry failed at Node startup (No such file); actual scrolling remains explicitly pendingR23.

## Early shared contrast — UX-R19

Dark accent primitive changed from#5fae86 to#6cbb93. Unrounded sRGB contrast on#263c2e is5.1844:1; dark on-accent text is7.7962:1. Semantic aliases retained. Inspected dark Today11:457 render and existing hover/focus/disabled/loading/error component inventory. Completed leaf remains enabled; strike style preserved. Keyboard/screen-reader execution and text reflow remain future implementation/runtime evidence; enlarged stress fixture inR20.

## Today density — UX-R05

Shared active/selected/long/parent rows use8px top/bottom padding and retain15px titles/32px checkbox/36px Start. Today header puts date beside title; uses8px gaps and task count/Your order cue. Eight baseline split rows use479px. Added640×800 twenty-task/expanded stress reference65:5554 and pinned active countdown outside scrolling work content. Compact/split composition renders inspected; actual scroll pendingR23. Shared streak fixed height overridden instances normalized to60px.

## Week navigation — UX-R06

Added visible Previous/Today/Next to15 representative prototype states plus compact/light and split/dark references. Today resolves service current week, frozen when closed, with completion-state branching. Previous visits prior closed week; Next reaches empty next week without carryover. History remains separate; year-boundary640 reference added. Bounded next-week sample has disabled Next beyond its illustrated range, not a restriction for implementation. One cross-page reaction attempt rolled back atomically; corrected static references without reactions. Week native screenshot inspected.

## Contextual Move and Reorder — UX-R07

Selected-placement toolbar identifiesRead/SundayNov1/project-parent; move dialogs retain source context. Read grip/reorder cue and result agree; movedFriday result nowshowsRead ratherthanOutline, withitsSaturdayplacementpreserved bycontract. ExplicitCancel/MoveDown andfirst-boundarydisabledUp; staticlast-itemreferenceadded. Addedowned statesMoveSaving70:4678,MoveFailed70:4844,MoveResponseUncertain70:5009; normalMoveusespendingthenresult, failedRetryretainsinput, uncertainCheckStatusavoidsclaimingrollback. Reordercompositioninspected. Self-navigationattemptrolledbackatomicallyandwasguarded. Actualdrag/keyboard timingremainunverified.

## Compact Week overview — UX-R08

SharedWeekly row nowplacesgrip/project anddue+estimateonthecontextline,with15pxleaf/checkbox/Startbelow;59pxordinaryheightandnaturalwrapping. Daystriphastotalleafcounts,weeklyprogressusesunique2of11/18%, completedbranch3of11/27%. ReclaimedchromeandkeptEndWeekbottomright. ExpandedCompletedroot6:2336nowretainsall8unfinishedand2compactcompletedrows. Compact/splitreferencesalignedto8sourceleaves. Weekcompositionrenderinspected;requiredscroll/dragremainpendingR23.

## Wide Week readability — UX-R09

1440wide13:710nowdefaultsProjectsclosed,yielding192pxcards.NativeShow/HideProjectsvariablepreservesselection/plans. Columnsmin184px;openingpaneretainsreadabilityviahorizontalboardscrollwithquietcontinuationcue;eachdayownsverticalscroll. Added1279/1280selected-dayfallbackcomparisons;proposedtransitionnotfinalconfirmedbreakpoint. Widecompositioninspected;toggle/scrollactualexecutionpending. A nullconditionalelsewasrejected/rolledback; replacedwithexplicitbooleancondition.

## Selection versus order — UX-R10

TodaydefaultrowsnowuseActive,notSelected,withYourordercueonly. WeektoolbarcallsitsReadplacementSelected;selectiondoesnotreorder. AddedTodayreordered79:5105;OrderbooleanVariableID:79:5104changesonlyonconfirmedreorder.197nativetargetroutesflattenedtosustainillustratedidleorderbetweenTodayandWeek;Canceldoesnotsetit. Preserved10startsandreadcheckbox/Startreactionswhenswappinginstances. Reorderedrenderinspected. Timers/completioninarbitraryordercombinationsremainoutsidefiniteprototypecoverage;appmustpersistorderseparately. Nativeundefinedelseconditionhandledafteratomicallyrolled-backattempt.

## Crowded Projects and task entry — UX-R11

Projects/child/reopened/Done-subviewdrawersnowhavefixedheading/projectcontrols/AddtaskfooterandoneTaskscrollbody,withparent/childgroupingspreserved. Readcompletedrowstayedabovefooter.24pxpadding/8pxgapsreclaimspacewhileRename/AddstayunderProjects. Added640×80015-active-leaf/multiple-parentstress82:6877,oneSaveeditor82:7190,andinput-retainingfailedSave82:7364. NormalProjectsrendervisuallychecked;Save/validationremainrepresentativenativepaths,notappatomic-saveimplementation.

R11 independent review found missing Notes in failed-save reference. Repaired live failed-save root9:6023 and compact82:7364 with retained Notes; combined due/estimate into one row to preserve geometry. Crowded parent controls/body/footer checks passed; actual scroll remains pending.

## Live Done versus frozen history — UX-R12

Doneuses3uniquecompletedtasksoverall,planned-year/month/weekhierarchyandNoPlannedWeek;ondemandAbouttotalsexplainsrepeatedmembership. RepairedhiddenReadrowauto-layoutandscrolling. Chapter4appearsintwoplannedweeksbutcountsonceoverall. Closedsourceframesnowshowall12originaldateplacementsfor11uniqueleaveswithreadonlyAtclosurestatus,dues,andseparatecurrentReadstatus. PriorclosedweekretainsoldSummarizechapter4notes/Oct29/20min/unfinishedwhilecurrentisSummarizechapter4/Oct30/25min/complete;Missed1. Done/priorhistoryrendersinspected;reopen/pendingerrornativeflowsretained,actualexecutionpending.

## Immediate carryover defaults — UX-R13

EndWeekconfirmationnowclosesandimmediatelyopenschoiceswithall9eligibleleaveschecked;Readcompleteatclosurebranchselects8. EightSundaydefaultsNov8,citationsWednesdayNov4;ReadlastsourceNov1notOct31. Recheckingrestoresdefault. Preselectiondoesnotsave;Cancelkeepsclosedsource. Empty/all-complete640referencesadded. Existingrootsretainedand4day/recoveryexamplesaddedwithinCloseSection. Integrationrejectedsome11-argumentANDguardsandoversizedreturnatomically;binaryANDandcompactnonduplicatedIDevidencesucceeded. Native9-checkbox/date/ApplyconstructionalsoavailableforR14verification.

## Reviewed carryover — UX-R14

Ninecheckboxes/sevennext-weekdates,Review/Apply,Cancel/reentry,exclusions/stale/failed/unconfirmedstatesbuilt. CorrectedhorizontalHUGsizingaftervisualreview;fixedfootersoutsideoneworkinglistscroll. CriticalnativeAPIroundtriptruncatedmulti-caseconditionalstotwo;replacedwithseparatesingleIFactionsandcapturedcountstocascades.17checksagainstinstalledreactionmetadatapass:9/8defaults,lastsource+7,recheckreset,noApplybeforeclosure,Cancel,exact2-taskdates,already-appliedexclusion,closure-completeReadstillineligibleafterreopen,duplicateApplynoaddition. Thisisamodelinterpreter,notbrowserexecution. R21mustrebuildoldernavigationwiththesameverifiedsingleIFpattern;actualscroll/clickstillpendingR23.

## Stats scopes and Missed — UX-R15

Statsandthreewidth/themereferencesseparateall-timeconfirmedtime/finalizedsessionsfromcurrentuniqueleafcompletionandfrozenMissed. Optionalclosed-week/project/estimatesdetail;chartslabelMon26etc.7installedreaction-modelcheckspassforopenweekexclusion,source9or8misses,latercompletion/reopening,knownsaved-timecorrectionbranches,andopendisclosuretoggle.800compositioninspected. Added800×700repeated-missreference100:7733andindependentNov9fixture:Readtwo-sourcedatescountsoneinweek1,oneinweek2;latercompletionretainsMissed2×,overall11. Noapp/statisticspersistenceclaim.

R15 verification note: initial validation cell had a JavaScript local-name collision and atomically made no changes. Reran the standalone installed-metadata interpreter successfully before startingR16; all seven recorded checks pass.

## Track setup — UX-R16

IdleChangeTaskopensincompleteleafpickerincludingunscheduledBookstudyroomintwodistinctprojects. Active/paused/review/unknown/known-failedsessionroutesprotectexistingselection. OneForestentry,quietPineowneddisclosure,compactDurationfield,locked-speciescopyinactivesessions. Removedrepeated30-minuteexplanation. OriginalStart/Pause/FinishactionsretainedforR21review. Prototype/referencesupdated;Trackflowrepackedinto3×3nativeframesandStatssectionmovedbelowwith500pxgap. Ready/recoveryrendersinspected;rootnumbers/returnroutesverifyR17/R21. Initialdraftsyntaxcollisionwasatomicallyrejectedandfixedbeforeconstruction.

## Recovery consequences — UX-R17

Normalrecoveryshows12minconfirmed/18remaining/5excluded;separateDarkboundary105:8259shows120trustedseconds/300excluded/1680remainingandunchanged45savedminutesbeforefinish. Centeredrecoverycontrols;explicitContinue/FinishretainslockedPineandsamesession. Addedfailed105:5656/unconfirmed105:5693withsame-receiptretry,priorityguardandlast-knownPausedcopy.12installedreaction-modelcheckspassforactivepickerpreservation,unscheduledselection,noautostart/resume,known/unknownsaveguards,speciestoggle,and12minfinish/retrywithouttaskcompletion. Failed/boundaryrendersinspected. Browser/timing/replaypersistenceandhardwareevidenceunclaimed.

## Assistant affordances — UX-R18

PlainContextandmodelstatusreplaceambiguousselectors;answersandsourcesstaycalmandcomposerfixedoutsideanswerscroll. Addedretained-draftframe110:5638;Cancel/errorpreservequestion,Answerclearsonlydraft,NewQuestionclearscurrentstate. Read-completesampleanswerpointstoOutlineandlabelsReadcompleteinSources.6installedreaction-modelcheckspass;native/referencepagebatchesseparate. Self-navigationNewQuestionHomewasatomicallyrejectedandcorrectedtoin-placeclear. CurrentM5Apply/Undo/carryoverappcapabilityremainsoutsidethisread-onlysample. Renderinspected;actualtyping/model/keyboardexecutionunverified.

## Responsive/theme propagation — UX-R20

Reviewed87editableprototypeframesand46responsive/theme/statefixtures. AddedmissingProjects/Done,compactcarryover/history/timer,recoveryandDarkcompositions;200%textfixture115:8987uses30pxtasktitlesandlargercontrolswithnaturalverticalreflow,notcanvaszoom. SixnewcompositionsindependentlyreviewedwithnoP1staticfinding. AllfontsInterfallback,nomissingfonts,noimage-filledUI,zeroSectionoverlap/overflow. Referencepageorganizedinto7flowSectionsand13accidentalclonedflowstartsremoved;main10startspreserved. Added32pxgriphitboxaround16pxSVGwithunchanged59pxcardheight;R21wiresthetarget. Browserreflow/scroll/keyboardunverified. R21current slices: globalroutes,Create/reopenconsistency,Move/dateconsistency,closure/carryover/reset/native-modelchecks.

## November 2 stop checkpoint — UX-R21 unfinished

The user explicitly requested stopping prototype work and documenting completion
and remaining work. No further Figma mutation was started after that request.
Environment verified with `sw_vers -productVersion` (`26.6.2`) and `uname -a`
(Darwin arm64). Synthetic service day remains November 1, 2026.

### Applied work

- Final pre-pairing navigation batch rewired 912 controls, including 487 task Start
  controls and seven 32px drag targets. It returned zero unresolved calendar edges
  and zero ambiguous task targets. This evidence predates new pairing rows.
- Added Move flags, frozen Friday/Sunday slots and a captured next-week suggestion.
  Moving Sunday Read to Friday leaves Saturday as its latest source date, yielding
  Saturday, November 7. Other placements and task identity remain unchanged.
- Expanded carryover to a maximum of 12 candidates (baseline nine, plus reopened
  Theme/Chapter and the created Draft). Captured closure flags are not rewritten
  on repeat closure; Review/Apply remains explicit.
- Added default/reversed order groups in 12 native views and a reverse example
  `147:7536`. Native drag requires SMART_ANIMATE; rejected DISSOLVE/conditional
  drag attempts rolled back and were replaced by a supported link/entry dispatch.
- Paired 138 live surface/leaf combinations, adding 132 row counterparts with no
  returned pairing warnings. Shared completion/count wiring was applied to all 89
  registered product/state frames in bounded batches. Unsupported sample checkboxes
  are disabled, rather than mapped to Read. Only Read, Theme and Chapter completion
  are demonstrated. The new Draft checkbox is intentionally disabled.
- Week counts and End Week preview routes were repaired; duplicate source-week
  range/footer History controls were hidden. Completed totals, frozen Missed and
  caption variables were integrated. Today summary restores the “Your order” cue.
- Added review launcher `141:7346` in section `141:7345`; preserved the ten original
  starts and added one review start. Launcher background was repaired to color/bg
  after its initial screenshot; that repair still needs a fresh render.
- Applied time-context patch: 17 variables (`155:8299`–`155:8315`), capture on seven
  Finish/retry controls, and corrections on `7:3280` / `7:3247`. It supports finite
  45→57 and 43→55 focus, 45→43 / 57→55 correction, replay and captured attribution.
  The new wallet branches were installed but not independently executed afterward.

### Verification actually completed

The cached, read-only interpreter over installed native reactions passed ten
cases: one Save/retry without duplication; blocked closed-day Save; Read complete/
reopen preserving idle/running/paused/review/sleep; completed-at-closure Theme and
Chapter staying excluded after reopening; 12 eligible candidates applying once;
and Move preserving frozen dates and the Saturday suggestion. It mutates a local
Map, not Figma variables, and is not browser interaction evidence.

The independent visual reviewer provisionally scored 87.09/100, compared with the
original 76.84/100, using the same weights. No new static P1 was observed in its
captured scope. [Full provisional review](2026-11-02-ux-refinement-provisional-review.md).
That capture predates the latest pairing/completion/time changes. Its two P2
findings were addressed in code (manual-order cue and duplicated Week chrome),
but a final rendered recheck is pending. Earlier 42 scoped installed-model checks
remain historical; they were not all rerun on this paused tree.

One monolithic completion write timed out. A subsequent read confirmed no new
Completion variables or partial wiring; bounded batches then completed. Broad
full-page read audits also timed out, so no full-file audit pass is claimed.
An oversized purchase read was rejected without writes and replaced by a narrow
read. Computer-control Node startup remains unavailable; actual clicks, scroll,
arbitrary drag, keyboard and screen-reader checks were not performed.

### Exact work remaining on resumption

1. **Repair known failure example:** `5:4694` / Retry `I5:4843;3:349` has no action.
   Its direct named start does not seed Read as complete. Seed the intended case,
   keep completion unchanged on failure, wire successful retry to reopen Read,
   preserve the active session and keep feedback/retry reachable. Review the old
   preserved checkbox handlers on this failure backdrop before enabling them.
2. **Finish control integration after pairing:** rerun a targeted navigation/Start
   pass for new rows, include reverse root `147:7536` in source-week routing, and
   wire new Read grip targets. Preserve the existing reverse dispatch and Escape
   routes. Do not replay the archived creation patches.
3. **Reset/default/entry integration:** launcher reset currently has 147 baseline
   variables plus timer-status reset; it predates the 17 time variables and final
   completion/day-count additions. Reconcile disclosure defaults (new groups may
   expand under the old defaults), isolated error starts including Assistant,
   retained questions and all pending-result entries. Normalize newly introduced
   parent context labels against the canonical fixture.
4. **Verify finite time/reward behavior:** exercise the installed time/correction
   patch and all wallet branches and retries. Bind `7:2852` (currently fixed57) to
   actual saved focus and `7:2855` (currently live selected task) to saved context.
   Inspect Forest attribution. The purchase-failure sample `7:2998` still shows
   fixed20 coins while global baseline is33. Buy currently demonstrates failure,
   not a successful purchase/ownership transaction; keep that boundary explicit.
5. **Final R21 checks:** partition/cache structural reads, validate destinations,
   single-IF/binary guards, cancellation, drag sizes and no stale count side effects.
   Rerun affected installed models, then inspect post-change Today, completed/timer,
   Week/reverse, Projects/child, frozen/carryover, Stats, error and launcher renders.
   Recheck affected compact/dark references where a shared visual asset changes.
6. **Then R22–R24:** finish independent QA and rescore on the final tree; obtain
   actual core click/scroll and user acceptance evidence; deliver the reviewed
   handoff. R23 and R24 are not complete. Draft handoff text is saved as evidence.

### Outcome and preservation

**R21 acceptance has not passed: work is unfinished and paused.** Completed
substeps and passing model cases do not waive missing checks or the known retry
defect. The final original36-ticket acceptance, app/core-trial and Mac hardware
gates are unchanged. No application implementation, database/service operation,
application tests, commit or push was performed for this checkpoint. Unrelated
working changes and concurrent commits were preserved.

Durable records: `frontend/design/refinement-execution.json` key
`r21Checkpoint20261102`; ledger key `refinementCurrentNativeMeta`; and
[resumption support](../../frontend/design/refinement-support/README.md).
Current status and next action live only in `docs/PROGRESS.md`.

### Documentation closeout checks

`git diff --check -- docs/PROGRESS.md docs/COMPLETED.md docs/reviews/2026-11-01-ux-refinement.md docs/reviews/2026-11-02-ux-refinement-provisional-review.md frontend/design/figma-node-ledger.json frontend/design/refinement-execution.json frontend/design/refinement-support` returned exit0.

A read-only Python content check passed: repair register is20Done/1Paused/3Not
started; stale R20/plan-only guidance is absent; both evidence JSON files parse;
all11 successful bounded completion batches and the10 passing installed-model
cases are retained; current/review/support Markdown whitespace and relative links
resolve; root AGENTS.md and the repository design skill remain present. No
application test suite was run for this documentation-only closeout.
