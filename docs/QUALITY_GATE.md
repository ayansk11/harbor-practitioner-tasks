# Quality gate: checks G1 to G30

Every task's DESIGN.md records its gate verdicts against this list, in a section titled "Gate record":
[`orders-export-missing-rows`](orders-export-missing-rows/DESIGN.md),
[`tenant-isolation-docshare`](tenant-isolation-docshare/DESIGN.md),
[`ab-test-reanalysis`](ab-test-reanalysis/DESIGN.md),
[`et0-station-ingest`](et0-station-ingest/DESIGN.md),
[`feature-leakage-churn`](feature-leakage-churn/DESIGN.md).

Last updated: 2026-10-29.

**What this list is.** The checks restate the take-home brief's own text as yes/no questions in plain words: its opening
sentence, "Choosing your tasks", "What makes a strong task", "What to submit" and "How we will review" (which ends with
the delivery line). The brief is not in this repository; each check quotes the words it rests on.

**Words used here.** *Verifier* (the brief's word) and *grader* mean the same thing: `tests/test.sh` and what it runs.
*Full reward* means a score of 1. *Accepted* means the verifier gives full reward. *The agent's container* is the sealed
computer the agent works in.

## How the checks are applied
1. Every decision is checked against this list before it is implemented: choosing a task and its domain; its
   environment, its instruction, its verifier, its reference solution, a second valid solution, its wrong and shortcut
   attempts; and project-level choices that shape the tasks or their delivery.
2. Decisions that are not about a task itself (for example the runner, the repository layout, a tool choice) get the
   checks that fit, mainly reproducibility (G16, G17); others only where they fit. The rest are `N/A` with a reason.
3. Any `FAIL` blocks implementation until the design is fixed, unless the author overrides it explicitly; the record
   then says so.
4. Each decision gets a written gate record: every check `PASS`, `FAIL` or `N/A`, each with a one-line reason. `N/A` is
   never used to dodge a check that fits. After a fix, the decision is checked again.
5. Every design proposal shows its gate result, and everyone who designs, builds or reviews a task scores it against
   this list.
6. **What `PASS` means before anything exists:** the design makes the check true. Some checks can only be proven by
   running the task (G4, G12, G13, G16, G17 and G22 to G25); the validation runs prove them later, and a failed run
   reopens the gate.
7. **What `PASS` means after the runs:** a check that needs a run passes only with a recorded run. A task is not
   finished until G22 to G25 pass with recorded runs.
8. A question with several parts passes only if every part is yes.

## The checks
### A. Choosing the task (the brief's opening sentence; "Choosing your tasks")
| Id | Check (answer yes to pass) | Take-home brief | Fails when, for example |
|---|---|---|---|
| G1 | **Self-contained:** does the package carry everything it needs (files, setup, verifier, solution), with no dependence on anything outside it that can change (a live website, a file on our Mac)? | "Build five self-contained tasks." (opening sentence) | it needs a live website, a file on our Mac or a service outside the task |
| G2 | **Useful work:** does the job give real value to the person who asked for it? | "complete useful work" (opening sentence) | a puzzle, a trick question, busywork no one needs |
| G3 | **Credible environment:** does the setup look like what a professional would really face (see also G9)? | "in a credible environment" (opening sentence) | a toy folder with one file and no context |
| G4 | **Clear success check:** can a script (the verifier) tell "done" from "not done", with no person judging? | "a clear way to tell whether the work was done" (opening sentence); "verifier" ("Fair scoring") | success depends on taste or opinion that no script can check |
| G5 | **Distinct problem:** is it a different problem from the other four tasks (different symptom, cause and fix), even if they share a base? | "each should present a distinct problem" ("Choosing your tasks") | two tasks are the same bug in different files |
| G6 | **Strong judgment:** can the task's author judge what is realistic, what is correct and what is cheating? | "any area where you have strong judgment" ("Choosing your tasks") | no one on our side can tell a right answer from a plausible wrong one |
| G7 | **Practitioner need:** would a real practitioner (an engineer, analyst or researcher) actually need this done at work? | "work a practitioner might actually need done" ("Choosing your tasks") | the request is something no one would ever ask |
| G8 | **Complete inputs:** are all files, tools and constraints inside the task, and is every constraint the verifier enforces stated in the instruction? | "provide the files, tools, and constraints needed to do it" ("Choosing your tasks"); see G15 | a needed tool is missing, or the verifier enforces a rule the instruction never states |

Note on G6 (how it is read here): the judgment must rest on evidence anyone can check: code that runs, answers
recomputed from the data, public standards and documentation. It cannot rest on a specialist's taste.

Not checks on purpose: "five" (opening sentence) is a count; the list of directions and BenchmarkList ("Choosing your
tasks") are suggestions; "may share a base" ("Choosing your tasks") is a permission.

### B. Realistic work ("What makes a strong task": "Realistic work")
| Id | Check | Take-home brief | Fails when, for example |
|---|---|---|---|
| G9 | **Makes sense in the field:** do the request, the inputs and the expected outcome make sense to someone who works in that field? | "The request, inputs, and expected outcome should make sense in the chosen field." | inputs no real system would produce; an outcome no one would want |
| G10 | **Useful result:** does the agent produce a useful answer, artifact (a file it builds) or system state (something left in the right condition)? | "The agent should produce a useful answer, artifact, or system state." | the output is thrown away or useless to the person asking |

### C. Fair scoring ("What makes a strong task": "Fair scoring")
| Id | Check | Take-home brief | Fails when, for example |
|---|---|---|---|
| G11 | **Checks the outcome:** does the verifier check the result that was asked for, not the method used or which file was edited (unless the task itself rules out a method)? | "The verifier should check the requested outcome." | it searches the code for a function name instead of running the code |
| G12 | **Shortcuts fail:** is every shortcut that skips the work rejected? | "It should reject shortcuts that skip the work" | hard-coding the expected values, deleting or editing the tests, faking output files, code that only handles the examples it was shown, or a trivial answer still gets full reward |
| G13 | **Other valid solutions accepted:** does a materially different correct solution get full reward? | "and accept materially different valid solutions." | a correct fix done another way is rejected because the verifier expects our exact reference |

### D. Meaningful challenge ("What makes a strong task": "Meaningful challenge")
| Id | Check | Take-home brief | Fails when, for example |
|---|---|---|---|
| G14 | **Honest difficulty:** does the difficulty come from the investigation, judgment or implementation the work really needs? | "Difficulty should come from the investigation, judgment, or implementation the work requires" | it is hard only because of volume, tedium or output formatting |
| G15 | **No unfair difficulty:** is it free of missing information, of pointless restrictions and of a fragile verifier? | "not from missing information, arbitrary restrictions, or a fragile grader." | an unstated unit or format; a pointless rule; a verifier that rejects 9.99 against 9.990 or an extra space |

### E. Reproducibility ("What makes a strong task": "Reproducibility")
| Id | Check | Take-home brief | Fails when, for example |
|---|---|---|---|
| G16 | **Reliable from a clean start:** does it build and run from nothing, and does the same solution get the same verdict every time? | "The task should run reliably from a clean start" | software versions that are not fixed, a website that changes, random choices that change between runs, a verifier that depends on timing |
| G17 | **Answer key hidden:** are the reference solution and the verifier's logic outside the agent's workspace (not in its container or its files) while it works? | "with the reference solution and grading logic kept outside the agent's workspace." | tests, the solution script or the expected answers are copied into the agent's container |

### F. The package and the README ("What to submit")
| Id | Check | Take-home brief | Fails when, for example |
|---|---|---|---|
| G18 | **Harbor-compatible package:** does the task live in its own `<task-slug>/` folder with `task.toml`, `instruction.md`, `environment/`, `tests/test.sh` and `solution/`, so that Harbor can run it? | "Submit a GitHub repository with five separate Harbor-compatible task packages."; the folder list that follows it | a file is missing or misnamed, or Harbor cannot build or run the task |
| G19 | **Its own four parts:** does it have its own instruction, environment, verifier and canonical solution, and does it still stand on its own if it uses a shared base? | "Each package should contain its own instruction, environment, verifier, and canonical solution. A shared base is fine." | the task only works if another task's folder is present |
| G20 | **README row:** does the README have this task's row with the capability assessed, the user-facing objective, how success is checked and the validation we ran? | "Include a short README with one row per task: the capability assessed, the user-facing objective, how success is checked, and the validation you ran." | the row is missing, a column is empty, or the validation cell claims runs we did not make |
| G21 | **Setup and limitations:** are the setup steps and the known limitations written down honestly? | "Note any setup steps or known limitations." | a reviewer cannot run it from the README, or a known weak spot is left out |

### G. The proof runs ("What to submit", its last paragraph)
Before implementation these checks ask whether the design makes the proof possible and names the attempts. After
implementation they pass only with a recorded run. A task is not finished until G22 to G25 pass with recorded runs.
| Id | Check | Take-home brief | Fails when, for example |
|---|---|---|---|
| G22 | **Reference gets full reward:** does the canonical solution score 1, shown by a recorded run? | "show that the canonical solution earns full reward" | the reference scores below 1, or only sometimes |
| G23 | **Doing nothing fails:** does a no-op (an agent that does nothing) score 0, shown by a recorded run? | "and that a no-op ... fail" | the untouched starting state already gets full reward |
| G24 | **A wrong or cheating attempt fails:** does at least one plausible incorrect attempt or shortcut attempt score 0, shown by a recorded run? | "and at least one plausible incorrect or shortcut attempt fail" | an honest half-fix or a cheat (hard-coding, deleting tests) gets full reward |
| G25 | **Not tied to our solution:** where more than one valid approach exists, does a different correct solution also score 1, so the verifier does not depend on incidental details of ours (file names, function names, output order)? | "Where more than one valid approach exists, check that the verifier does not depend on incidental details of your reference solution." | a correct solution done another way is rejected |

"You may use agents or other tools to build and critique the tasks." (same paragraph) is a permission, not a check.

### H. Ready for review ("How we will review")
| Id | Check | Take-home brief | Fails when, for example |
|---|---|---|---|
| G26 | **Inspectable:** can a reviewer inspect the prompt, the environment, the verifier and our run traces (our reading: we ship the traces)? | "We will inspect the prompt, environment, verifier, and available run traces" | the traces are missing, or the verifier is hard to read |
| G27 | **Runs on their setup:** does the task run for the reviewers' own agent trials (our reading: without our keys, our machines or anything only we have)? | "and may run agent trials." | it needs our cloud key, our Mac or a file outside the repository |
| G28 | **The three review questions:** does the task resemble valuable work, does the scoring reflect that work, and would an agent's failure reveal a real capability gap (not an unclear instruction or a verifier bug)? | "We care whether the task resembles valuable work, whether scoring reflects that work, and whether failures reveal a real capability gap." | agents fail because of a typo in the instruction or a verifier bug |
| G29 | **Not hard for its own sake:** is the task free of difficulty added only to lower the pass rate? | "A low pass rate by itself is not a sign of quality." | a rule or trap added only to make agents fail |

### I. Delivery (the last line of "How we will review")
| Id | Check | Take-home brief | Fails when, for example |
|---|---|---|---|
| G30 | **Delivered:** is the work in a GitHub repository with tejpal@diffuselabs.ai (@tejpalv) added? | "Deliver the completed assignment as a GitHub repository, and add tejpal@diffuselabs.ai (@tejpalv)." (link text shown; the brief writes the address as a mailto link) | the repository is missing or unreadable to the reviewer |

## Gate record format
Each task's record is in its `docs/<slug>/DESIGN.md`, next to the design it gates (project-level records live with the
planning notes, which are not in this repository).
```
Gate record: <decision> (<date>)
Applies to: task <slug> | project-level
G1  PASS | FAIL | N/A - <one-line reason>
...
G30 PASS | FAIL | N/A - <one-line reason>
Result: PASS | BLOCKED (G<n>, ...) | OVERRIDDEN by the author ("<reason>", <date>)
```
Reading the task records: `PASS (plan)` marks a check scored on the design or plan when the record was written;
`PASS (run)` marks one scored from runs, and `PASS (run, recorded: <file>)` names the file that holds the recorded run.

## Where the proof is
The validation runs (oracle, no-op, wrong and shortcut attempts, second valid solution) are the proof, after
implementation, for G4, G12, G13, G16, G17 and G22 to G25. Their results are in
`validation/<slug>/PROOF_RESULTS_<run>.md`, indexed in [`validation/README.md`](../validation/README.md).
