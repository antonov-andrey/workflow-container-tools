# `code-antipattern-audit-instrumental` Report

## Scope
- `scope`: `<fill repository-relative scope>`

## Report metadata
- `report_uuid`: `<fill uuidgen output>`
- `report_path`: `<fill repository-relative report path>`

## Executed commands
- `<fill each executed command or write None>`

## Checker results
- `project-standards:python-developer/scripts/python_proxy_method_check.py`: `PASS`|`FAIL`|`NOT_RUN`
- `project-standards:python-developer/scripts/python_single_use_artifact_check.py`: `PASS`|`FAIL`|`NOT_RUN`
- `project-standards:python-developer/scripts/python_argument_pack_check.py`: `PASS`|`FAIL`|`NOT_RUN`
- `project-standards:python-developer/scripts/python_control_flow_complexity_check.py`: `PASS`|`FAIL`|`NOT_RUN`
- `project-standards:python-developer/scripts/python_dependency_fanout_check.py`: `PASS`|`FAIL`|`NOT_RUN`
- `project-standards:python-developer/scripts/python_hidden_dependency_construction_check.py`: `PASS`|`FAIL`|`NOT_RUN`
- `project-standards:python-developer/scripts/python_generic_bucket_module_check.py`: `PASS`|`FAIL`|`NOT_RUN`

## Reviewed anti-pattern cards
- `<fill each reviewed anti-pattern id or write None>`

## Collected signals
- `<fill one bullet per raw signal with checker id, file path, line, triggering pattern, candidate anti-pattern ids, and scope expansion used, or write None>`

## Rejected signals
- `<fill one bullet per rejected signal with checker id, file path, line, rejected anti-pattern ids, competing cards rejected when relevant, exception status, and rejection reason, or write None>`

## Confirmed anti-pattern cases
- `<fill one bullet per confirmed case with anti-pattern ids, violated owner rule, file path, line, supporting checker ids, competing cards rejected, exception status, scope expansion used, and remediation direction, or write None>`

## Clean cards checked
- `<fill one bullet per reviewed anti-pattern id with inspected area and no confirmed case in the declared scope, or write None>`

## Verdict
- `overall_verdict`: `CLEAN` (replace with `FINDINGS` or `NO_AUDITABLE_SCOPE` as needed)
